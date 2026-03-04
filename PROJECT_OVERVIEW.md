# Tree Species Classification Project

## Project Overview

This project implements a comprehensive tree species classification pipeline using multi-seasonal satellite imagery in Google Earth Engine. Based on state-of-the-art remote sensing methods, it combines optical (Sentinel-2) and radar (Sentinel-1) data with terrain features to achieve accurate classification at 10-meter resolution.

## Key Features

✅ **Multi-seasonal analysis** - Captures phenological patterns across 4 seasons  
✅ **Multiple data sources** - Sentinel-1 SAR + Sentinel-2 optical + DEM  
✅ **Rich feature set** - 100+ features including spectral indices, texture, radar indices  
✅ **Machine learning** - Random Forest classifier with 71 trees  
✅ **Temporal analysis** - Gradient features capture vegetation dynamics  
✅ **Comprehensive accuracy** - Confusion matrix, kappa, per-class metrics  
✅ **Zonal statistics** - Compare natural vs plantation forests  
✅ **Cloud-based** - Runs on Google Earth Engine (no local processing)  

## Scientific Background

The methodology implements techniques from recent forest remote sensing research:

- **Spectral Indices**: NDVI, EVI, GNDVI, MTCI, REIP, IRECI - capture vegetation health and chlorophyll content
- **Texture Features**: GLCM-based texture from NIR band - captures canopy structure
- **Radar Indices**: VH/VV ratios and backscatter - sensitive to structure and moisture
- **Temporal Gradients**: EVI and VH changes between seasons - capture phenology
- **Percentile Composites**: 20th and 80th percentiles - reduce noise and outliers
- **Terrain Features**: Slope and aspect - control species distribution

## Workflow

```
1. Data Acquisition
   ├─ Sentinel-2 SR (optical)
   ├─ Sentinel-1 GRD (radar)
   └─ SRTM DEM (elevation)
   
2. Preprocessing
   ├─ Cloud masking (Sentinel-2)
   ├─ Radiometric calibration
   └─ Temporal filtering
   
3. Feature Extraction
   ├─ Spectral indices (9 indices)
   ├─ GLCM texture (8 features)
   ├─ Radar indices (4 indices)
   ├─ Temporal gradients
   ├─ Percentile composites (20th, 80th)
   └─ Terrain features (slope, aspect)
   
4. Classification
   ├─ Feature stack creation
   ├─ Training data sampling
   ├─ Random Forest training (71 trees)
   └─ Image classification
   
5. Validation & Analysis
   ├─ Confusion matrix
   ├─ Accuracy metrics (OA, Kappa, PA, UA)
   ├─ Area statistics
   └─ Forest type comparison
```

## Technical Specifications

| Parameter | Value | Notes |
|-----------|-------|-------|
| Spatial Resolution | 10m | From Sentinel-2 bands |
| Temporal Coverage | 4 seasons | Spring, Summer, Autumn, Winter |
| Feature Count | ~100+ | Varies by data availability |
| Classification Algorithm | Random Forest | 71 trees, sqrt(features) per split |
| Number of Classes | 7 | Configurable |
| Processing Platform | Google Earth Engine | Cloud-based |
| Output Format | GeoTIFF | Compatible with GIS software |

## Data Requirements

### Minimum Requirements
- **Training samples**: 50+ per class (350 total for 7 classes)
- **Validation samples**: 20+ per class (140 total)
- **Study area**: < 1000 km² (for reasonable processing time)
- **Time period**: One year with clear seasonal differences

### Recommended
- **Training samples**: 100+ per class (700 total)
- **Validation samples**: 50+ per class (350 total)
- **Well-distributed**: Spatially distributed across study area
- **High quality**: Field-verified species labels
- **Balanced**: Equal samples per class

## Performance

### Processing Time (approximate)
- Small area (< 100 km²): 10-20 minutes
- Medium area (100-500 km²): 20-40 minutes
- Large area (500-1000 km²): 40-90 minutes

*Note: Actual time depends on data availability and server load*

### Expected Accuracy
Based on similar studies:
- **Overall Accuracy**: 75-90%
- **Kappa Coefficient**: 0.70-0.85

Accuracy depends on:
- Training data quality and quantity
- Class separability (some species are more similar)
- Study area characteristics
- Image quality and cloud cover

## Limitations

1. **Cloud cover**: Requires relatively cloud-free imagery
2. **Seasonal data**: Needs data from all four seasons
3. **Species similarity**: Cannot always distinguish very similar species
4. **Mixed pixels**: 10m resolution may mix multiple species
5. **Processing limits**: GEE memory limits for very large areas
6. **Training data**: Requires field-collected ground truth

## Use Cases

### Forest Management
- Inventory tree species distribution
- Monitor plantation composition
- Track species changes over time

### Conservation
- Identify rare or invasive species
- Map priority conservation areas
- Assess biodiversity patterns

### Research
- Study species-environment relationships
- Analyze forest succession
- Model ecosystem services

### Policy & Planning
- Support forest policy decisions
- Plan sustainable management
- Assess carbon stocks by species

## Customization Options

### Modify Seasons
```python
CONFIG['seasons'] = {
    'spring': {'start': '2019-03-01', 'end': '2019-04-30'},
    'summer': {'start': '2019-06-01', 'end': '2019-07-31'},
    # ... customize for your region
}
```

### Change Resolution
```python
CONFIG['scale'] = 20  # Use 20m for faster processing
```

### Adjust Classifier
```python
CONFIG['n_trees'] = 100  # More trees = better accuracy but slower
```

### Select Features
Modify `build_feature_stack()` to include/exclude specific features

## Outputs

### 1. Classified Map
- **Format**: GeoTIFF
- **Resolution**: 10m
- **Values**: 0-6 (class IDs)
- **Projection**: EPSG:4326 (WGS84)

### 2. Accuracy Assessment
- Confusion matrix (class x class)
- Overall Accuracy (%)
- Kappa coefficient
- Producer's Accuracy per class
- User's Accuracy per class
- F1-Score per class

### 3. Area Statistics
- Pixel count per class
- Area in hectares per class
- Area in km² per class
- Percentage coverage per class

### 4. Zonal Statistics
- Class distribution in natural forests
- Class distribution in plantation forests
- Comparative analysis

## Citation

If you use this code in your research, please cite:

```
[Citation for the paper from forests-12-00565-v2.pdf]
```

## License

This project is provided for research and educational purposes.

## Contributing

Contributions are welcome! Areas for improvement:
- Additional spectral indices
- Alternative classifiers (SVM, Neural Networks)
- Feature selection algorithms
- Multi-year analysis
- Change detection capabilities

## Version History

- **v1.0** (2024) - Initial implementation
  - Multi-seasonal Sentinel-1/2 processing
  - 9 spectral indices + GLCM texture
  - Random Forest classification
  - Comprehensive accuracy assessment

## Contact & Support

For questions, issues, or contributions:
- Open an issue on the repository
- Check README.md for detailed documentation
- See QUICKSTART.md for quick setup guide

---

**Built with Google Earth Engine Python API**
