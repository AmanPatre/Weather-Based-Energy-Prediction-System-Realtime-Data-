import json
from pathlib import Path

from optimization.model import load_defaults
from optimization.solve_milp import solve_day


def load_series(path: Path) -> list:
	if not path.exists():
		return []
	with open(path, "r", encoding="utf-8") as f:
		obj = json.load(f)
	# accept multiple key casings
	return (
		obj.get("forecast_series_kWh")
		or obj.get("forecast_series_kwh")
		or obj.get("forecast_series")
		or []
	)


def main():
	root = Path(__file__).resolve().parent.parent
	solar_path = root / "solar_energy_forecast.json"
	wind_path = root / "wind_energy_forecast.json"
	cfg_path = root / "data" / "inputs_defaults.json"

	# Load demand/battery/grid/params from defaults
	_, demand, battery, grid, params = load_defaults(str(cfg_path))

	# Prefer real forecasts if available
	solar = load_series(solar_path)
	wind = load_series(wind_path)
	if solar and wind and len(solar) == 24 and len(wind) == 24:
		gen = [float(s) + float(w) for s, w in zip(solar, wind)]
	else:
		print("Warning: solar/wind forecast files missing or invalid. Falling back to defaults.")
		# Fall back: try to read forecast from defaults
		with open(cfg_path, "r", encoding="utf-8") as f:
			cfg = json.load(f)
		gen = (
			cfg.get("forecast_series_kWh")
			or cfg.get("forecast_series_kwh")
			or cfg.get("forecast_series")
		)
		if not gen or len(gen) != 24:
			raise RuntimeError("No valid generation series found. Provide solar_energy_forecast.json and wind_energy_forecast.json with 24 values each.")

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
