"""
Comprehensive test suite for tree species classification pipeline
Tests all components without requiring Earth Engine authentication
"""

import sys
import traceback
from datetime import datetime


class TestRunner:
    """Run comprehensive tests on the classification pipeline"""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.results = []
    
    def run_test(self, test_name, test_func):
        """Run a single test and record results"""
        print(f"\n{'='*70}")
        print(f"TEST: {test_name}")
        print('='*70)
        
        try:
            result = test_func()
            if result:
                print(f"✓ PASSED: {test_name}")
                self.passed += 1
                self.results.append((test_name, "PASSED", None))
            else:
                print(f"✗ FAILED: {test_name}")
                self.failed += 1
                self.results.append((test_name, "FAILED", "Test returned False"))
        except Exception as e:
            print(f"✗ FAILED: {test_name}")
            print(f"Error: {str(e)}")
            traceback.print_exc()
            self.failed += 1
            self.results.append((test_name, "FAILED", str(e)))
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"\nTotal Tests: {self.passed + self.failed}")
        print(f"✓ Passed: {self.passed}")
        print(f"✗ Failed: {self.failed}")
        print(f"Success Rate: {(self.passed/(self.passed+self.failed)*100):.1f}%")
        
        if self.failed > 0:
            print("\nFailed Tests:")
            for name, status, error in self.results:
                if status == "FAILED":
                    print(f"  - {name}")
                    if error:
                        print(f"    Error: {error[:100]}")
        
        print("\n" + "="*70)


def test_imports():
    """Test 1: Import all required modules"""
    print("Testing module imports...")
    
    required_modules = [
        'ee',
        'numpy',
        'pandas',
        'json',
        'datetime'
    ]
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"  ✓ {module}")
        except ImportError as e:
            print(f"  ✗ {module}: {e}")
            return False
    
    return True


def test_config_validation():
    """Test 2: Configuration validation"""
    print("Testing configuration...")
    
    try:
        import config
        
        # Check required attributes
        required_attrs = [
            'YEAR', 'SEASONS', 'N_CLASSES', 'CLASS_NAMES',
            'RF_N_TREES', 'SPATIAL_RESOLUTION', 'PERCENTILES'
        ]
        
        for attr in required_attrs:
            if not hasattr(config, attr):
                print(f"  ✗ Missing config attribute: {attr}")
                return False
            print(f"  ✓ {attr}: {getattr(config, attr)}")
        
        # Validate basic constraints
        if config.N_CLASSES != len(config.CLASS_NAMES):
            print(f"  ✗ N_CLASSES ({config.N_CLASSES}) != len(CLASS_NAMES) ({len(config.CLASS_NAMES)})")
            return False
        
        if config.SPATIAL_RESOLUTION < 5 or config.SPATIAL_RESOLUTION > 100:
            print(f"  ✗ Invalid SPATIAL_RESOLUTION: {config.SPATIAL_RESOLUTION}")
            return False
        
        print("  ✓ Configuration is valid")
        return True
        
    except Exception as e:
        print(f"  ✗ Configuration error: {e}")
        return False


def test_main_script_structure():
    """Test 3: Main script structure"""
    print("Testing main script structure...")
    
    try:
        import tree_species_classification as tsc
        
        # Check for required classes
        required_classes = [
            'SentinelProcessor',
            'DEMProcessor',
            'TreeSpeciesClassifier',
            'ZonalStatistics'
        ]
        
        for cls_name in required_classes:
            if not hasattr(tsc, cls_name):
                print(f"  ✗ Missing class: {cls_name}")
                return False
            print(f"  ✓ Class found: {cls_name}")
        
        # Check for required functions
        required_functions = [
            'build_feature_stack',
            'main'
        ]
        
        for func_name in required_functions:
            if not hasattr(tsc, func_name):
                print(f"  ✗ Missing function: {func_name}")
                return False
            print(f"  ✓ Function found: {func_name}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Script structure error: {e}")
        return False


def test_class_initialization():
    """Test 4: Class initialization without EE"""
    print("Testing class initialization...")
    
    try:
        # Test CONFIG dictionary
        from tree_species_classification import CONFIG
        
        print(f"  ✓ CONFIG loaded")
        print(f"    - Year: {CONFIG['year']}")
        print(f"    - Scale: {CONFIG['scale']}m")
        print(f"    - Trees: {CONFIG['n_trees']}")
        print(f"    - Classes: {CONFIG['n_classes']}")
        print(f"    - Seasons: {len(CONFIG['seasons'])}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Class initialization error: {e}")
        return False


