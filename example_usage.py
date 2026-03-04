"""
Example usage of the tree species classification pipeline
This script demonstrates how to run the full classification workflow
"""

import ee
from tree_species_classification import main, CONFIG

# Note: Earth Engine should be initialized before running examples
# Uncomment the following to initialize:
# try:
#     ee.Initialize()
#     print("Earth Engine initialized successfully!")
# except Exception as e:
#     print(f"Error initializing Earth Engine: {e}")
#     print("Please run: earthengine authenticate")
#     exit(1)


def example_basic_classification():
    """
    Example 1: Basic classification workflow
    Replace with your actual data paths
    """
    print("\n=== Example 1: Basic Classification ===\n")
    
    # Define area of interest (example coordinates - replace with yours)
    # This example uses a region in central Europe
    aoi = ee.Geometry.Rectangle([
        10.0, 48.0,  # [lon_min, lat_min]
        10.5, 48.5   # [lon_max, lat_max]
    ])
    
    # Load your training and validation data
    # Option 1: From Earth Engine Assets
    training_points = ee.FeatureCollection('users/YOUR_USERNAME/training_points')
    validation_points = ee.FeatureCollection('users/YOUR_USERNAME/validation_points')
    forest_zones = ee.FeatureCollection('users/YOUR_USERNAME/forest_zones')
    
    # Option 2: Create sample data programmatically (for testing)
    # training_points = create_sample_training_data(aoi)
    # validation_points = create_sample_validation_data(aoi)
    # forest_zones = create_sample_forest_zones(aoi)
    
    # Run the classification pipeline
    results = main(
        aoi=aoi,
        training_points=training_points,
        validation_points=validation_points,
        forest_zones=forest_zones,
        export_path='tree_species_example'
    )
    
    print("\n=== Classification Complete ===")
    print(f"Check your Google Drive 'GEE_Exports' folder for results")
    
    return results


def example_custom_configuration():
    """
    Example 2: Classification with custom configuration
    """
    print("\n=== Example 2: Custom Configuration ===\n")
    
    # Modify configuration
    CONFIG['n_trees'] = 100  # Use more trees
    CONFIG['scale'] = 20     # Lower resolution for faster processing
    
    # Define smaller test area
    aoi = ee.Geometry.Rectangle([10.0, 48.0, 10.2, 48.2])
    
    # Load data
    training_points = ee.FeatureCollection('users/YOUR_USERNAME/training_points')
    validation_points = ee.FeatureCollection('users/YOUR_USERNAME/validation_points')
    forest_zones = ee.FeatureCollection('users/YOUR_USERNAME/forest_zones')
    
    # Run pipeline
    results = main(
        aoi=aoi,
        training_points=training_points,
        validation_points=validation_points,
        forest_zones=forest_zones,
        export_path='tree_species_custom'
    )
    
    return results


def create_sample_training_data(aoi, n_samples_per_class=10):
    """
    Create sample training data for testing
    WARNING: This is random data for testing only!
    Use real field data for actual classification.
    """
    import random
    
    print("Creating sample training data...")
    
    bounds = aoi.bounds().coordinates().getInfo()[0]
    lon_min, lat_min = bounds[0]
    lon_max, lat_max = bounds[2]
    
    features = []
    for class_id in range(CONFIG['n_classes']):
        for _ in range(n_samples_per_class):
            lon = random.uniform(lon_min, lon_max)
            lat = random.uniform(lat_min, lat_max)
            
            feature = ee.Feature(
                ee.Geometry.Point([lon, lat]),
                {'class': class_id}
            )
            features.append(feature)
    
    training_fc = ee.FeatureCollection(features)
    print(f"Created {len(features)} sample training points")
    
    return training_fc


def create_sample_validation_data(aoi, n_samples_per_class=5):
    """
    Create sample validation data for testing
    WARNING: This is random data for testing only!
    """
    import random
    
    print("Creating sample validation data...")
    
    bounds = aoi.bounds().coordinates().getInfo()[0]
    lon_min, lat_min = bounds[0]
    lon_max, lat_max = bounds[2]
    
    features = []
    for class_id in range(CONFIG['n_classes']):
        for _ in range(n_samples_per_class):
            lon = random.uniform(lon_min, lon_max)
            lat = random.uniform(lat_min, lat_max)
            
            feature = ee.Feature(
                ee.Geometry.Point([lon, lat]),
                {'class': class_id}
            )
            features.append(feature)
    
    validation_fc = ee.FeatureCollection(features)
    print(f"Created {len(features)} sample validation points")
    
    return validation_fc


def create_sample_forest_zones(aoi):
    """
    Create sample forest zones for testing
    """
    print("Creating sample forest zones...")
    
    bounds = aoi.bounds().coordinates().getInfo()[0]
    lon_min, lat_min = bounds[0]
    lon_max, lat_max = bounds[2]
    
    # Create two zones: natural and plantation
    mid_lon = (lon_min + lon_max) / 2
    
    natural_zone = ee.Feature(
        ee.Geometry.Rectangle([lon_min, lat_min, mid_lon, lat_max]),
        {'type': 'natural'}
    )
    
    plantation_zone = ee.Feature(
        ee.Geometry.Rectangle([mid_lon, lat_min, lon_max, lat_max]),
        {'type': 'plantation'}
    )
    
    zones_fc = ee.FeatureCollection([natural_zone, plantation_zone])
    print("Created 2 sample forest zones")
    
    return zones_fc


