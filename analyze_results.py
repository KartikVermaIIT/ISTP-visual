"""
Visualization and analysis utilities for tree species classification results
"""

import ee
import pandas as pd
import numpy as np
from datetime import datetime


class ResultsAnalyzer:
    """Analyze and visualize classification results"""
    
    def __init__(self, classified_image, validation_data, class_names=None):
        """
        Args:
            classified_image: ee.Image with classification results
            validation_data: ee.FeatureCollection with validation points
            class_names: List of class names (optional)
        """
        self.classified_image = classified_image
        self.validation_data = validation_data
        self.class_names = class_names or [f'Class {i}' for i in range(7)]
    
    def compute_confusion_matrix(self, classifier):
        """
        Compute detailed confusion matrix
        
        Args:
            classifier: Trained ee.Classifier
            
        Returns:
            dict: Confusion matrix and accuracy metrics
        """
        # Classify validation data
        validated = self.validation_data.classify(classifier)
        
        # Compute confusion matrix
        confusion = validated.errorMatrix('class', 'classification')
        
        # Get matrix as array
        matrix_array = np.array(confusion.getInfo())
        
        # Compute metrics
        results = {
            'confusion_matrix': matrix_array,
            'overall_accuracy': confusion.accuracy().getInfo(),
            'kappa': confusion.kappa().getInfo(),
            'producers_accuracy': confusion.producersAccuracy().getInfo(),
            'consumers_accuracy': confusion.consumersAccuracy().getInfo()
        }
        
        return results
    
    def print_accuracy_report(self, confusion_results):
        """
        Print formatted accuracy report
        
        Args:
            confusion_results: Results from compute_confusion_matrix()
        """
        print("\n" + "="*60)
        print("CLASSIFICATION ACCURACY REPORT")
        print("="*60 + "\n")
        
        print(f"Overall Accuracy: {confusion_results['overall_accuracy']:.4f} ({confusion_results['overall_accuracy']*100:.2f}%)")
        print(f"Kappa Coefficient: {confusion_results['kappa']:.4f}")
        
        print("\n--- Confusion Matrix ---")
        matrix = confusion_results['confusion_matrix']
        
        # Print header
        print("\n" + " "*15 + "Predicted")
        print(" "*10, end="")
        for i, name in enumerate(self.class_names):
            print(f"{name:>12}", end="")
        print()
        
        print("Actual")
        for i, row in enumerate(matrix):
            print(f"{self.class_names[i]:>10}", end="")
            for val in row:
                print(f"{int(val):>12}", end="")
            print()
        
        print("\n--- Per-Class Accuracy ---")
        producers = confusion_results['producers_accuracy']
        consumers = confusion_results['consumers_accuracy']
        
        print(f"\n{'Class':<15} {'Producer':>12} {'User':>12} {'F1-Score':>12}")
        print("-" * 55)
        
        for i, name in enumerate(self.class_names):
            prod_acc = producers[i] if i < len(producers) else 0
            cons_acc = consumers[i] if i < len(consumers) else 0
            
            # Calculate F1 score
            if prod_acc + cons_acc > 0:
                f1 = 2 * (prod_acc * cons_acc) / (prod_acc + cons_acc)
            else:
                f1 = 0
            
            print(f"{name:<15} {prod_acc:>11.4f} {cons_acc:>11.4f} {f1:>11.4f}")
        
        print("\n" + "="*60 + "\n")
    
    def compute_area_statistics(self, scale=10):
        """
        Compute area statistics for each class
        
        Args:
            scale: Pixel size in meters
            
        Returns:
            dict: Area statistics per class
        """
        # Get pixel counts
        class_areas = self.classified_image.reduceRegion(
            reducer=ee.Reducer.frequencyHistogram(),
            scale=scale,
            maxPixels=1e13,
            bestEffort=True
        )
        
        # Convert to dictionary
        histogram = class_areas.getInfo()
        
        if 'classification' in histogram:
            histogram = histogram['classification']
        
        # Convert pixel counts to areas
        pixel_area_m2 = scale * scale
        area_stats = {}
        
        for class_str, pixel_count in histogram.items():
            class_id = int(class_str)
            area_hectares = (pixel_count * pixel_area_m2) / 10000
            area_km2 = area_hectares / 100
            
            area_stats[class_id] = {
                'pixels': pixel_count,
                'hectares': area_hectares,
                'km2': area_km2
            }
        
        return area_stats
    
    def print_area_report(self, area_stats):
        """
        Print formatted area statistics report
        
        Args:
            area_stats: Results from compute_area_statistics()
        """
        print("\n" + "="*60)
        print("AREA STATISTICS REPORT")
        print("="*60 + "\n")
        
        total_hectares = sum(stats['hectares'] for stats in area_stats.values())
        total_km2 = total_hectares / 100
        
        print(f"{'Class':<20} {'Pixels':>12} {'Hectares':>12} {'km²':>12} {'%':>8}")
        print("-" * 68)
        
        for class_id in sorted(area_stats.keys()):
            stats = area_stats[class_id]
            percentage = (stats['hectares'] / total_hectares * 100) if total_hectares > 0 else 0
            
            class_name = self.class_names[class_id] if class_id < len(self.class_names) else f'Class {class_id}'
            
            print(f"{class_name:<20} {stats['pixels']:>12,} {stats['hectares']:>12,.2f} "
                  f"{stats['km2']:>12,.4f} {percentage:>7.2f}%")
        
        print("-" * 68)
        print(f"{'TOTAL':<20} {sum(s['pixels'] for s in area_stats.values()):>12,} "
              f"{total_hectares:>12,.2f} {total_km2:>12,.4f} {'100.00':>7}%")
        
        print("\n" + "="*60 + "\n")
    
    def compare_forest_types(self, natural_zone, plantation_zone, scale=10):
        """
        Compare classification results between natural and plantation forests
        
        Args:
            natural_zone: ee.Geometry for natural forest
            plantation_zone: ee.Geometry for plantation forest
            scale: Pixel size in meters
            
        Returns:
            dict: Comparison results
        """
        # Get histograms for each zone
        natural_hist = self.classified_image.reduceRegion(
            reducer=ee.Reducer.frequencyHistogram(),
            geometry=natural_zone,
            scale=scale,
            maxPixels=1e13
        ).getInfo()
        
        plantation_hist = self.classified_image.reduceRegion(
            reducer=ee.Reducer.frequencyHistogram(),
            geometry=plantation_zone,
            scale=scale,
            maxPixels=1e13
        ).getInfo()
        
        # Extract classification histogram
        if 'classification' in natural_hist:
            natural_hist = natural_hist['classification']
        if 'classification' in plantation_hist:
            plantation_hist = plantation_hist['classification']
        
        pixel_area_m2 = scale * scale
        
        comparison = {
            'natural': {},
            'plantation': {}
        }
        
        # Process natural forest
        for class_str, count in natural_hist.items():
            class_id = int(class_str)
            comparison['natural'][class_id] = {
                'pixels': count,
                'hectares': (count * pixel_area_m2) / 10000
            }
        
        # Process plantation forest
        for class_str, count in plantation_hist.items():
            class_id = int(class_str)
            comparison['plantation'][class_id] = {
                'pixels': count,
                'hectares': (count * pixel_area_m2) / 10000
            }
        
        return comparison
    
    def print_forest_comparison(self, comparison_results):
        """
        Print forest type comparison report
        
        Args:
            comparison_results: Results from compare_forest_types()
        """
        print("\n" + "="*70)
        print("FOREST TYPE COMPARISON")
        print("="*70 + "\n")
        
        print(f"{'Class':<20} {'Natural (ha)':>15} {'Plantation (ha)':>18} {'Difference':>15}")
        print("-" * 70)
        
        all_classes = set(comparison_results['natural'].keys()) | set(comparison_results['plantation'].keys())
        
        total_natural = 0
        total_plantation = 0
        
        for class_id in sorted(all_classes):
            natural_ha = comparison_results['natural'].get(class_id, {}).get('hectares', 0)
            plantation_ha = comparison_results['plantation'].get(class_id, {}).get('hectares', 0)
            difference = natural_ha - plantation_ha
            
            total_natural += natural_ha
            total_plantation += plantation_ha
            
            class_name = self.class_names[class_id] if class_id < len(self.class_names) else f'Class {class_id}'
            
            diff_str = f"{difference:+,.2f}"
            print(f"{class_name:<20} {natural_ha:>15,.2f} {plantation_ha:>18,.2f} {diff_str:>15}")
        
        print("-" * 70)
        print(f"{'TOTAL':<20} {total_natural:>15,.2f} {total_plantation:>18,.2f} "
              f"{total_natural-total_plantation:>+15,.2f}")
        
        print("\n" + "="*70 + "\n")
    
    def export_results_to_csv(self, confusion_results, area_stats, output_dir='.'):
        """
        Export results to CSV files
        
        Args:
            confusion_results: Confusion matrix results
            area_stats: Area statistics
            output_dir: Output directory
        """
        from pathlib import Path
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Export confusion matrix
        confusion_df = pd.DataFrame(
            confusion_results['confusion_matrix'],
            index=self.class_names,
            columns=self.class_names
        )
        confusion_file = output_dir / f'confusion_matrix_{timestamp}.csv'
        confusion_df.to_csv(confusion_file)
        print(f"Saved confusion matrix: {confusion_file}")
        
        # Export accuracy metrics
        accuracy_data = {
            'Metric': ['Overall Accuracy', 'Kappa Coefficient'],
            'Value': [
                confusion_results['overall_accuracy'],
                confusion_results['kappa']
            ]
        }
        
        # Add per-class metrics
        for i, name in enumerate(self.class_names):
            accuracy_data['Metric'].extend([
                f'{name} - Producer Accuracy',
                f'{name} - User Accuracy'
            ])
            prod = confusion_results['producers_accuracy'][i] if i < len(confusion_results['producers_accuracy']) else 0
            user = confusion_results['consumers_accuracy'][i] if i < len(confusion_results['consumers_accuracy']) else 0
            accuracy_data['Value'].extend([prod, user])
        
        accuracy_df = pd.DataFrame(accuracy_data)
        accuracy_file = output_dir / f'accuracy_metrics_{timestamp}.csv'
        accuracy_df.to_csv(accuracy_file, index=False)
        print(f"Saved accuracy metrics: {accuracy_file}")
        
        # Export area statistics
        area_data = []
        for class_id in sorted(area_stats.keys()):
            stats = area_stats[class_id]
            class_name = self.class_names[class_id] if class_id < len(self.class_names) else f'Class {class_id}'
            area_data.append({
                'Class_ID': class_id,
                'Class_Name': class_name,
                'Pixels': stats['pixels'],
                'Area_Hectares': stats['hectares'],
                'Area_km2': stats['km2']
            })
        
        area_df = pd.DataFrame(area_data)
        area_file = output_dir / f'area_statistics_{timestamp}.csv'
        area_df.to_csv(area_file, index=False)
        print(f"Saved area statistics: {area_file}")
        
        print(f"\nAll results exported to: {output_dir}")
    
    def generate_summary_report(self, confusion_results, area_stats, output_file='classification_report.txt'):
        """
        Generate comprehensive text report
        
        Args:
            confusion_results: Confusion matrix results
            area_stats: Area statistics
            output_file: Output filename
        """
        with open(output_file, 'w') as f:
            f.write("="*70 + "\n")
            f.write("TREE SPECIES CLASSIFICATION - SUMMARY REPORT\n")
            f.write("="*70 + "\n\n")
            
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Overall accuracy
            f.write("OVERALL ACCURACY METRICS\n")
            f.write("-" * 70 + "\n")
            f.write(f"Overall Accuracy: {confusion_results['overall_accuracy']:.4f} ({confusion_results['overall_accuracy']*100:.2f}%)\n")
            f.write(f"Kappa Coefficient: {confusion_results['kappa']:.4f}\n\n")
            
            # Per-class accuracy
            f.write("PER-CLASS ACCURACY\n")
            f.write("-" * 70 + "\n")
            f.write(f"{'Class':<20} {'Producer Acc':>15} {'User Acc':>15} {'F1-Score':>15}\n")
            f.write("-" * 70 + "\n")
            
            for i, name in enumerate(self.class_names):
                prod = confusion_results['producers_accuracy'][i] if i < len(confusion_results['producers_accuracy']) else 0
                user = confusion_results['consumers_accuracy'][i] if i < len(confusion_results['consumers_accuracy']) else 0
                f1 = 2 * (prod * user) / (prod + user) if (prod + user) > 0 else 0
                
                f.write(f"{name:<20} {prod:>15.4f} {user:>15.4f} {f1:>15.4f}\n")
            
            f.write("\n")
            
            # Area statistics
            f.write("AREA COVERAGE\n")
            f.write("-" * 70 + "\n")
            
            total_hectares = sum(stats['hectares'] for stats in area_stats.values())
            
            for class_id in sorted(area_stats.keys()):
                stats = area_stats[class_id]
                percentage = (stats['hectares'] / total_hectares * 100) if total_hectares > 0 else 0
                class_name = self.class_names[class_id] if class_id < len(self.class_names) else f'Class {class_id}'
                
                f.write(f"{class_name:<20} {stats['hectares']:>12,.2f} ha ({percentage:>6.2f}%)\n")
            
            f.write("-" * 70 + "\n")
            f.write(f"{'TOTAL':<20} {total_hectares:>12,.2f} ha\n")
            
            f.write("\n" + "="*70 + "\n")
        
        print(f"Summary report saved: {output_file}")


