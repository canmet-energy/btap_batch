"""
Integration test for BTAP optimization with pymoo 0.6.1.5
This test creates a simplified optimization problem to validate the end-to-end workflow.
"""

import unittest
import numpy as np
from unittest.mock import Mock, patch
import sys
import os
from pathlib import Path

# Add the project root to the path so we can import the modules
PROJECT_ROOT = str(Path(os.path.dirname(os.path.realpath(__file__))).parent.absolute())
sys.path.append(PROJECT_ROOT)

from src.btap.btap_optimization import BTAPProblem
from pymoo.core.problem import StarmapParallelization
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.operators.sampling.rnd import IntegerRandomSampling
from pymoo.operators.repair.rounding import RoundingRepair
from pymoo.optimize import minimize
from multiprocessing.pool import ThreadPool


class SimpleBTAPOptimizationMock:
    """A simplified mock of BTAPOptimization for integration testing"""
    
    def __init__(self):
        self.algorithm_nsga_minimize_objectives = ['total_energy', 'capital_cost']
        self.max_number_of_simulations = 10
        self.pbar = Mock()
        self.pbar.update = Mock()
        
        # Mock counters
        self._completed_runs = 0
        self._failed_runs = 0
        
    def number_of_variables(self):
        return 2
        
    def x_u(self):
        return [3, 2]  # Upper bounds: [0-3] for var1, [0-2] for var2
        
    def generate_run_option_file(self, x):
        return {
            ':datapoint_id': f"test_dp_{x[0]}_{x[1]}",
            'option1': x[0],
            'option2': x[1]
        }
        
    def run_datapoint(self, run_options):
        """Simulate running a datapoint with a simple objective function"""
        # Simple test functions for multi-objective optimization
        x1 = run_options['option1']
        x2 = run_options['option2']
        
        # Objective 1: Minimize sum of squares (energy-like)
        total_energy = x1**2 + x2**2
        
        # Objective 2: Minimize weighted sum (cost-like) 
        capital_cost = 2*x1 + 3*x2
        
        return {
            'total_energy': total_energy,
            'capital_cost': capital_cost,
            ':datapoint_id': run_options[':datapoint_id']
        }
        
    def save_results_to_database(self, results):
        """Mock saving results"""
        self._completed_runs += 1
        
    def get_num_of_runs_completed(self):
        return self._completed_runs
        
    def get_num_of_runs_failed(self):
        return self._failed_runs


