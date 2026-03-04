# 🌲 Tree Species Classification - Streamlit UI Guide

## Quick Start

### 1. Install Dependencies
```bash
pip install streamlit plotly
```

### 2. Launch the Web UI
```bash
streamlit run streamlit_app.py
```

Or simply double-click `run_streamlit.bat` on Windows.

### 3. Access the Application
The app will automatically open in your browser at: `http://localhost:8501`

---

## Features Overview

### 🏠 Home Page
- **System Overview**: View data sources, features, and performance metrics
- **Quick Start Guide**: Step-by-step instructions for setup, data preparation, and classification
- **System Architecture**: Understanding the processing pipeline

### ⚙️ Configuration
- **Study Area Settings**: Define your region and timeframe
- **Seasonal Dates**: Customize dates for Spring, Summer, Autumn, Winter
- **Classification Parameters**: Adjust Random Forest settings, resolution, and features
- **Export Options**: Choose output format and scale
- **Save/Load**: Manage configuration profiles

### 📊 Results Dashboard
- **Accuracy Metrics**: Overall accuracy, Kappa coefficient, per-class statistics
- **Confusion Matrix**: Interactive heatmap showing classification performance
- **Performance Summary**: Quick view of best and worst performing classes
- **Download Results**: Export confusion matrix and accuracy reports

### 📈 Analysis
- **Area Statistics**: Pie charts and bar plots showing species distribution
- **Feature Importance**: Top contributing features in classification
- **Forest Type Comparison**: Natural vs. plantation analysis
- **Temporal Trends**: Multi-year analysis (upcoming feature)

### 🗺️ Visualization
- **Color Scheme Editor**: Customize map colors for each species
- **Earth Engine Code**: Ready-to-use JavaScript for Code Editor
- **Interactive Maps**: View classification results (requires actual data)
- **Layer Controls**: Toggle different map layers

### 📚 Documentation
- **User Guide**: Complete instructions for using the system
- **Methods**: Scientific methodology and algorithms
- **FAQ**: Common questions and troubleshooting
- **Resources**: Links to documentation and external resources

---

## Usage Workflow

### Step 1: Configure Your Study
1. Go to **⚙️ Configuration** page
2. Set your study area coordinates
3. Adjust seasonal date ranges for your region
4. Select features to include
5. Save configuration

### Step 2: Prepare Training Data
1. Collect field samples with GPS coordinates
2. Create CSV with columns: `longitude`, `latitude`, `class`
3. Download template from **🏠 Home** page
4. Upload to Earth Engine as FeatureCollection

### Step 3: Run Classification
```python
from tree_species_classification import main
import ee

ee.Initialize()

aoi = ee.Geometry.Rectangle([lon_min, lat_min, lon_max, lat_max])
training = ee.FeatureCollection('users/YOUR_USERNAME/training')
validation = ee.FeatureCollection('users/YOUR_USERNAME/validation')
zones = ee.FeatureCollection('users/YOUR_USERNAME/zones')

results = main(aoi, training, validation, zones, 'my_classification')
```

### Step 4: View Results
1. Go to **📊 Results Dashboard**
2. Review accuracy metrics and confusion matrix
3. Identify areas for improvement
4. Download reports

### Step 5: Analyze and Visualize
1. **📈 Analysis** page: View area statistics and feature importance
2. **🗺️ Visualization** page: Create maps using Earth Engine Code Editor
3. Export visualizations and statistics

---

## Tips for Best Results

### Data Preparation
- ✅ Collect 100+ samples per class
- ✅ Balance classes (equal samples each)
- ✅ Verify species labels in the field
- ✅ Distribute samples across study area
- ✅ Split into 70% training, 30% validation

### Configuration
- ✅ Match seasonal dates to local phenology
- ✅ Use all 4 seasons if possible
- ✅ Keep resolution at 10m for best accuracy
- ✅ Enable all feature groups initially
- ✅ Use 71 trees (optimal from research)

### Improving Accuracy
- 📈 Add more training samples
- 📈 Remove misclassified samples
- 📈 Adjust seasonal date ranges
- 📈 Include additional features
- 📈 Use stratified sampling

---

## Troubleshooting

### App Won't Start
**Error**: `streamlit: command not found`
**Solution**: Install Streamlit: `pip install streamlit plotly`

### Missing Data Visualizations
**Status**: Demo mode with sample data
**Solution**: Run actual classification to see real results

### Earth Engine Errors
**Error**: `ee.Initialize() failed`
**Solution**: Authenticate: `earthengine authenticate`

### Configuration Not Saving
**Status**: In-memory only in demo
**Solution**: Edit `config.py` directly for persistent changes

---

## Customization

### Adding Your Own Species
1. Edit `config.py` and update `CLASS_NAMES`
2. Adjust `n_classes` parameter
3. Prepare training data with new classes
4. Re-run classification

### Custom Color Schemes
1. Go to **🗺️ Visualization** page
2. Use color pickers for each class
3. Copy generated Earth Engine code
4. Paste into Code Editor

### Additional Features
1. Edit `tree_species_classification.py`
2. Add new index calculation functions
3. Include in feature stack
4. Re-train classifier

---

## Performance Notes

- **Processing Time**: 10-90 minutes depending on area size
- **Memory**: Streamlit uses ~200-500MB RAM
- **Browser**: Works best in Chrome or Firefox
- **Resolution**: Dashboard optimized for 1920×1080 or higher

---

## Data Privacy

- All processing happens locally and on Google servers
- No data is sent to third parties
- Training data stays in your Earth Engine account
- Results are saved to your Google Drive

---

## Updates and Support

### Documentation Files
- `README.md` - Complete system documentation
- `QUICKSTART.md` - Quick start guide
- `PROJECT_OVERVIEW.md` - Scientific background
- `TEST_REPORT.txt` - Validation results

### Testing
Run comprehensive tests:
```bash
python test_pipeline.py
```

Run demonstrations:
```bash
python demo.py
```

---

## Advanced Features (Coming Soon)

- 📊 Real-time processing status
- 🗺️ Integrated map viewer
- 📈 Multi-year trend analysis
- 🔄 Batch processing multiple areas
- 📤 Direct export from UI
- 🎯 Active learning for sample selection
- 🌐 Multi-language support

---

## Keyboard Shortcuts

- `Ctrl + R` - Rerun application
- `Ctrl + C` - Stop server (in terminal)
- `?` - Show Streamlit keyboard shortcuts

---

## Credits

Built with:
- **Streamlit** - Web application framework
- **Plotly** - Interactive visualizations
- **Google Earth Engine** - Satellite data processing
- **Python** - Core programming language

---

## License

This project follows the same license as the original research paper implementation.

For questions and support, refer to the documentation files or run the demo scripts.

**Happy Classifying! 🌲🛰️**