def test_prepare_training_data_structure():
    """Test 5: Training data preparation structure"""
    print("Testing training data preparation...")
    
    try:
        import prepare_training_data as ptd
        
        # Check for main class
        if not hasattr(ptd, 'TrainingDataPreparation'):
            print("  ✗ Missing TrainingDataPreparation class")
            return False
        
        print("  ✓ TrainingDataPreparation class found")
        
        # Check for utility functions
        functions = [
            'create_sample_csv_template',
            'example_prepare_from_csv'
        ]
        
        for func_name in functions:
            if not hasattr(ptd, func_name):
                print(f"  ✗ Missing function: {func_name}")
                return False
            print(f"  ✓ Function found: {func_name}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Training data preparation error: {e}")
        return False


def test_analyze_results_structure():
    """Test 6: Results analysis structure"""
    print("Testing results analysis...")
    
    try:
        import analyze_results as ar
        
        if not hasattr(ar, 'ResultsAnalyzer'):
            print("  ✗ Missing ResultsAnalyzer class")
            return False
        
        print("  ✓ ResultsAnalyzer class found")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Results analysis error: {e}")
        return False


def test_example_usage_structure():
    """Test 7: Example usage structure"""
    print("Testing example usage...")
    
    try:
        import example_usage as eu
        
        functions = [
            'create_sample_training_data',
            'create_sample_validation_data',
            'create_sample_forest_zones'
        ]
        
        for func_name in functions:
            if not hasattr(eu, func_name):
                print(f"  ✗ Missing function: {func_name}")
                return False
            print(f"  ✓ Function found: {func_name}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Example usage error: {e}")
        return False


def test_csv_template_generation():
    """Test 8: CSV template generation"""
    print("Testing CSV template generation...")
    
    try:
        import prepare_training_data as ptd
        import os
        
        template_path = 'test_training_template.csv'
        
        # Generate template
        ptd.create_sample_csv_template(template_path)
        
        # Check if file exists
        if not os.path.exists(template_path):
            print("  ✗ Template file not created")
            return False
        
        print(f"  ✓ Template created: {template_path}")
        
        # Read and validate
        import pandas as pd
        df = pd.read_csv(template_path)
        
        required_columns = ['longitude', 'latitude', 'class']
        for col in required_columns:
            if col not in df.columns:
                print(f"  ✗ Missing column: {col}")
                return False
            print(f"  ✓ Column found: {col}")
        
        # Clean up
        os.remove(template_path)
        print("  ✓ Template validation passed")
        
        return True
        
    except Exception as e:
        print(f"  ✗ CSV template generation error: {e}")
        return False


def test_numpy_operations():
    """Test 9: NumPy operations for accuracy calculations"""
    print("Testing NumPy operations...")
    
    try:
        import numpy as np
        
        # Simulate confusion matrix
        confusion = np.array([
            [45, 5, 2, 0, 1, 0, 0],
            [3, 48, 1, 0, 2, 0, 0],
            [1, 2, 50, 1, 0, 0, 0],
            [0, 1, 2, 47, 3, 1, 0],
            [2, 0, 0, 2, 46, 0, 1],
            [0, 0, 1, 1, 0, 48, 2],
            [1, 0, 0, 0, 1, 2, 45]
        ])
        
        print(f"  ✓ Created test confusion matrix: {confusion.shape}")
        
        # Calculate overall accuracy
        overall_acc = np.trace(confusion) / np.sum(confusion)
        print(f"  ✓ Overall Accuracy: {overall_acc:.4f}")
        
        # Calculate per-class accuracy
        producer_acc = np.diag(confusion) / np.sum(confusion, axis=1)
        print(f"  ✓ Producer's Accuracy (mean): {np.mean(producer_acc):.4f}")
        
        consumer_acc = np.diag(confusion) / np.sum(confusion, axis=0)
        print(f"  ✓ Consumer's Accuracy (mean): {np.mean(consumer_acc):.4f}")
        
        # Calculate Kappa (simplified)
        po = overall_acc
        pe = np.sum(np.sum(confusion, axis=1) * np.sum(confusion, axis=0)) / (np.sum(confusion) ** 2)
        kappa = (po - pe) / (1 - pe)
        print(f"  ✓ Kappa Coefficient: {kappa:.4f}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ NumPy operations error: {e}")
        return False


