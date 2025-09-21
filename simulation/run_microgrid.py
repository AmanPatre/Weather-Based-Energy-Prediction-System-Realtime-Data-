import json
from pathlib import Path

from optimization.microgrid_model import load_microgrid_defaults
from optimization.solve_microgrid import solve_microgrid


def load_series(path: Path) -> list:
	if not path.exists():
		return []
	with open(path, "r", encoding="utf-8") as f:
		obj = json.load(f)
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

	# Load microgrid defaults
	_, loads, battery, params = load_microgrid_defaults(str(cfg_path))

	# Load solar + wind forecasts
	solar = load_series(solar_path)
	wind = load_series(wind_path)
	if solar and wind and len(solar) == 24 and len(wind) == 24:
		gen = [float(s) + float(w) for s, w in zip(solar, wind)]
		print("Using real solar + wind forecasts")
	else:
		print("Warning: Using default generation (no forecasts found)")
		gen = [0.0] * 24

	# Solve microgrid
	res = solve_microgrid(gen, loads, battery, params)

	print("=== MICROGRID ENERGY DISTRIBUTION ===")
	print(f"Status: {res['status']}")
	print(f"Total penalty: {res['total_penalty']:.2f}")
	print()
	print("Hour | Charge | Discharge | SOC  | Hospital | School | Homes | Curtail")
	print("-----|--------|-----------|------|----------|--------|-------|--------")
	
	for h in range(24):
		hospital_status = "✓" if res['hospital_unmet_kWh'][h] == 0 else "✗"
		school_status = "✓" if res['school_unmet_kWh'][h] == 0 else "✗"
		homes_status = "✓" if res['homes_unmet_kWh'][h] == 0 else "✗"
		
		print(f"{h:02d}   | {res['charge_kWh'][h]:6.2f} | {res['discharge_kWh'][h]:9.2f} | "
		      f"{res['soc_kWh'][h]:4.1f} | {hospital_status:8s} | {school_status:6s} | "
		      f"{homes_status:5s} | {res['curtail_kWh'][h]:7.2f}")

	# Summary
	total_hospital_unmet = sum(res['hospital_unmet_kWh'])
	total_school_unmet = sum(res['school_unmet_kWh'])
	total_homes_unmet = sum(res['homes_unmet_kWh'])
	total_curtail = sum(res['curtail_kWh'])
	
	print(f"\n=== SUMMARY ===")
	print(f"Hospital unmet: {total_hospital_unmet:.2f} kWh ({'✓ All served' if total_hospital_unmet == 0 else '✗ Some unmet'})")
	print(f"School unmet: {total_school_unmet:.2f} kWh ({'✓ All served' if total_school_unmet == 0 else '✗ Some unmet'})")
	print(f"Homes unmet: {total_homes_unmet:.2f} kWh ({'✓ All served' if total_homes_unmet == 0 else '✗ Some unmet'})")
	print(f"Total curtailed: {total_curtail:.2f} kWh")


if __name__ == "__main__":
	main()
