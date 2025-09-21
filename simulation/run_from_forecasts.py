import json
from pathlib import Path

from optimization.model import load_defaults
from optimization.solve_milp import solve_day


def load_series(path: Path) -> list:
	with open(path, "r", encoding="utf-8") as f:
		obj = json.load(f)
	return obj.get("forecast_series_kWh") or obj.get("forecast_series") or []


def main():
	root = Path(__file__).resolve().parent.parent
	solar_path = root / "solar_energy_forecast.json"
	wind_path = root / "wind_energy_forecast.json"
	defaults_path = root / "data" / "inputs_defaults.json"

	# Load defaults for demand/battery/grid/params
	gen_default, demand, battery, grid, params = load_defaults(str(defaults_path))

	# Load forecasts and combine
	solar = load_series(solar_path)
	wind = load_series(wind_path)
	if not solar or not wind:
		raise RuntimeError("Missing or invalid solar/wind forecast JSON files.")
	if len(solar) != 24 or len(wind) != 24:
		raise RuntimeError("Forecast series must be 24 values each (hourly).")
	gen = [float(s) + float(w) for s, w in zip(solar, wind)]

	# Solve day
	res = solve_day(gen, demand, battery, grid, params)

	print("Status:", res["status"]) 
	print("Total cost:", round(res["total_cost"], 2))
	print("Hour charge discharge import export soc unmet curtail")
	for h in range(24):
		print(
			f"{h:02d}\t{res['charge_kWh'][h]:.2f}\t{res['discharge_kWh'][h]:.2f}\t"
			f"{res['grid_import_kWh'][h]:.2f}\t{res['grid_export_kWh'][h]:.2f}\t{res['soc_kWh'][h]:.2f}\t"
			f"{res['unmet_kWh'][h]:.2f}\t{res['curtail_kWh'][h]:.2f}"
		)


if __name__ == "__main__":
	main()