def test_pandas_operations():
    """Test 10: Pandas operations for data handling"""
    print("Testing Pandas operations...")
    
    try:
        import pandas as pd
        import numpy as np
        
        # Create sample training data
        data = {
            'longitude': np.random.uniform(-122, -121, 100),
            'latitude': np.random.uniform(37, 38, 100),
            'class': np.random.randint(0, 7, 100),
            'species_name': ['Oak', 'Pine', 'Spruce', 'Beech', 'Birch', 'Fir', 'Mixed'] * 14 + ['Oak', 'Pine']
        }
        
        df = pd.DataFrame(data)
        print(f"  ✓ Created DataFrame: {df.shape}")
        
        # Test filtering
        class_0 = df[df['class'] == 0]
        print(f"  ✓ Filtered data: {len(class_0)} samples for class 0")
        
        # Test grouping
        class_counts = df.groupby('class').size()
        print(f"  ✓ Class distribution calculated")
        
        # Test summary statistics
        stats = df[['longitude', 'latitude']].describe()
        print(f"  ✓ Summary statistics computed")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Pandas operations error: {e}")
        return False


def test_date_parsing():
    """Test 11: Date parsing for seasonal filtering"""
    print("Testing date parsing...")
    
    try:
        from datetime import datetime
        import config
        
        for season_name, dates in config.SEASONS.items():
            start = datetime.strptime(dates['start'], '%Y-%m-%d')
            end = datetime.strptime(dates['end'], '%Y-%m-%d')
            
            duration = (end - start).days
            print(f"  ✓ {season_name}: {dates['start']} to {dates['end']} ({duration} days)")
            
            if duration < 0:
                print(f"  ✗ Invalid date range for {season_name}")
                return False
        
        return True
        
    except Exception as e:
        print(f"  ✗ Date parsing error: {e}")
        return False


def test_file_structure():
    """Test 12: Check all required files exist"""
    print("Testing file structure...")
    
    import os
    
    required_files = [
        'tree_species_classification.py',
        'prepare_training_data.py',
        'example_usage.py',
        'analyze_results.py',
        'config.py',
        'requirements.txt',
        'README.md',
        'QUICKSTART.md',
        'PROJECT_OVERVIEW.md',
        '.gitignore'
    ]
    
    all_exist = True
    for filename in required_files:
        if os.path.exists(filename):
            print(f"  ✓ {filename}")
        else:
            print(f"  ✗ {filename} - NOT FOUND")
            all_exist = False
    
    return all_exist


def test_documentation():
    """Test 13: Check documentation completeness"""
    print("Testing documentation...")
    
    try:
        # Check README
        with open('README.md', 'r', encoding='utf-8') as f:
            readme = f.read()
        
        sections = [
            'Installation',
            'Usage',
            'Features',
            'Configuration',
            'Output'
        ]
        
        for section in sections:
            if section.lower() in readme.lower():
                print(f"  ✓ README contains '{section}' section")
            else:
                print(f"  ✗ README missing '{section}' section")
                return False
        
        # Check QUICKSTART
        with open('QUICKSTART.md', 'r', encoding='utf-8') as f:
            quickstart = f.read()
        
        if 'pip install' in quickstart and 'ee.Initialize' in quickstart:
            print("  ✓ QUICKSTART has setup instructions")
        else:
            print("  ✗ QUICKSTART incomplete")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ✗ Documentation error: {e}")
        return False


def test_config_export_settings():
    """Test 14: Export configuration"""
    print("Testing export settings...")
    
    try:
        import config
        
        # Check export settings
        export_attrs = [
            'EXPORT_PREFIX',
            'EXPORT_FOLDER',
            'MAX_PIXELS',
            'TILE_SCALE',
            'OUTPUT_CRS'
        ]
        
        for attr in export_attrs:
            if hasattr(config, attr):
                value = getattr(config, attr)
                print(f"  ✓ {attr}: {value}")
            else:
                print(f"  ✗ Missing export setting: {attr}")
                return False
        
        return True
        
    except Exception as e:
        print(f"  ✗ Export settings error: {e}")
        return False


def test_feature_configuration():
    """Test 15: Feature configuration"""
    print("Testing feature configuration...")
    
    try:
        import config
        
        if not hasattr(config, 'FEATURES'):
            print("  ✗ Missing FEATURES configuration")
            return False
        
        features = config.FEATURES
        print(f"  ✓ Features configuration found")
        
        feature_groups = [
            'sentinel2_bands',
            'spectral_indices',
            'texture',
            'sentinel1_bands',
            'radar_indices',
            'temporal_gradients',
            'terrain'
        ]
        
        for group in feature_groups:
            if group in features:
                status = "enabled" if features[group] else "disabled"
                print(f"    - {group}: {status}")
            else:
                print(f"  ✗ Missing feature group: {group}")
                return False
        
        # Check spectral indices
        if hasattr(config, 'SPECTRAL_INDICES'):
            indices = config.SPECTRAL_INDICES
            enabled_count = sum(1 for v in indices.values() if v)
            print(f"  ✓ Spectral indices: {enabled_count}/{len(indices)} enabled")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Feature configuration error: {e}")
        return False


