"""
Utilities for preparing training and validation data for tree species classification
Supports multiple input formats: CSV, Shapefile, GeoJSON, KML
"""

import ee
import pandas as pd
import json
from pathlib import Path


class TrainingDataPreparation:
    """Prepare training and validation data for GEE classification"""
    
    def __init__(self):
        """Initialize Earth Engine"""
        # Note: Users should call ee.Initialize() before creating this class
        pass
    
    def from_csv(self, csv_path, lon_col='longitude', lat_col='latitude', 
                 class_col='class', crs='EPSG:4326'):
        """
        Create FeatureCollection from CSV file
        
        Args:
            csv_path: Path to CSV file
            lon_col: Column name for longitude
            lat_col: Column name for latitude
            class_col: Column name for class labels
            crs: Coordinate reference system
            
        Returns:
            ee.FeatureCollection
        """
        df = pd.read_csv(csv_path)
        
        features = []
        for idx, row in df.iterrows():
            lon = float(row[lon_col])
            lat = float(row[lat_col])
            class_val = int(row[class_col])
            
            # Create point geometry
            point = ee.Geometry.Point([lon, lat], crs)
            
            # Create feature with properties
            properties = {class_col: class_val}
            
            # Add all other columns as properties
            for col in df.columns:
                if col not in [lon_col, lat_col, class_col]:
                    properties[col] = row[col]
            
            feature = ee.Feature(point, properties)
            features.append(feature)
        
        fc = ee.FeatureCollection(features)
        print(f"Created FeatureCollection with {len(features)} points from CSV")
        
        return fc
    
    def from_geojson(self, geojson_path, class_property='class'):
        """
        Create FeatureCollection from GeoJSON file
        
        Args:
            geojson_path: Path to GeoJSON file
            class_property: Property name for class labels
            
        Returns:
            ee.FeatureCollection
        """
        with open(geojson_path, 'r') as f:
            geojson_data = json.load(f)
        
        features = []
        for feature_data in geojson_data['features']:
            coords = feature_data['geometry']['coordinates']
            properties = feature_data['properties']
            
            # Ensure class property exists and is integer
            if class_property in properties:
                properties[class_property] = int(properties[class_property])
            
            if feature_data['geometry']['type'] == 'Point':
                geom = ee.Geometry.Point(coords)
            elif feature_data['geometry']['type'] == 'Polygon':
                geom = ee.Geometry.Polygon(coords)
            else:
                print(f"Skipping unsupported geometry type: {feature_data['geometry']['type']}")
                continue
            
            feature = ee.Feature(geom, properties)
            features.append(feature)
        
        fc = ee.FeatureCollection(features)
        print(f"Created FeatureCollection with {len(features)} features from GeoJSON")
        
        return fc
    
    def from_shapefile(self, shapefile_path, class_col='class'):
        """
        Create FeatureCollection from Shapefile
        Requires geopandas
        
        Args:
            shapefile_path: Path to shapefile (.shp)
            class_col: Column name for class labels
            
        Returns:
            ee.FeatureCollection
        """
        try:
            import geopandas as gpd
        except ImportError:
            print("geopandas is required for shapefile support")
            print("Install with: pip install geopandas")
            raise
        
        gdf = gpd.read_file(shapefile_path)
        
        # Convert to EPSG:4326 if needed
        if gdf.crs.to_string() != 'EPSG:4326':
            print(f"Converting from {gdf.crs} to EPSG:4326")
            gdf = gdf.to_crs('EPSG:4326')
        
        features = []
        for idx, row in gdf.iterrows():
            geom = row.geometry
            
            # Create properties dictionary
            properties = {col: row[col] for col in gdf.columns if col != 'geometry'}
            
            # Ensure class is integer
            if class_col in properties:
                properties[class_col] = int(properties[class_col])
            
            # Convert geometry
            if geom.geom_type == 'Point':
                ee_geom = ee.Geometry.Point([geom.x, geom.y])
            elif geom.geom_type == 'Polygon':
                coords = list(geom.exterior.coords)
                ee_geom = ee.Geometry.Polygon(coords)
            else:
                print(f"Skipping unsupported geometry type: {geom.geom_type}")
                continue
            
            feature = ee.Feature(ee_geom, properties)
            features.append(feature)
        
        fc = ee.FeatureCollection(features)
        print(f"Created FeatureCollection with {len(features)} features from Shapefile")
        
        return fc
    
    def split_train_validation(self, feature_collection, train_ratio=0.7, seed=42):
        """
        Split FeatureCollection into training and validation sets
        
        Args:
            feature_collection: ee.FeatureCollection to split
            train_ratio: Proportion for training (0-1)
            seed: Random seed for reproducibility
            
        Returns:
            tuple: (training_fc, validation_fc)
        """
        # Add random column
        fc_with_random = feature_collection.randomColumn('random', seed)
        
        # Split based on random value
        training = fc_with_random.filter(ee.Filter.lt('random', train_ratio))
        validation = fc_with_random.filter(ee.Filter.gte('random', train_ratio))
        
        train_count = training.size().getInfo()
        val_count = validation.size().getInfo()
        
        print(f"Training samples: {train_count}")
        print(f"Validation samples: {val_count}")
        
        return training, validation
    
    def balance_classes(self, feature_collection, class_property='class', 
                       samples_per_class=None, seed=42):
        """
        Balance classes by sampling equal number from each class
        
        Args:
            feature_collection: ee.FeatureCollection to balance
            class_property: Property name for class labels
            samples_per_class: Number of samples per class (None = min class size)
            seed: Random seed
            
        Returns:
            ee.FeatureCollection: Balanced feature collection
        """
        # Get unique classes
        classes = feature_collection.aggregate_array(class_property).distinct()
        
        # Get class counts
        class_counts = {}
        for cls in classes.getInfo():
            count = feature_collection.filter(
                ee.Filter.eq(class_property, cls)
            ).size().getInfo()
            class_counts[cls] = count
            print(f"Class {cls}: {count} samples")
        
        # Determine samples per class
        if samples_per_class is None:
            samples_per_class = min(class_counts.values())
        
        print(f"\nBalancing to {samples_per_class} samples per class...")
        
        # Sample from each class
        balanced_features = []
        for cls in classes.getInfo():
            class_features = feature_collection.filter(
                ee.Filter.eq(class_property, cls)
            )
            
            # Random sample
            sampled = class_features.randomColumn('random', seed).sort('random').limit(samples_per_class)
            balanced_features.append(sampled)
        
        # Merge all classes
        balanced_fc = ee.FeatureCollection(balanced_features).flatten()
        
        total = balanced_fc.size().getInfo()
        print(f"Balanced dataset: {total} total samples")
        
        return balanced_fc
    
    def export_to_asset(self, feature_collection, asset_id, description='export'):
        """
        Export FeatureCollection to Earth Engine Asset
        
        Args:
            feature_collection: ee.FeatureCollection to export
            asset_id: Asset ID (e.g., 'users/username/asset_name')
            description: Task description
            
        Returns:
            ee.batch.Task
        """
        task = ee.batch.Export.table.toAsset(
            collection=feature_collection,
            description=description,
            assetId=asset_id
        )
        
        task.start()
        print(f"Export task started: {description}")
        print(f"Asset ID: {asset_id}")
        print("Check task status at: https://code.earthengine.google.com/tasks")
        
        return task
    
    def validate_data(self, feature_collection, class_property='class', 
                     expected_classes=None):
        """
        Validate training/validation data
        
        Args:
            feature_collection: ee.FeatureCollection to validate
            class_property: Property name for class labels
            expected_classes: List of expected class values (e.g., [0,1,2,3,4,5,6])
            
        Returns:
            dict: Validation results
        """
        print("\n=== Data Validation ===\n")
        
        # Total features
        total = feature_collection.size().getInfo()
        print(f"Total features: {total}")
        
        # Check for null geometries
        null_geom = feature_collection.filter(
            ee.Filter.eq('.geo', None)
        ).size().getInfo()
        print(f"Null geometries: {null_geom}")
        
        # Get unique classes
        classes = feature_collection.aggregate_array(class_property).distinct().sort()
        class_list = classes.getInfo()
        print(f"Unique classes: {class_list}")
        
        # Class distribution
        print("\nClass distribution:")
        class_counts = {}
        for cls in class_list:
            count = feature_collection.filter(
                ee.Filter.eq(class_property, cls)
            ).size().getInfo()
            class_counts[cls] = count
            print(f"  Class {cls}: {count} samples")
        
        # Check for expected classes
        issues = []
        if expected_classes is not None:
            missing = set(expected_classes) - set(class_list)
            extra = set(class_list) - set(expected_classes)
            
            if missing:
                issues.append(f"Missing classes: {missing}")
            if extra:
                issues.append(f"Unexpected classes: {extra}")
        
        # Check for class imbalance
        if class_counts:
            max_count = max(class_counts.values())
            min_count = min(class_counts.values())
            imbalance_ratio = max_count / min_count if min_count > 0 else float('inf')
            
            if imbalance_ratio > 3:
                issues.append(f"Class imbalance detected (ratio: {imbalance_ratio:.2f})")
                print(f"\n⚠ Warning: Class imbalance ratio: {imbalance_ratio:.2f}")
                print("Consider using balance_classes() method")
        
        # Check for insufficient samples
        if total < 50:
            issues.append("Very few samples - consider collecting more data")
        
        # Summary
        print("\n" + "="*40)
        if issues:
            print("⚠ Issues found:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("✓ Data validation passed")
        print("="*40 + "\n")
        
        return {
            'total_features': total,
            'null_geometries': null_geom,
            'classes': class_list,
            'class_counts': class_counts,
            'issues': issues
        }


def example_prepare_from_csv():
    """Example: Prepare training data from CSV"""
    prep = TrainingDataPreparation()
    
    # Load from CSV
    training_fc = prep.from_csv(
        'training_points.csv',
        lon_col='longitude',
        lat_col='latitude',
        class_col='species_class'
    )
    
    # Validate
    prep.validate_data(training_fc, class_property='species_class', 
                      expected_classes=[0,1,2,3,4,5,6])
    
    # Balance classes
    balanced_fc = prep.balance_classes(training_fc, class_property='species_class')
    
    # Split train/validation
    train_fc, val_fc = prep.split_train_validation(balanced_fc, train_ratio=0.7)
    
    # Export to assets
    prep.export_to_asset(train_fc, 'users/YOUR_USERNAME/training_points', 
                        'training_export')
    prep.export_to_asset(val_fc, 'users/YOUR_USERNAME/validation_points',
                        'validation_export')
    
    return train_fc, val_fc


def example_prepare_from_shapefile():
    """Example: Prepare training data from Shapefile"""
    prep = TrainingDataPreparation()
    
    # Load from shapefile
    training_fc = prep.from_shapefile(
        'field_data/training_points.shp',
        class_col='tree_class'
    )
    
    # Validate and process
    prep.validate_data(training_fc, class_property='tree_class')
    
    return training_fc


def create_sample_csv_template(output_path='training_template.csv'):
    """
    Create a CSV template for training data
    
    Args:
        output_path: Path to save template CSV
    """
    # Sample data structure
    data = {
        'longitude': [-122.5, -122.4, -122.3, -122.2],
        'latitude': [37.5, 37.6, 37.7, 37.8],
        'class': [0, 1, 2, 0],
        'species_name': ['Oak', 'Pine', 'Spruce', 'Oak'],
        'confidence': ['high', 'high', 'medium', 'high'],
        'collection_date': ['2019-06-15', '2019-06-15', '2019-06-16', '2019-06-16'],
        'notes': ['Dense canopy', 'Young stand', 'Mixed age', 'Old growth']
    }
    
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    
    print(f"Template CSV created: {output_path}")
    print("\nRequired columns:")
    print("  - longitude: Decimal degrees")
    print("  - latitude: Decimal degrees")
    print("  - class: Integer class label (0-6 for 7 classes)")
    print("\nOptional columns:")
    print("  - species_name: Human-readable species name")
    print("  - confidence: Data quality indicator")
    print("  - collection_date: When data was collected")
    print("  - notes: Additional information")


if __name__ == "__main__":
    print("="*60)
    print("Training Data Preparation Utilities")
    print("="*60 + "\n")
    
    # Create template CSV
    # create_sample_csv_template('training_template.csv')
    
    # Example usage:
    # 1. From CSV
    # train_fc, val_fc = example_prepare_from_csv()
    
    # 2. From Shapefile
    # training_fc = example_prepare_from_shapefile()
    
    print("To use these utilities:")
    print("1. Uncomment the example function calls above")
    print("2. Replace paths with your actual data files")
    print("3. Update class column names to match your data")
    print("4. Replace 'YOUR_USERNAME' with your Earth Engine username")
