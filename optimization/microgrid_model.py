import json
from typing import Dict, List, Tuple

try:
	import pulp
except ImportError:  # type: ignore
	pulp = None  # type: ignore


def build_microgrid_model(gen_kwh: List[float], loads: Dict, battery: Dict, params: Dict) -> Tuple[object, Dict[str, List[object]]]:
	"""
	Microgrid energy distribution model - no grid trading, priority loads only.
	
	Loads (priority order):
	- hospital: critical load (must be served first)
	- school: important load (served if possible)
	- homes: regular load (served with remaining energy)
	
	Variables per hour h:
	- charge[h]: battery charge (kWh)
	- discharge[h]: battery discharge (kWh)
	- soc[h]: battery state of charge (kWh)
	- hospital_served[h]: hospital load served (kWh)
	- school_served[h]: school load served (kWh)
	- homes_served[h]: homes load served (kWh)
	- hospital_unmet[h]: hospital unmet demand (kWh)
	- school_unmet[h]: school unmet demand (kWh)
	- homes_unmet[h]: homes unmet demand (kWh)
	- curtail[h]: excess energy wasted (kWh)
	"""
	if pulp is None:
		raise ImportError("pulp not installed. Install with: pip install pulp")

	H = len(gen_kwh)

	# Battery parameters
	capacity = float(battery.get("capacity_kWh", 20.0))
	soc0 = float(battery.get("soc0_kWh", 10.0))
	max_c = float(battery.get("max_charge_rate_kW", 5.0))
	max_d = float(battery.get("max_discharge_rate_kW", 5.0))
	eta_c = float(params.get("eta_charge", 0.95))
	eta_d = float(params.get("eta_discharge", 0.95))

	# Load parameters
	hospital_demand = loads.get("hospital_kWh", [2.0] * H)  # 2.0 kWh/hour (increased for visibility)
	school_demand = loads.get("school_kWh", [1.0] * H)     # 1.0 kWh/hour (daytime only)
	homes_demand = loads.get("homes_kWh", [0.8] * H)       # 0.8 kWh/hour (reduced for better balance)

	# Penalty weights
	P_hospital_unmet = float(params.get("P_hospital_unmet", 1000.0))  # Very high penalty
	P_school_unmet = float(params.get("P_school_unmet", 100.0))       # High penalty
	P_homes_unmet = float(params.get("P_homes_unmet", 10.0))          # Medium penalty
	P_curtail = float(params.get("P_curtail", 1.0))                   # Low penalty
	P_cycle = float(params.get("P_cycle", 0.1))                       # Very low penalty

	model = pulp.LpProblem("Microgrid_Energy_Distribution", pulp.LpMinimize)

	# Decision variables
	charge = [pulp.LpVariable(f"charge_{h}", lowBound=0) for h in range(H)]
	discharge = [pulp.LpVariable(f"discharge_{h}", lowBound=0) for h in range(H)]
	soc = [pulp.LpVariable(f"soc_{h}", lowBound=0, upBound=capacity) for h in range(H)]
	
	hospital_served = [pulp.LpVariable(f"hospital_served_{h}", lowBound=0) for h in range(H)]
	school_served = [pulp.LpVariable(f"school_served_{h}", lowBound=0) for h in range(H)]
	homes_served = [pulp.LpVariable(f"homes_served_{h}", lowBound=0) for h in range(H)]
	
	hospital_unmet = [pulp.LpVariable(f"hospital_unmet_{h}", lowBound=0) for h in range(H)]
	school_unmet = [pulp.LpVariable(f"school_unmet_{h}", lowBound=0) for h in range(H)]
	homes_unmet = [pulp.LpVariable(f"homes_unmet_{h}", lowBound=0) for h in range(H)]
	
	curtail = [pulp.LpVariable(f"curtail_{h}", lowBound=0) for h in range(H)]

	# Initial SoC
	model += soc[0] == soc0

	for h in range(H):
		# Energy balance: generation + discharge = charge + loads + curtail
		total_served = hospital_served[h] + school_served[h] + homes_served[h]
		model += gen_kwh[h] + discharge[h] == charge[h] + total_served + curtail[h]

		# Load constraints (served + unmet = demand)
		model += hospital_served[h] + hospital_unmet[h] == hospital_demand[h]
		model += school_served[h] + school_unmet[h] == school_demand[h]
		model += homes_served[h] + homes_unmet[h] == homes_demand[h]

		# Rate limits
		model += charge[h] <= max_c
		model += discharge[h] <= max_d

		# SoC dynamics
		if h < H - 1:
			model += soc[h + 1] == soc[h] + eta_c * charge[h] - discharge[h] / eta_d

	# Objective: minimize penalties
	objective = []
	for h in range(H):
		objective.append(P_hospital_unmet * hospital_unmet[h])
		objective.append(P_school_unmet * school_unmet[h])
		objective.append(P_homes_unmet * homes_unmet[h])
		objective.append(P_curtail * curtail[h])
		objective.append(P_cycle * (charge[h] + discharge[h]))

	model += pulp.lpSum(objective)

	vars_dict = {
		"charge": charge,
		"discharge": discharge,
		"soc": soc,
		"hospital_served": hospital_served,
		"school_served": school_served,
		"homes_served": homes_served,
		"hospital_unmet": hospital_unmet,
		"school_unmet": school_unmet,
		"homes_unmet": homes_unmet,
		"curtail": curtail,
	}

	return model, vars_dict


def load_microgrid_defaults(path: str) -> Tuple[List[float], Dict, Dict, Dict]:
	"""Load microgrid-specific defaults"""
	with open(path, "r", encoding="utf-8") as f:
		cfg = json.load(f)
	
	gen = cfg.get("forecast_series_kWh", [0.0] * 24)
	
	# Microgrid loads (kWh per hour) - INCREASED for better visibility
	loads = {
		"hospital_kWh": [2.0] * 24,  # 2.0 kWh/hour (constant critical load - increased)
		"school_kWh": [1.0 if 6 <= h <= 18 else 0.0 for h in range(24)],  # Daytime only - increased
		"homes_kWh": [0.8, 0.6, 0.6, 0.7, 0.9, 1.2, 1.8, 2.4, 2.6, 2.4, 2.2, 2.0, 
		              1.8, 1.9, 2.1, 2.6, 3.0, 3.2, 3.0, 2.4, 1.8, 1.2, 0.9, 0.8]
	}
	
	battery = cfg.get("battery", {})
	params = cfg.get("params", {})
	
	return gen, loads, battery, params
