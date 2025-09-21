import json
from pathlib import Path

from optimization.microgrid_model import load_microgrid_defaults
from optimization.solve_microgrid_qaoa import compare_solvers


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


def print_results(result: dict, method: str):
	"""Print results for a specific method"""
	print(f"\n=== {method.upper()} RESULTS ===")
	print(f"Status: {result['status']}")
	print(f"Total penalty: {result['total_penalty']:.2f}")
	
	# Summary statistics
	total_hospital_unmet = sum(result['hospital_unmet_kWh'])
	total_school_unmet = sum(result['school_unmet_kWh'])
	total_homes_unmet = sum(result['homes_unmet_kWh'])
	total_curtail = sum(result['curtail_kWh'])
	
	print(f"Hospital unmet: {total_hospital_unmet:.2f} kWh")
	print(f"School unmet: {total_school_unmet:.2f} kWh")
	print(f"Homes unmet: {total_homes_unmet:.2f} kWh")
	print(f"Total curtailed: {total_curtail:.2f} kWh")


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

	# Compare classical vs quantum
	print("=== QUANTUM vs CLASSICAL OPTIMIZATION COMPARISON ===")
	results = compare_solvers(gen, loads, battery, params)
	
	# Print individual results
	print_results(results["classical"], "Classical MILP")
	print_results(results["quantum"], "Quantum QAOA")
	
	# Print comparison
	print(f"\n=== COMPARISON ===")
	comp = results["comparison"]
	print(f"Classical penalty: {comp['classical_penalty']:.2f}")
	print(f"Quantum penalty: {comp['quantum_penalty']:.2f}")
	print(f"Quantum/Classical ratio: {comp['penalty_ratio']:.3f}")
	print(f"Classical status: {comp['classical_status']}")
	print(f"Quantum status: {comp['quantum_status']}")
	
	if comp['penalty_ratio'] < 1.1:
		print("✅ Quantum solution is competitive with classical!")
	elif comp['penalty_ratio'] < 2.0:
		print("⚠️ Quantum solution is reasonable but not optimal")
	else:
		print("❌ Quantum solution needs tuning (try different reps/shots)")
	
	# Show hourly comparison for key metrics
	print(f"\n=== HOURLY COMPARISON (SOC) ===")
	print("Hour | Classical SOC | Quantum SOC | Difference")
	print("-----|---------------|-------------|----------")
	for h in range(24):
		classical_soc = results["classical"]["soc_kWh"][h]
		quantum_soc = results["quantum"]["soc_kWh"][h]
		diff = abs(classical_soc - quantum_soc)
		print(f"{h:02d}   | {classical_soc:11.2f} | {quantum_soc:9.2f} | {diff:8.2f}")


if __name__ == "__main__":
	main()
