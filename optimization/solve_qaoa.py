from typing import Dict, Any

from qiskit_aer.primitives import Sampler as AerSampler
from qiskit.algorithms import QAOA
from qiskit_optimization.algorithms import MinimumEigenOptimizer


def solve_quadratic_program(qp) -> Dict[str, Any]:
	sampler = AerSampler(options={"shots": 2048})
	qaoa = QAOA(sampler=sampler, reps=2)
	optimizer = MinimumEigenOptimizer(qaoa)
	result = optimizer.solve(qp)
	return {
		"fval": result.fval,
		"x": result.x,
		"variables": [v.name for v in qp.variables],
	}