def example_analyze_results():
    """Example: Analyze classification results"""
    import ee
    ee.Initialize()
    
    # Load classified image and validation data
    classified = ee.Image('users/YOUR_USERNAME/tree_species_classified')
    validation = ee.FeatureCollection('users/YOUR_USERNAME/validation_points')
    classifier = None  # Load your trained classifier
    
    # Define class names
    class_names = [
        'Oak', 'Pine', 'Spruce', 'Beech', 
        'Birch', 'Fir', 'Mixed'
    ]
    
    # Initialize analyzer
    analyzer = ResultsAnalyzer(classified, validation, class_names)
    
    # Compute and print confusion matrix
    confusion_results = analyzer.compute_confusion_matrix(classifier)
    analyzer.print_accuracy_report(confusion_results)
    
    # Compute and print area statistics
    area_stats = analyzer.compute_area_statistics(scale=10)
    analyzer.print_area_report(area_stats)
    
    # Export results
    analyzer.export_results_to_csv(confusion_results, area_stats, output_dir='results')
    
    # Generate summary report
    analyzer.generate_summary_report(confusion_results, area_stats, 
                                    output_file='results/classification_summary.txt')
    
    return analyzer


if __name__ == "__main__":
    print("="*60)
    print("Results Analysis Utilities")
    print("="*60 + "\n")
    
    print("To use these utilities:")
    print("1. Run the classification pipeline first")
    print("2. Load the classified image and validation data")
    print("3. Call example_analyze_results() with your data")
    print("\nExample:")
    print("  analyzer = example_analyze_results()")
