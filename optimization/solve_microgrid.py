from typing import Dict, List, Any

from optimization.microgrid_model import build_microgrid_model

try:
	import pulp
except ImportError:  # type: ignore
	pulp = None  # type: ignore


def solve_microgrid(gen_kwh: List[float], loads: Dict, battery: Dict, params: Dict) -> Dict[str, Any]:
	"""Solve microgrid energy distribution problem"""
	if pulp is None:
		raise ImportError("pulp not installed. Install with: pip install pulp")

	model, vars_dict = build_microgrid_model(gen_kwh, loads, battery, params)

	status = model.solve(pulp.PULP_CBC_CMD(msg=False))
	status_str = pulp.LpStatus[status]

	def values(name: str) -> List[float]:
		return [float(v.value()) for v in vars_dict[name]]

	charge = values("charge")
	discharge = values("discharge")
	soc = values("soc")
	hospital_served = values("hospital_served")
	school_served = values("school_served")
	homes_served = values("homes_served")
	hospital_unmet = values("hospital_unmet")
	school_unmet = values("school_unmet")
	homes_unmet = values("homes_unmet")
	curtail = values("curtail")

	total_penalty = float(pulp.value(model.objective))

	return {
		"status": status_str,
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
	}