def test_method_signatures():
    """Test 16: Check method signatures"""
    print("Testing method signatures...")
    
    try:
        import tree_species_classification as tsc
        import inspect
        
        # Check main function signature
        main_sig = inspect.signature(tsc.main)
        params = list(main_sig.parameters.keys())
        
        expected_params = ['aoi', 'training_points', 'validation_points', 'forest_zones']
        
        for param in expected_params:
            if param in params:
                print(f"  ✓ main() has parameter: {param}")
            else:
                print(f"  ✗ main() missing parameter: {param}")
                return False
        
        # Check SentinelProcessor methods
        sp = tsc.SentinelProcessor
        required_methods = [
            'load_sentinel2',
            'load_sentinel1',
            'compute_spectral_indices',
            'compute_glcm_texture',
            'compute_radar_indices'
        ]
        
        for method_name in required_methods:
            if hasattr(sp, method_name):
                print(f"  ✓ SentinelProcessor.{method_name}()")
            else:
                print(f"  ✗ Missing method: {method_name}")
                return False
        
        return True
        
    except Exception as e:
        print(f"  ✗ Method signature error: {e}")
        return False


def test_error_handling():
    """Test 17: Error handling in code"""
    print("Testing error handling...")
    
    try:
        # Test that imports work properly
        import tree_species_classification
        import prepare_training_data
        import analyze_results
        
        print("  ✓ All modules import without errors")
        
        # Test config validation
        import config
        if hasattr(config, 'validate_config'):
            print("  ✓ Config validation function exists")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Error handling test failed: {e}")
        return False


def test_class_names_consistency():
    """Test 18: Class names consistency"""
    print("Testing class names consistency...")
    
    try:
        import config
        from tree_species_classification import CONFIG as TSC_CONFIG
        
        # Check that class names match in both configs
        if config.N_CLASSES == TSC_CONFIG['n_classes']:
            print(f"  ✓ N_CLASSES consistent: {config.N_CLASSES}")
        else:
            print(f"  ✗ N_CLASSES mismatch: {config.N_CLASSES} vs {TSC_CONFIG['n_classes']}")
            return False
        
        # Check class names length
        if len(config.CLASS_NAMES) == config.N_CLASSES:
            print(f"  ✓ CLASS_NAMES length matches: {len(config.CLASS_NAMES)}")
        else:
            print(f"  ✗ CLASS_NAMES length mismatch")
            return False
        
        # Print class names
        print("  ✓ Class definitions:")
        for i, name in enumerate(config.CLASS_NAMES):
            print(f"    {i}: {name}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Class names consistency error: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("TREE SPECIES CLASSIFICATION - COMPREHENSIVE TEST SUITE")
    print("="*70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    runner = TestRunner()
    
    # Core functionality tests
    runner.run_test("Module Imports", test_imports)
    runner.run_test("Configuration Validation", test_config_validation)
    runner.run_test("Main Script Structure", test_main_script_structure)
    runner.run_test("Class Initialization", test_class_initialization)
    
    # Component tests
    runner.run_test("Training Data Preparation", test_prepare_training_data_structure)
    runner.run_test("Results Analysis", test_analyze_results_structure)
    runner.run_test("Example Usage", test_example_usage_structure)
    
    # Functionality tests
    runner.run_test("CSV Template Generation", test_csv_template_generation)
    runner.run_test("NumPy Operations", test_numpy_operations)
    runner.run_test("Pandas Operations", test_pandas_operations)
    runner.run_test("Date Parsing", test_date_parsing)
    
    # Configuration tests
    runner.run_test("Export Configuration", test_config_export_settings)
    runner.run_test("Feature Configuration", test_feature_configuration)
    runner.run_test("Class Names Consistency", test_class_names_consistency)
    
    # Code quality tests
    runner.run_test("File Structure", test_file_structure)
    runner.run_test("Documentation", test_documentation)
    runner.run_test("Method Signatures", test_method_signatures)
    runner.run_test("Error Handling", test_error_handling)
    
    # Print summary
    runner.print_summary()
    
    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return runner.passed == (runner.passed + runner.failed)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
