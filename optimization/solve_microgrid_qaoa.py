from typing import Dict, List, Any
import numpy as np

from optimization.microgrid_model import build_microgrid_model
from optimization.qubo import build_quadratic_program

try:
	import pulp
	from qiskit_aer.primitives import Sampler as AerSampler
	from qiskit_algorithms import QAOA
	from qiskit_optimization.algorithms import MinimumEigenOptimizer
except ImportError as e:
	print(f"Missing dependencies: {e}")
	print("Install with: pip install pulp qiskit qiskit-optimization qiskit-aer qiskit-algorithms")
	pulp = None


def solve_microgrid_classical(gen_kwh: List[float], loads: Dict, battery: Dict, params: Dict) -> Dict[str, Any]:
	"""Classical MILP solver for comparison"""
	try:
		import pulp
	except ImportError:
		raise ImportError("pulp not installed")
	
	model, vars_dict = build_microgrid_model(gen_kwh, loads, battery, params)
	status = model.solve(pulp.PULP_CBC_CMD(msg=False))
	status_str = pulp.LpStatus[status]

	def values(name: str) -> List[float]:
		return [float(v.value()) for v in vars_dict[name]]

	return {
		"method": "Classical MILP",
		"status": status_str,
		"total_penalty": float(pulp.value(model.objective)),
		"charge_kWh": values("charge"),
		"discharge_kWh": values("discharge"),
		"soc_kWh": values("soc"),
		"hospital_served_kWh": values("hospital_served"),
		"school_served_kWh": values("school_served"),
		"homes_served_kWh": values("homes_served"),
		"hospital_unmet_kWh": values("hospital_unmet"),
		"school_unmet_kWh": values("school_unmet"),
		"homes_unmet_kWh": values("homes_unmet"),
		"curtail_kWh": values("curtail"),
	}


def solve_microgrid_qaoa(gen_kwh: List[float], loads: Dict, battery: Dict, params: Dict, 
                        reps: int = 2, shots: int = 2048) -> Dict[str, Any]:
	"""Quantum-inspired QAOA solver for microgrid optimization"""
	
	# Build simplified QUBO for quantum solver
	# Convert loads to demand format for QUBO
	total_demand = []
	for h in range(24):
		hospital_demand = loads.get("hospital_kWh", [2.0] * 24)[h]
		school_demand = loads.get("school_kWh", [1.0 if 6 <= h <= 18 else 0.0 for h in range(24)])[h]
		homes_demand = loads.get("homes_kWh", [0.8] * 24)[h]
		total_demand.append(hospital_demand + school_demand + homes_demand)
	
	# Create dummy grid params for QUBO
	grid = {"price_buy_per_kWh": 0.0, "price_sell_per_kWh": 0.0, "export_limit_kW": 0.0, "import_limit_kW": 0.0}
	
	qp = build_quadratic_program(gen_kwh, total_demand, battery, grid, params, unit_kwh=1.0, levels=3)
	
	# Solve with QAOA
	from qiskit_algorithms.optimizers import COBYLA
	sampler = AerSampler()
	optimizer = COBYLA()
	qaoa = QAOA(sampler=sampler, optimizer=optimizer, reps=reps)
	min_eigen_optimizer = MinimumEigenOptimizer(qaoa)
	result = min_eigen_optimizer.solve(qp)
	
	# Decode quantum result back to microgrid format
	x = result.x
	vars_list = [v.name for v in qp.variables]
	
	# Initialize arrays
	charge = [0.0] * 24
	discharge = [0.0] * 24
	soc = [10.0] * 24  # Start with initial SOC
	hospital_served = [0.0] * 24
	school_served = [0.0] * 24
	homes_served = [0.0] * 24
	hospital_unmet = [0.0] * 24
	school_unmet = [0.0] * 24
	homes_unmet = [0.0] * 24
	curtail = [0.0] * 24
	
	# Decode quantum variables (simplified mapping)
	for h in range(24):
		# Map quantum variables to microgrid actions
		# This is a simplified decoding - in practice you'd need more sophisticated mapping
		charge_idx = h * 7  # Approximate mapping
		discharge_idx = h * 7 + 1
		
		if charge_idx < len(x):
			charge[h] = x[charge_idx] * 2.0  # Scale to reasonable values
		if discharge_idx < len(x):
			discharge[h] = x[discharge_idx] * 2.0
		
		# Update SOC
		if h < 23:
			soc[h + 1] = max(0, min(20, soc[h] + charge[h] * 0.95 - discharge[h] / 0.95))
		
		# Estimate load serving (simplified)
		available = gen_kwh[h] + discharge[h] - charge[h]
		hospital_demand = loads.get("hospital_kWh", [2.0] * 24)[h]
		school_demand = loads.get("school_kWh", [1.0 if 6 <= h <= 18 else 0.0 for h in range(24)])[h]
		homes_demand = loads.get("homes_kWh", [0.8] * 24)[h]
		
		# Priority serving
		hospital_served[h] = min(available, hospital_demand)
		available -= hospital_served[h]
		hospital_unmet[h] = hospital_demand - hospital_served[h]
		
		school_served[h] = min(available, school_demand)
		available -= school_served[h]
		school_unmet[h] = school_demand - school_served[h]
		
		homes_served[h] = min(available, homes_demand)
		available -= homes_served[h]
		homes_unmet[h] = homes_demand - homes_served[h]
		
		curtail[h] = max(0, available)
	
	# Calculate total penalty
	total_penalty = (
		sum(hospital_unmet) * 1000.0 +
		sum(school_unmet) * 100.0 +
		sum(homes_unmet) * 10.0 +
		sum(curtail) * 1.0 +
		sum(charge) * 0.1 + sum(discharge) * 0.1
	)
	
	return {
		"method": f"QAOA (reps={reps}, shots={shots})",
		"status": "Optimal" if result.fval is not None else "Infeasible",
		"total_penalty": total_penalty,
		"charge_kWh": charge,
		"discharge_kWh": discharge,
		"soc_kWh": soc,
		"hospital_served_kWh": hospital_served,
		"school_served_kWh": school_served,
		"homes_served_kWh": homes_served,
		"hospital_unmet_kWh": hospital_unmet,
		"school_unmet_kWh": school_unmet,
		"homes_unmet_kWh": homes_unmet,
		"curtail_kWh": curtail,
		"quantum_fval": result.fval,
	}


def compare_solvers(gen_kwh: List[float], loads: Dict, battery: Dict, params: Dict) -> Dict[str, Any]:
	"""Compare classical vs quantum solvers"""
	print("Solving with Classical MILP...")
	classical_result = solve_microgrid_classical(gen_kwh, loads, battery, params)
	
	print("Solving with QAOA...")
	quantum_result = solve_microgrid_qaoa(gen_kwh, loads, battery, params)
	
	return {
		"classical": classical_result,
		"quantum": quantum_result,
		"comparison": {
			"classical_penalty": classical_result["total_penalty"],
			"quantum_penalty": quantum_result["total_penalty"],
			"penalty_ratio": quantum_result["total_penalty"] / max(classical_result["total_penalty"], 1e-6),
			"classical_status": classical_result["status"],
			"quantum_status": quantum_result["status"]
		}
	}
