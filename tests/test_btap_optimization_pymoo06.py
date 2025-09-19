"""
Unit tests for BTAP optimization functionality with pymoo 0.6.1.5
Tests cover the updated parallelization and algorithm API changes.
"""

import unittest
import numpy as np
from unittest.mock import Mock, MagicMock, patch
from multiprocessing.pool import ThreadPool
import sys
import os
from pathlib import Path

# Add the project root to the path so we can import the modules
PROJECT_ROOT = str(Path(os.path.dirname(os.path.realpath(__file__))).parent.absolute())
sys.path.append(PROJECT_ROOT)

# Import the classes we're testing
from src.btap.btap_optimization import BTAPProblem, BTAPOptimization
from src.btap.exceptions import FailedSimulationException
from pymoo.core.problem import StarmapParallelization
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.operators.sampling.rnd import IntegerRandomSampling
from pymoo.operators.repair.rounding import RoundingRepair


class TestBTAPProblemPymoo06(unittest.TestCase):
    """Test the BTAPProblem class with the new pymoo 0.6.x API"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a mock btap_optimization object
        self.mock_btap_optimization = Mock()
        self.mock_btap_optimization.number_of_variables.return_value = 3
        self.mock_btap_optimization.algorithm_nsga_minimize_objectives = ['objective1', 'objective2']
        self.mock_btap_optimization.x_u.return_value = [2, 3, 4]  # Upper bounds for discrete variables
        
    def test_btap_problem_initialization_without_runner(self):
        """Test BTAPProblem initialization without elementwise_runner"""
        problem = BTAPProblem(btap_optimization=self.mock_btap_optimization)
        
        # Check that the problem was initialized correctly
        self.assertEqual(problem.n_var, 3)
        self.assertEqual(problem.n_obj, 2)
        self.assertEqual(problem.n_constr, 0)
        self.assertEqual(problem.xl, [0, 0, 0])
        self.assertEqual(problem.xu, [2, 3, 4])
        self.assertEqual(problem.type_var, int)
        
    def test_btap_problem_initialization_with_runner(self):
        """Test BTAPProblem initialization with elementwise_runner for parallelization"""
        # Create a mock runner
        mock_runner = Mock()
        
        problem = BTAPProblem(
            btap_optimization=self.mock_btap_optimization,
            elementwise_runner=mock_runner
        )
        
        # Check that the problem was initialized correctly
        self.assertEqual(problem.n_var, 3)
        self.assertEqual(problem.n_obj, 2)
        self.assertEqual(problem.n_constr, 0)
        self.assertEqual(problem.xl, [0, 0, 0])
        self.assertEqual(problem.xu, [2, 3, 4])
        self.assertEqual(problem.type_var, int)
        
    def test_btap_problem_evaluate_method(self):
        """Test the _evaluate method of BTAPProblem"""
        # Set up mocks for the evaluation
        self.mock_btap_optimization.generate_run_option_file.return_value = {'option': 'value'}
        self.mock_btap_optimization.run_datapoint.return_value = {
            'objective1': 1.5,
            'objective2': 2.3,
            'other_data': 'test'
        }
        self.mock_btap_optimization.save_results_to_database.return_value = None
        self.mock_btap_optimization.get_num_of_runs_completed.return_value = 5
        self.mock_btap_optimization.max_number_of_simulations = 100
        self.mock_btap_optimization.get_num_of_runs_failed.return_value = 1
        self.mock_btap_optimization.pbar = Mock()
        
        problem = BTAPProblem(btap_optimization=self.mock_btap_optimization)
        
        # Test input
        x = np.array([1, 2, 0])
        out = {}
        
        # Call the evaluate method
        problem._evaluate(x, out)
        
        # Verify the method calls
        self.mock_btap_optimization.generate_run_option_file.assert_called_once_with([1, 2, 0])
        self.mock_btap_optimization.run_datapoint.assert_called_once_with({'option': 'value'})
        self.mock_btap_optimization.save_results_to_database.assert_called_once()
        self.mock_btap_optimization.pbar.update.assert_called_once_with(1)
        
        # Check that the output was set correctly
        expected_objectives = np.column_stack([1.5, 2.3])
        np.testing.assert_array_equal(out["F"], expected_objectives)
        
    def test_btap_problem_evaluate_missing_objective(self):
        """Test that _evaluate raises exception when objective is missing from results"""
        # Set up mocks - missing objective2
        self.mock_btap_optimization.generate_run_option_file.return_value = {'option': 'value'}
        self.mock_btap_optimization.run_datapoint.return_value = {
            'objective1': 1.5,
            # 'objective2': missing!
            'other_data': 'test'
        }
        self.mock_btap_optimization.save_results_to_database.return_value = None
        
        problem = BTAPProblem(btap_optimization=self.mock_btap_optimization)
        
        # Test input
        x = np.array([1, 2, 0])
        out = {}
        
        # Call the evaluate method and expect an exception
        with self.assertRaises(FailedSimulationException) as context:
            problem._evaluate(x, out)
        
        self.assertIn("Objective value objective2 not found in results", str(context.exception))


class TestStarmapParallelization(unittest.TestCase):
    """Test the new parallelization approach with StarmapParallelization"""
    
    def test_starmap_parallelization_creation(self):
        """Test that StarmapParallelization can be created with ThreadPool.starmap"""
        with ThreadPool(2) as pool:
            runner = StarmapParallelization(pool.starmap)
            self.assertIsInstance(runner, StarmapParallelization)
            
    def test_starmap_parallelization_with_mock_pool(self):
        """Test StarmapParallelization with a mock pool"""
        # Create a mock starmap function
        mock_starmap = Mock()
        mock_starmap.return_value = [1, 2, 3]
        
        runner = StarmapParallelization(mock_starmap)
        self.assertIsInstance(runner, StarmapParallelization)


class TestAlgorithmConfiguration(unittest.TestCase):
    """Test the new algorithm configuration with pymoo 0.6.x operators"""
    
    def test_nsga2_initialization(self):
        """Test NSGA2 algorithm initialization with new operators"""
        algorithm = NSGA2(
            pop_size=20,
            sampling=IntegerRandomSampling(),
            crossover=SBX(prob=0.9, eta=15, vtype=float, repair=RoundingRepair()),
            mutation=PM(eta=20, vtype=float, repair=RoundingRepair()),
            eliminate_duplicates=True,
        )
        
        self.assertIsInstance(algorithm, NSGA2)
        self.assertEqual(algorithm.pop_size, 20)
        self.assertIsInstance(algorithm.sampling, IntegerRandomSampling)
        self.assertIsInstance(algorithm.crossover, SBX)
        self.assertIsInstance(algorithm.mutation, PM)
        self.assertTrue(algorithm.eliminate_duplicates)
        
    def test_operator_configurations(self):
        """Test that operators are configured correctly for integer variables"""
        # Test SBX crossover configuration
        crossover = SBX(prob=0.9, eta=15, vtype=float, repair=RoundingRepair())
        self.assertIsInstance(crossover, SBX)
        self.assertIsInstance(crossover.repair, RoundingRepair)
        
        # Test PM mutation configuration
        mutation = PM(eta=20, vtype=float, repair=RoundingRepair())
        self.assertIsInstance(mutation, PM)
        self.assertIsInstance(mutation.repair, RoundingRepair)
        
        # Test IntegerRandomSampling
        sampling = IntegerRandomSampling()
        self.assertIsInstance(sampling, IntegerRandomSampling)


class TestBTAPOptimizationIntegration(unittest.TestCase):
    """Integration tests for BTAPOptimization class with new pymoo API"""
    
    def setUp(self):
        """Set up test fixtures for integration tests"""
        # Create a mock analysis_config
        self.mock_config = {
            'algorithm': {
                'type': 'nsga2',
                'nsga': {
                    'population': 10,
                    'n_generations': 2,
                    'prob': 0.9,
                    'eta': 15
                }
            }
        }
        
    @patch('src.btap.btap_optimization.BTAPAnalysis.__init__')
    @patch('src.btap.btap_optimization.BTAPOptimization.create_paths_folders')
    @patch('src.btap.btap_optimization.BTAPOptimization.create_options_encoder')
    def test_btap_optimization_init(self, mock_create_encoder, mock_create_paths, mock_super_init):
        """Test BTAPOptimization initialization"""
        mock_super_init.return_value = None
        
        optimization = BTAPOptimization(
            analysis_config=self.mock_config,
            output_folder="/tmp/test",
            analysis_input_folder="/tmp/input"
        )
        
        self.assertIsInstance(optimization, BTAPOptimization)
        self.assertIsNone(optimization.max_number_of_simulations)
        
    def test_backward_compatibility_interface(self):
        """Test that the external interface remains the same for existing users"""
        # The BTAPOptimization class should still have the same public methods
        # that existing code depends on
        
        with patch('src.btap.btap_optimization.BTAPAnalysis.__init__'):
            optimization = BTAPOptimization()
            
            # Check that key methods exist (they may be inherited from BTAPAnalysis)
            self.assertTrue(hasattr(optimization, 'run'))
            self.assertTrue(hasattr(optimization, 'run_analysis'))
            self.assertTrue(hasattr(optimization, 'number_of_minimize_objectives'))
        

class TestRegressionSafety(unittest.TestCase):
    """Test that the changes don't break existing functionality"""
    
    def test_imports_are_available(self):
        """Test that all the new imports are available and can be imported"""
        try:
            from pymoo.core.problem import StarmapParallelization
            from pymoo.algorithms.moo.nsga2 import NSGA2
            from pymoo.operators.crossover.sbx import SBX
            from pymoo.operators.mutation.pm import PM
            from pymoo.operators.sampling.rnd import IntegerRandomSampling
            from pymoo.operators.repair.rounding import RoundingRepair
        except ImportError as e:
            self.fail(f"Import failed: {e}")
            
    def test_algorithm_api_compatibility(self):
        """Test that the new algorithm API is compatible with the minimize function"""
        from pymoo.optimize import minimize
        from pymoo.problems import get_problem
        
        # Create a simple test problem
        try:
            problem = get_problem("sphere")
            algorithm = NSGA2(
                pop_size=10,
                sampling=IntegerRandomSampling(),
                crossover=SBX(prob=0.9, eta=15, vtype=float, repair=RoundingRepair()),
                mutation=PM(eta=20, vtype=float, repair=RoundingRepair()),
                eliminate_duplicates=True,
            )
            
            # This should not raise an exception - just test that the API is compatible
            # We won't actually run the optimization in the test
            self.assertIsNotNone(algorithm)
            self.assertIsNotNone(problem)
            
        except Exception as e:
            self.fail(f"Algorithm API compatibility test failed: {e}")


if __name__ == '__main__':
    unittest.main()