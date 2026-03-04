# Quick Start Guide

## Setup (5 minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Authenticate Google Earth Engine
```bash
earthengine authenticate
```
Follow the browser prompts to authenticate with your Google account.

### 3. Prepare Your Data

You need three datasets:

#### A. Training Points
Create a CSV file with your field observations:
```csv
longitude,latitude,class,species_name
-122.5,37.5,0,Oak
-122.4,37.6,1,Pine
-122.3,37.7,2,Spruce
```

#### B. Validation Points  
Similar format to training points (separate locations)

#### C. Forest Zones (optional)
Polygons defining natural vs plantation forests

## Running the Classification (3 steps)

### Step 1: Prepare Training Data

```python
from prepare_training_data import TrainingDataPreparation
import ee

ee.Initialize()
prep = TrainingDataPreparation()

# Load your CSV
training_fc = prep.from_csv(
    'your_training_points.csv',
    lon_col='longitude',
    lat_col='latitude',
    class_col='class'
)

# Validate the data
prep.validate_data(training_fc, class_property='class', 
                  expected_classes=[0,1,2,3,4,5,6])

# Balance classes (optional but recommended)
balanced_fc = prep.balance_classes(training_fc, class_property='class')

# Split train/validation
train_fc, val_fc = prep.split_train_validation(balanced_fc, train_ratio=0.7)

# Upload to Earth Engine
prep.export_to_asset(train_fc, 'users/YOUR_USERNAME/training', 'training')
prep.export_to_asset(val_fc, 'users/YOUR_USERNAME/validation', 'validation')
```

Wait for the export tasks to complete (check at https://code.earthengine.google.com/tasks)

### Step 2: Run Classification

```python
from tree_species_classification import main
import ee

ee.Initialize()

# Define your study area
aoi = ee.Geometry.Rectangle([
    10.0, 48.0,   # lon_min, lat_min
    10.5, 48.5    # lon_max, lat_max
])

# Load your data from assets
training = ee.FeatureCollection('users/YOUR_USERNAME/training')
validation = ee.FeatureCollection('users/YOUR_USERNAME/validation')

# Create simple forest zones (or load from asset)
forest_zones = ee.FeatureCollection([
    ee.Feature(aoi, {'type': 'natural'})
])

# Run the pipeline
results = main(
    aoi=aoi,
    training_points=training,
    validation_points=validation,
    forest_zones=forest_zones,
    export_path='my_classification'
)

print(f"Overall Accuracy: {results['accuracy_metrics']['overall_accuracy'].getInfo():.4f}")
print(f"Kappa: {results['accuracy_metrics']['kappa'].getInfo():.4f}")
```

This will:
- Process Sentinel-1 and Sentinel-2 imagery
- Extract ~100+ features per pixel
- Train Random Forest classifier
- Generate classified map
- Compute accuracy metrics
- Export results to Google Drive

### Step 3: Analyze Results

After exports complete, analyze your results:

```python
from analyze_results import ResultsAnalyzer
import ee

ee.Initialize()

# Load results
classified = ee.Image('users/YOUR_USERNAME/my_classification')
validation = ee.FeatureCollection('users/YOUR_USERNAME/validation')

class_names = ['Oak', 'Pine', 'Spruce', 'Beech', 'Birch', 'Fir', 'Mixed']

analyzer = ResultsAnalyzer(classified, validation, class_names)

# Compute metrics
confusion = analyzer.compute_confusion_matrix(classifier)
analyzer.print_accuracy_report(confusion)

area_stats = analyzer.compute_area_statistics(scale=10)
analyzer.print_area_report(area_stats)

# Export to CSV
analyzer.export_results_to_csv(confusion, area_stats, output_dir='results')
```

## Testing Without Real Data

Test the pipeline with sample data:

```python
from example_usage import example_with_sample_data

# This creates random training data for testing
results = example_with_sample_data()
```

**Warning:** Results will not be meaningful with random data!

## Common Issues

### "User memory limit exceeded"
- Reduce study area size
- Increase CONFIG['scale'] to 20 meters
- Process in tiles

### "No images found"
- Check date ranges match your region's data availability
- Adjust cloud cover threshold

### Low accuracy (< 70%)
- Collect more training samples (aim for 100+ per class)
- Balance classes
- Verify training data quality
- Check for geographic/temporal mismatch

## Next Steps

1. **Customize class definitions**: Edit class_names for your tree species
2. **Adjust seasons**: Modify CONFIG['seasons'] for your region's phenology  
3. **Tune parameters**: Experiment with CONFIG['n_trees'], feature selection
4. **Visualize**: Use output maps in QGIS or ArcGIS

## File Structure

```
.
├── tree_species_classification.py   # Main pipeline
├── prepare_training_data.py          # Data preparation
├── example_usage.py                  # Usage examples
├── analyze_results.py                # Results analysis
├── requirements.txt                  # Dependencies
├── README.md                         # Full documentation
└── QUICKSTART.md                     # This file
```

## Support

See [README.md](README.md) for detailed documentation.
