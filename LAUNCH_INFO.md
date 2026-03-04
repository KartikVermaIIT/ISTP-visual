# 🚀 Launch Instructions

## Your Streamlit Web UI is Now Running!

### Access the Application
Open your web browser and go to:
**http://localhost:8501**

The application should open automatically in your default browser.

---

## What You Can Do Now

### 1. 🏠 Home Page
- View system overview and quick start guide
- Download CSV template for training data
- Learn about the processing pipeline

### 2. ⚙️ Configuration
- Set study area coordinates
- Adjust seasonal date ranges
- Configure classification parameters
- Enable/disable feature groups

### 3. 📊 Results Dashboard
- View accuracy metrics (Overall Accuracy, Kappa)
- Interactive confusion matrix
- Per-class performance statistics
- Download reports

### 4. 📈 Analysis
- Area distribution charts (pie chart, bar chart)
- Feature importance rankings
- Forest type comparisons
- Detailed statistics tables

### 5. 🗺️ Visualization
- Customize color schemes
- Generate Earth Engine visualization code
- View classification maps (with real data)

### 6. 📚 Documentation
- Complete user guide
- Scientific methodology
- FAQ and troubleshooting
- External resources

---

## Demo Mode

The UI is currently showing **demo data** with:
- Sample confusion matrices
- Example area statistics
- Feature importance charts
- Simulated accuracy metrics (~89% OA, 0.88 Kappa)

### To Use with Real Data:
1. Run the actual classification: `python tree_species_classification.py`
2. The results will be exported to Google Drive
3. Load them into the UI for visualization

---

## Tips

- 💡 **Navigate** using the sidebar on the left
- 📊 **Interactive charts** - hover for details, zoom, pan
- 📥 **Download** buttons available throughout
- 🎨 **Customize** colors in Visualization page
- 📋 **Copy** code snippets directly

---

## Keyboard Shortcuts

- `Ctrl + R` - Reload the app
- `Ctrl + C` (in terminal) - Stop the server

---

## If the Browser Doesn't Open

Manually navigate to: **http://localhost:8501**

Or check the terminal for the exact URL.

---

## Need Help?

- Read **STREAMLIT_GUIDE.md** for detailed instructions
- Check **README.md** for system documentation
- Run **demo.py** to see all features
- Read **QUICKSTART.md** for classification guide

---

**Enjoy exploring your tree species classification system! 🌲🛰️**