def example_with_sample_data():
    """
    Example 3: Quick test with generated sample data
    WARNING: This uses random points for testing only!
    Results will not be meaningful.
    """
    print("\n=== Example 3: Testing with Sample Data ===\n")
    print("WARNING: Using randomly generated training data")
    print("This is for testing the pipeline only - results will not be accurate!\n")
    
    # Small test area
    aoi = ee.Geometry.Rectangle([10.0, 48.0, 10.1, 48.1])
    
    # Create sample data
    training_points = create_sample_training_data(aoi, n_samples_per_class=20)
    validation_points = create_sample_validation_data(aoi, n_samples_per_class=10)
    forest_zones = create_sample_forest_zones(aoi)
    
    # Run pipeline with lower resolution for speed
    CONFIG['scale'] = 20
    
    results = main(
        aoi=aoi,
        training_points=training_points,
        validation_points=validation_points,
        forest_zones=forest_zones,
        export_path='tree_species_test'
    )
    
    return results


def visualize_results(classified_image, aoi):
    """
    Example 4: Visualize results in Earth Engine Code Editor
    Prints JavaScript code to paste into Code Editor
    """
    print("\n=== Visualization Code for Earth Engine Code Editor ===\n")
    
    # Get the image ID (if it's been exported to an asset)
    # For immediate visualization, you'd need to run this in a Jupyter notebook
    # with geemap or use the Code Editor
    
    js_code = f"""
// Paste this in Earth Engine Code Editor

// Define area of interest
var aoi = ee.Geometry.Rectangle([
    {aoi.bounds().coordinates().getInfo()[0][0][0]},
    {aoi.bounds().coordinates().getInfo()[0][0][1]},
    {aoi.bounds().coordinates().getInfo()[0][2][0]},
    {aoi.bounds().coordinates().getInfo()[0][2][1]}
]);

// Load classified image (replace with your exported asset)
var classified = ee.Image('users/YOUR_USERNAME/tree_species_classified');

// Define visualization parameters
var classVis = {{
    min: 0,
    max: 6,
    palette: [
        '#1f77b4',  // Class 0 - Blue
        '#ff7f0e',  // Class 1 - Orange
        '#2ca02c',  // Class 2 - Green
        '#d62728',  // Class 3 - Red
        '#9467bd',  // Class 4 - Purple
        '#8c564b',  // Class 5 - Brown
        '#e377c2'   // Class 6 - Pink
    ]
}};

// Add layers to map
Map.centerObject(aoi, 12);
Map.addLayer(classified, classVis, 'Tree Species Classification');
Map.addLayer(aoi, {{color: 'white'}}, 'Area of Interest', false);

// Add legend
var legend = ui.Panel({{
    style: {{
        position: 'bottom-left',
        padding: '8px 15px'
    }}
}});

var legendTitle = ui.Label({{
    value: 'Tree Species Classes',
    style: {{fontWeight: 'bold', fontSize: '16px'}}
}});
legend.add(legendTitle);

var classes = [
    'Class 0: Oak',
    'Class 1: Pine', 
    'Class 2: Spruce',
    'Class 3: Beech',
    'Class 4: Birch',
    'Class 5: Fir',
    'Class 6: Mixed'
];

var colors = classVis.palette;

for (var i = 0; i < classes.length; i++) {{
    var colorBox = ui.Label({{
        style: {{
            backgroundColor: colors[i],
            padding: '8px',
            margin: '0 0 4px 0'
        }}
    }});
    
    var description = ui.Label({{
        value: classes[i],
        style: {{margin: '0 0 4px 6px'}}
    }});
    
    var panel = ui.Panel({{
        widgets: [colorBox, description],
        layout: ui.Panel.Layout.Flow('horizontal')
    }});
    
    legend.add(panel);
}}

Map.add(legend);

print('Classification loaded successfully');
"""
    
    print(js_code)
    print("\n" + "="*50)


if __name__ == "__main__":
    print("="*60)
    print("Tree Species Classification - Example Usage")
    print("="*60)
    
    # Choose which example to run:
    
    # Example 1: Basic classification (requires real data)
    # results = example_basic_classification()
    
    # Example 2: Custom configuration (requires real data)
    # results = example_custom_configuration()
    
    # Example 3: Test with sample data (for testing pipeline only)
    # results = example_with_sample_data()
    
    # Example 4: Generate visualization code
    # aoi = ee.Geometry.Rectangle([10.0, 48.0, 10.5, 48.5])
    # visualize_results(None, aoi)
    
    print("\nTo run an example:")
    print("1. Uncomment one of the example function calls above")
    print("2. Replace 'YOUR_USERNAME' with your Earth Engine username")
    print("3. Update AOI coordinates for your study area")
    print("4. Ensure you have training/validation data uploaded")
    print("\nFor testing: Use example_with_sample_data() (generates random data)")
    print("For production: Use example_basic_classification() with real field data")
