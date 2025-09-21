import json
from typing import Dict, List, Tuple

try:
	import pulp
except ImportError:  # type: ignore
	pulp = None  # type: ignore


def build_milp_model(gen_kwh: List[float], demand_kwh: List[float], battery: Dict, grid: Dict, params: Dict) -> Tuple[object, Dict[str, List[object]]]:
	"""
	Create a MILP model (Person 1 deliverable) without solving it.

	Variables per hour h:
	- charge[h]      >=0 (kWh)
	- discharge[h]   >=0 (kWh)
	- grid_import[h] >=0 (kWh)
	- grid_export[h] >=0 (kWh)
	- soc[h]         >=0 (kWh)
	- unmet[h]       >=0 (kWh)
	- curtail[h]     >=0 (kWh)

	Constraints:
	- Energy balance: gen + import + discharge = demand + charge + export + curtail - unmet
	- SoC dynamics: soc[h+1] = soc[h] + eta_c*charge[h] - discharge[h]/eta_d
	- Bounds: 0<=soc<=capacity; rate limits; grid limits

	Objective (not solved here): min cost = sum(price_buy*import - price_sell*export
		+ lambda_unmet*unmet + mu_curtail*curtail + cycle_penalty*(charge+discharge))
	"""
	if pulp is None:
		raise ImportError("pulp not installed. Install with: pip install pulp")

	H = len(gen_kwh)

	capacity = float(battery.get("capacity_kWh", 20.0))
	soc0 = float(battery.get("soc0_kWh", 10.0))
	max_c = float(battery.get("max_charge_rate_kW", 5.0))
	max_d = float(battery.get("max_discharge_rate_kW", 5.0))
	eta_rt = float(battery.get("round_trip_efficiency", 0.95))
	eta_c = float(params.get("eta_charge", eta_rt ** 0.5))
	eta_d = float(params.get("eta_discharge", eta_rt ** 0.5))

	price_buy = float(grid.get("price_buy_per_kWh", 6.0))
	price_sell = float(grid.get("price_sell_per_kWh", 3.0))
	export_limit = float(grid.get("export_limit_kW", 5.0))
	import_limit = float(grid.get("import_limit_kW", 10.0))

	lambda_unmet = float(params.get("lambda_unmet", 100.0))
	mu_curtail = float(params.get("mu_curtail", 2.0))
	cycle_penalty = float(params.get("cycle_penalty", 0.01))

	model = pulp.LpProblem("Energy_Allocation_24h", pulp.LpMinimize)

	charge = [pulp.LpVariable(f"charge_{h}", lowBound=0) for h in range(H)]
	discharge = [pulp.LpVariable(f"discharge_{h}", lowBound=0) for h in range(H)]
	g_import = [pulp.LpVariable(f"grid_import_{h}", lowBound=0) for h in range(H)]
	g_export = [pulp.LpVariable(f"grid_export_{h}", lowBound=0) for h in range(H)]
	soc = [pulp.LpVariable(f"soc_{h}", lowBound=0, upBound=capacity) for h in range(H)]
	unmet = [pulp.LpVariable(f"unmet_{h}", lowBound=0) for h in range(H)]
	curtail = [pulp.LpVariable(f"curtail_{h}", lowBound=0) for h in range(H)]

	# Initial SoC equality
	model += soc[0] == max(0.0, min(capacity, soc0))

	for h in range(H):
		# Energy balance per hour
		model += (
			gen_kwh[h] + g_import[h] + discharge[h]
			== demand_kwh[h] + charge[h] + g_export[h] + curtail[h] - unmet[h]
		)

		# Rate limits and grid limits
		model += charge[h] <= max_c
		model += discharge[h] <= max_d
		model += g_export[h] <= export_limit
		model += g_import[h] <= import_limit

		# SoC dynamics except last hour
		if h < H - 1:
			model += soc[h + 1] == soc[h] + eta_c * charge[h] - discharge[h] / max(eta_d, 1e-6)

	# Objective
	cost = []
	for h in range(H):
		cost.append(price_buy * g_import[h])
		cost.append(-price_sell * g_export[h])
		cost.append(lambda_unmet * unmet[h])
		cost.append(mu_curtail * curtail[h])
		cost.append(cycle_penalty * (charge[h] + discharge[h]))

	model += pulp.lpSum(cost)

	vars_dict = {
		"charge": charge,
		"discharge": discharge,
		"grid_import": g_import,
		"grid_export": g_export,
		"soc": soc,
		"unmet": unmet,
		"curtail": curtail,
	}

	return model, vars_dict


def load_defaults(path: str) -> Tuple[List[float], List[float], Dict, Dict, Dict]:
	with open(path, "r", encoding="utf-8") as f:
		cfg = json.load(f)
	gen = cfg.get("forecast_series_kWh")
	demand = cfg.get("demand_series_kWh")
	return gen, demand, cfg.get("battery", {}), cfg.get("grid", {}), cfg.get("params", {})
