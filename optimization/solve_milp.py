from typing import Dict, List, Any

from optimization.model import build_milp_model

try:
	import pulp
except ImportError:  # type: ignore
	pulp = None  # type: ignore


def solve_day(gen_kwh: List[float], demand_kwh: List[float], battery: Dict, grid: Dict, params: Dict) -> Dict[str, Any]:
	if pulp is None:
		raise ImportError("pulp not installed. Install with: pip install pulp")

	model, vars_dict = build_milp_model(gen_kwh, demand_kwh, battery, grid, params)

	status = model.solve(pulp.PULP_CBC_CMD(msg=False))
	status_str = pulp.LpStatus[status]

	def values(name: str) -> List[float]:
		return [float(v.value()) for v in vars_dict[name]]

	charge = values("charge")
	discharge = values("discharge")
	g_import = values("grid_import")
	g_export = values("grid_export")
	soc = values("soc")
	unmet = values("unmet")
	curtail = values("curtail")

	total_cost = float(pulp.value(model.objective))

	return {
		"status": status_str,
		"total_cost": total_cost,
		"charge_kWh": charge,
		"discharge_kWh": discharge,
		"grid_import_kWh": g_import,
		"grid_export_kWh": g_export,
		"soc_kWh": soc,
		"unmet_kWh": unmet,
		"curtail_kWh": curtail,
	}
