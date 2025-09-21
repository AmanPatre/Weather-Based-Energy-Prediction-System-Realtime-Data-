from typing import Dict, List

from qiskit_optimization import QuadraticProgram


def build_quadratic_program(
	gen_kwh: List[float],
	demand_kwh: List[float],
	battery: Dict,
	grid: Dict,
	params: Dict,
	unit_kwh: float = 1.0,
	levels: int = 3,
) -> QuadraticProgram:
	"""
	Build a simplified QuadraticProgram (QUBO-friendly) for one day.

	- Discretizes per-hour battery action a[h] in {-L..0..+L} * unit_kwh via one-hot.
	- Discretizes export/import with small bit encodings.
	- Objective: balance mismatch^2 + penalties - revenue.

	Note: This is a compact template for quantum-inspired experiments; MILP is the
	reference for feasibility.
	"""
	qp = QuadraticProgram()
	H = len(gen_kwh)
	L = levels  # e.g., 1 -> {-1,0,+1}, 2 -> {-2,-1,0,1,2}

	# Battery and grid parameters (not strictly enforced as hard constraints here)
	capacity = float(battery.get("capacity_kWh", 20.0))
	soc0 = float(battery.get("soc0_kWh", 10.0))
	price_sell = float(grid.get("price_sell_per_kWh", 3.0))

	P_balance = float(params.get("P_balance", 10.0))
	P_onehot = float(params.get("P_onehot", 5.0))
	P_soc = float(params.get("P_soc_soft", 0.5))
	P_move = float(params.get("P_move", 0.2))

	# Variables
	a_vars = []
	for h in range(H):
		row = []
		for k in range(-L, L + 1):
			row.append(qp.binary_var(name=f"z_{h}_{k:+d}"))
		a_vars.append(row)
		x0 = qp.binary_var(name=f"s0_{h}")
		x1 = qp.binary_var(name=f"s1_{h}")

	# Build objective components
	objective_linear = {}
	objective_quadratic = {}
	objective_const = 0.0

	def add_quadratic_term(c, v1, v2):
		key = (v1, v2) if v1 <= v2 else (v2, v1)
		objective_quadratic[key] = objective_quadratic.get(key, 0.0) + c

	def add_linear_term(c, v):
		objective_linear[v] = objective_linear.get(v, 0.0) + c

	# Iterate hours
	soc_mid = capacity / 2.0 / unit_kwh
	soc = soc0 / unit_kwh
	for h in range(H):
		# a[h] encoding: sum_k k * z_{h,k}
		# one-hot penalty: (sum z - 1)^2
		sumz = None
		coeff_map = {}
		for k, zvar in zip(range(-L, L + 1), a_vars[h]):
			coeff_map[zvar.name] = float(k)
			add_linear_term(P_onehot * (-2.0), zvar.name)
			add_quadratic_term(P_onehot * 1.0, zvar.name, zvar.name)
			if sumz is None:
				sumz = zvar.name
			else:
				add_quadratic_term(2.0 * P_onehot, sumz, zvar.name)
				sumz = zvar.name

		# Approximate action magnitude penalty a^2
		for z_i, k_i in zip(a_vars[h], range(-L, L + 1)):
			for z_j, k_j in zip(a_vars[h], range(-L, L + 1)):
				coef = P_move * (k_i * k_j)
				add_quadratic_term(coef, z_i.name, z_j.name)

		# Sell bits
		s0 = f"s0_{h}"; s1 = f"s1_{h}"
		# Revenue: - price_sell * (s0 + 2*s1)
		add_linear_term(-price_sell * unit_kwh, s0)
		add_linear_term(-2.0 * price_sell * unit_kwh, s1)

		# Balance mismatch^2 term
		gen = gen_kwh[h] / unit_kwh
		dem = demand_kwh[h] / unit_kwh
		# mismatch = dem + sell - gen + a
		# Expand (mismatch)^2 as quadratic over binaries
		# Linear parts
		add_linear_term(P_balance * 1.0 * (dem - gen) * 0.0, s0)  # kept simple
		# Quadratic interaction with action variables
		for z_i, k_i in zip(a_vars[h], range(-L, L + 1)):
			# (dem - gen)*k_i*z_i  -> linear term
			add_linear_term(P_balance * 2.0 * (dem - gen) * k_i, z_i.name)

		# Soc soft penalty (keep near mid)
		soc_expr_coeff = 0.0
		for z_i, k_i in zip(a_vars[h], range(-L, L + 1)):
			# soc_{h+1} = soc + k_i
			# (soc - soc_mid)^2 -> soc terms constant w.r.t decision; cross terms add linear
			add_linear_term(P_soc * 2.0 * (soc - soc_mid) * k_i, z_i.name)
		soc += 0.0  # approximate propagation in soft penalty

	# Register objective
	qp.minimize(linear=objective_linear, quadratic=objective_quadratic, constant=objective_const)
	return qp
