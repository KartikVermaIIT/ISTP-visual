# Tree Species Classification Pipeline

Multi-seasonal tree species classification using Sentinel-1 SAR and Sentinel-2 optical imagery in Google Earth Engine.

## Overview

This pipeline implements an advanced remote sensing workflow for classifying tree species at 10m resolution using:
- **Multi-seasonal imagery** (Spring, Summer, Autumn, Winter 2019)
- **Sentinel-2** optical bands and spectral indices
- **Sentinel-1** SAR backscatter and radar indices
- **GLCM texture** features from NIR band
- **Temporal gradients** for phenology
- **DEM-derived terrain** features (slope and aspect)
- **Random Forest** classifier (71 trees)

## Features Computed

### Spectral Indices (Sentinel-2)
1. **NDVI** - Normalized Difference Vegetation Index
2. **EVI** - Enhanced Vegetation Index
3. **IPVI** - Infrared Percentage Vegetation Index
4. **TNDVI** - Transformed NDVI
5. **GNDVI** - Green NDVI
6. **BI2** - Brightness Index 2
7. **MTCI** - MERIS Terrestrial Chlorophyll Index
8. **REIP** - Red Edge Inflection Point
9. **IRECI** - Inverted Red-Edge Chlorophyll Index

### Texture Features (GLCM from NIR)
- Angular Second Moment (Energy)
- Contrast
- Correlation
- Variance
- Inverse Difference Moment (Homogeneity)
- Sum Average
- Entropy
- Dissimilarity

### Radar Indices (Sentinel-1)
1. **VH/VV Ratio** - Cross-pol to co-pol ratio
2. **VH - VV Difference** - Polarization difference
3. **Amplitude** - Average backscatter intensity
4. **Normalized Difference** - (VV-VH)/(VV+VH)

### Temporal Features
- **EVI Gradients** - Between consecutive seasons
- **VH Gradients** - SAR temporal changes
- **20th and 80th Percentiles** - For all features

### Terrain Features
- **Slope** - From SRTM DEM
- **Aspect** - Categorized into 8 directions with one-hot encoding (N, NE, E, SE, S, SW, W, NW)

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Authenticate Google Earth Engine

First time setup:
```bash
earthengine authenticate
```

In Python:
```python
import ee
ee.Authenticate()
ee.Initialize()
```

## Usage

### Basic Usage

```python
import ee
from tree_species_classification import main

# Initialize Earth Engine
ee.Initialize()

# Define your area of interest
aoi = ee.Geometry.Rectangle([
    lon_min, lat_min, 
    lon_max, lat_max
])

# Load your training and validation data
training_points = ee.FeatureCollection('users/your_username/training_points')
validation_points = ee.FeatureCollection('users/your_username/validation_points')
forest_zones = ee.FeatureCollection('users/your_username/forest_zones')

# Run the full pipeline
results = main(
    aoi=aoi,
    training_points=training_points,
    validation_points=validation_points,
    forest_zones=forest_zones,
    export_path='tree_species_2019'
)

# Access results
print(f"Overall Accuracy: {results['accuracy_metrics']['overall_accuracy'].getInfo()}")
print(f"Kappa: {results['accuracy_metrics']['kappa'].getInfo()}")
```

### Input Data Requirements

#### Training and Validation Points
- **Format**: Earth Engine FeatureCollection
- **Required Property**: `class` (integer 0-6 for 7 classes)
- **Geometry**: Point geometries
- **Example structure**:
  ```javascript
  // In Earth Engine Code Editor
  var trainingPoints = ee.FeatureCollection([
    ee.Feature(ee.Geometry.Point([lon, lat]), {class: 0}),  // Class 0: Oak
    ee.Feature(ee.Geometry.Point([lon, lat]), {class: 1}),  // Class 1: Pine
    // ... more points
  ]);
  ```

#### Forest Zones (for area statistics)
- **Format**: Earth Engine FeatureCollection
- **Required Property**: `type` (string: 'natural' or 'plantation')
- **Geometry**: Polygon geometries

### Creating Training Data

You can create training points in several ways:

#### Option 1: Earth Engine Code Editor
```javascript
// Draw points on the map and assign class values
var trainingPoints = oakPoints.merge(pinePoints).merge(sprucePoints)
  .map(function(f) {
    return f.set('class', f.get('species_code'));
  });

// Export to Asset
Export.table.toAsset({
  collection: trainingPoints,
  description: 'training_points',
  assetId: 'users/your_username/training_points'
});
```