class TestBTAPOptimizationIntegration(unittest.TestCase):
    """Integration tests for the complete optimization workflow"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_btap_optimization = SimpleBTAPOptimizationMock()
        
    def test_btap_problem_with_real_optimization(self):
        """Test BTAPProblem with a real (but small) optimization run"""
        # Create the problem
        problem = BTAPProblem(btap_optimization=self.mock_btap_optimization)
        
        # Verify problem setup
        self.assertEqual(problem.n_var, 2)
        self.assertEqual(problem.n_obj, 2)
        self.assertEqual(problem.n_constr, 0)
        self.assertEqual(problem.xl, [0, 0])
        self.assertEqual(problem.xu, [3, 2])
        self.assertEqual(problem.type_var, int)
        
        # Test the evaluate function directly
        x = np.array([1, 2])
        out = {}
        problem._evaluate(x, out)
        
        # Check that objectives were computed
        self.assertIn("F", out)
        objectives = out["F"]
        self.assertEqual(len(objectives), 2)
        
        # Expected: total_energy = 1^2 + 2^2 = 5, capital_cost = 2*1 + 3*2 = 8
        expected_objectives = np.array([[5.0, 8.0]])
        np.testing.assert_array_equal(objectives, expected_objectives)
        
    def test_optimization_with_parallelization(self):
        """Test the optimization with parallelization using StarmapParallelization"""
        # Test with ThreadPool parallelization
        with ThreadPool(2) as pool:
            runner = StarmapParallelization(pool.starmap)
            
            # Create problem with parallelization
            problem = BTAPProblem(
                btap_optimization=self.mock_btap_optimization,
                elementwise_runner=runner
            )
            
            # Create a simple algorithm
            algorithm = NSGA2(
                pop_size=6,  # Small population for quick test
                sampling=IntegerRandomSampling(),
                crossover=SBX(prob=0.9, eta=15, vtype=float, repair=RoundingRepair()),
                mutation=PM(eta=20, vtype=float, repair=RoundingRepair()),
                eliminate_duplicates=True,
            )
            
            # Run optimization for just 2 generations
            result = minimize(
                problem,
                algorithm,
                termination=('n_gen', 2),
                seed=1,
                verbose=False
            )
            
            # Check that optimization completed
            self.assertIsNotNone(result)
            self.assertIsNotNone(result.X)
            self.assertIsNotNone(result.F)
            
            # Check that we have the right number of objectives
            self.assertEqual(result.F.shape[1], 2)
            
            # Check that solutions are within bounds
            for solution in result.X:
                self.assertTrue(0 <= solution[0] <= 3)
                self.assertTrue(0 <= solution[1] <= 2)
                
            # Check that some evaluations were performed
            self.assertGreater(self.mock_btap_optimization.get_num_of_runs_completed(), 0)
            
    def test_optimization_without_parallelization(self):
        """Test the optimization without parallelization (serial execution)"""
        # Create problem without parallelization
        problem = BTAPProblem(btap_optimization=self.mock_btap_optimization)
        
        # Create a simple algorithm
        algorithm = NSGA2(
            pop_size=4,  # Small population for quick test
            sampling=IntegerRandomSampling(),
            crossover=SBX(prob=0.9, eta=15, vtype=float, repair=RoundingRepair()),
            mutation=PM(eta=20, vtype=float, repair=RoundingRepair()),
            eliminate_duplicates=True,
        )
        
        # Run optimization for just 1 generation
        result = minimize(
            problem,
            algorithm,
            termination=('n_gen', 1),
            seed=1,
            verbose=False
        )
        
        # Check that optimization completed
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.X)
        self.assertIsNotNone(result.F)
        
        # Check that we have the right number of objectives
        self.assertEqual(result.F.shape[1], 2)
        
        # Check that solutions are within bounds
        for solution in result.X:
            self.assertTrue(0 <= solution[0] <= 3)
            self.assertTrue(0 <= solution[1] <= 2)
            
        # Check that some evaluations were performed
        self.assertGreater(self.mock_btap_optimization.get_num_of_runs_completed(), 0)
        
    def test_algorithm_configuration_compatibility(self):
        """Test that the new algorithm configuration works correctly"""
        # Test all the operator configurations
        sampling = IntegerRandomSampling()
        crossover = SBX(prob=0.9, eta=15, vtype=float, repair=RoundingRepair())
        mutation = PM(eta=20, vtype=float, repair=RoundingRepair())
        
        algorithm = NSGA2(
            pop_size=10,
            sampling=sampling,
            crossover=crossover,
            mutation=mutation,
            eliminate_duplicates=True,
        )
        
        # Check that algorithm has the expected properties
        self.assertEqual(algorithm.pop_size, 10)
        self.assertIsInstance(algorithm.sampling, IntegerRandomSampling)
        self.assertIsInstance(algorithm.crossover, SBX)
        self.assertIsInstance(algorithm.mutation, PM)
        self.assertTrue(algorithm.eliminate_duplicates)
        
        # Check operator configurations
        self.assertEqual(crossover.prob, 0.9)
        self.assertEqual(crossover.eta, 15)
        self.assertIsInstance(crossover.repair, RoundingRepair)
        
        self.assertEqual(mutation.eta, 20)
        self.assertIsInstance(mutation.repair, RoundingRepair)


class TestBackwardCompatibility(unittest.TestCase):
    """Test that the changes maintain backward compatibility"""
    
    def test_btap_problem_api_compatibility(self):
        """Test that BTAPProblem API remains compatible"""
        mock_btap_optimization = SimpleBTAPOptimizationMock()
        
        # Old way (without elementwise_runner) should still work
        problem = BTAPProblem(btap_optimization=mock_btap_optimization)
        self.assertIsNotNone(problem)
        
        # New way (with elementwise_runner) should also work
        with ThreadPool(1) as pool:
            runner = StarmapParallelization(pool.starmap)
            problem_with_runner = BTAPProblem(
                btap_optimization=mock_btap_optimization,
                elementwise_runner=runner
            )
            self.assertIsNotNone(problem_with_runner)
            
    def test_problem_properties_unchanged(self):
        """Test that problem properties are unchanged"""
        mock_btap_optimization = SimpleBTAPOptimizationMock()
        problem = BTAPProblem(btap_optimization=mock_btap_optimization)
        
        # Check that all expected attributes exist
        self.assertTrue(hasattr(problem, 'n_var'))
        self.assertTrue(hasattr(problem, 'n_obj'))
        self.assertTrue(hasattr(problem, 'n_constr'))
        self.assertTrue(hasattr(problem, 'xl'))
        self.assertTrue(hasattr(problem, 'xu'))
        self.assertTrue(hasattr(problem, 'type_var'))
        self.assertTrue(hasattr(problem, '_evaluate'))
        
        # Check that the evaluate method signature is unchanged
        import inspect
        sig = inspect.signature(problem._evaluate)
        param_names = list(sig.parameters.keys())
        self.assertIn('x', param_names)
        self.assertIn('out', param_names)


if __name__ == '__main__':
    unittest.main()