#### Option 2: From Shapefile
```python
import ee
import geopandas as gpd

# Load shapefile
gdf = gpd.read_file('training_points.shp')

# Convert to Earth Engine FeatureCollection
features = []
for idx, row in gdf.iterrows():
    coords = [row.geometry.x, row.geometry.y]
    feature = ee.Feature(
        ee.Geometry.Point(coords),
        {'class': int(row['class'])}
    )
    features.append(feature)

training_fc = ee.FeatureCollection(features)
```

## Output

The pipeline generates three main outputs exported to Google Drive:

### 1. Classified Image
- **Filename**: `{export_path}_classified_10m.tif`
- **Resolution**: 10 meters
- **Values**: 0-6 (representing tree species classes)
- **Format**: GeoTIFF

### 2. Accuracy Metrics
- **Filename**: `{export_path}_accuracy_metrics.csv`
- **Contents**: 
  - Overall Accuracy
  - Kappa Coefficient
  - Confusion Matrix
  - Producer's Accuracy (per class)
  - Consumer's Accuracy (per class)

### 3. Area Statistics
- **Filename**: `{export_path}_area_statistics.csv`
- **Contents**:
  - Area per class within each forest zone
  - Natural vs Plantation forest breakdown

## Configuration

Modify the `CONFIG` dictionary in the script to adjust parameters:

```python
CONFIG = {
    'year': 2019,                    # Year of analysis
    'seasons': {...},                 # Seasonal date ranges
    'scale': 10,                      # Output resolution (meters)
    'n_trees': 71,                    # Random Forest trees
    'n_classes': 7,                   # Number of tree species
    'percentiles': [20, 80]           # Percentile composites
}
```

## Advanced Usage

### Custom Feature Extraction

```python
from tree_species_classification import SentinelProcessor, build_feature_stack

# Build feature stack only
feature_image, feature_bands = build_feature_stack(
    aoi=aoi,
    seasons=CONFIG['seasons']
)

print(f"Total features: {len(feature_bands)}")
print(f"Feature names: {feature_bands[:10]}...")  # First 10 features
```

### Custom Classification

```python
from tree_species_classification import TreeSpeciesClassifier

# Initialize classifier with custom parameters
classifier = TreeSpeciesClassifier(n_trees=100, n_classes=7)

# Train and classify
training_data = classifier.prepare_training_data(feature_image, training_points)
classifier.train(training_data, feature_bands)
classified = classifier.classify(feature_image)
```

### Zonal Analysis Only

```python
from tree_species_classification import ZonalStatistics

# Compute area statistics for existing classification
zonal_stats = ZonalStatistics(classified_image, scale=10)
area_stats = zonal_stats.compute_area_statistics(forest_zones)

# Convert to pandas DataFrame (after exporting)
import pandas as pd
stats_info = area_stats.getInfo()
df = pd.DataFrame(stats_info['features'])
```

## Class Definitions

Define your tree species classes based on your study area. Example:

| Class | Species | Description |
|-------|---------|-------------|
| 0 | Oak | Deciduous broadleaf |
| 1 | Pine | Evergreen conifer |
| 2 | Spruce | Evergreen conifer |
| 3 | Beech | Deciduous broadleaf |
| 4 | Birch | Deciduous broadleaf |
| 5 | Fir | Evergreen conifer |
| 6 | Mixed | Mixed species |

## Performance Considerations

### Processing Time
- Feature extraction: ~10-30 minutes depending on AOI size
- Classification: ~5-15 minutes
- Export: Varies by area (handled by GEE servers)

### Memory Optimization
- Use `tileScale` parameter for large areas
- Process in smaller chunks if needed
- Adjust `maxPixels` in export functions

### Best Practices
1. **Start small**: Test on a small AOI first
2. **Cloud filtering**: Adjust cloud threshold (currently 20%)
3. **Temporal window**: Adjust seasonal date ranges for your region
4. **Training data**: Use at least 50-100 samples per class
5. **Validation split**: 70/30 train/validation is typical

## Troubleshooting

### Common Issues

**Error: "User memory limit exceeded"**
- Increase `tileScale` parameter (try 8 or 16)
- Reduce AOI size
- Use fewer features

**Error: "No features in collection"**
- Check date ranges for your region
- Adjust cloud cover threshold
- Verify Sentinel data availability

**Low accuracy**
- Collect more training samples
- Balance classes (equal samples per class)
- Check for mislabeled training data
- Adjust seasonal date ranges

## Citation

If you use this code, please cite the original paper:

```
[Include paper citation from forests-12-00565-v2.pdf]
```

## License

This implementation is provided as-is for research and educational purposes.

## Contact

For questions or issues, please open an issue on the repository.

## Acknowledgments

- Sentinel-1 and Sentinel-2 data: ESA Copernicus Programme
- SRTM DEM: NASA/USGS
- Google Earth Engine platform
