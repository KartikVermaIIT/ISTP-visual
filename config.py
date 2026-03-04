"""
Configuration file for tree species classification
Modify these settings for your specific study area and requirements
"""

# ==============================================================================
# STUDY AREA CONFIGURATION
# ==============================================================================

# Area of Interest (AOI)
# Define your study area using lon/lat coordinates
# Format: [lon_min, lat_min, lon_max, lat_max]
AOI_COORDINATES = [
    10.0, 48.0,   # Southwest corner (longitude, latitude)
    10.5, 48.5    # Northeast corner (longitude, latitude)
]

# Alternative: Load AOI from asset
# AOI_ASSET = 'users/YOUR_USERNAME/study_area'
AOI_ASSET = None


# ==============================================================================
# TEMPORAL CONFIGURATION
# ==============================================================================

# Year of analysis
YEAR = 2019

# Seasonal date ranges (adjust for your region's phenology)
# Format: 'YYYY-MM-DD'
SEASONS = {
    'spring': {
        'start': '2019-03-01',
        'end': '2019-03-31'
    },
    'summer': {
        'start': '2019-06-01',
        'end': '2019-06-30'
    },
    'autumn': {
        'start': '2019-09-01',
        'end': '2019-09-30'
    },
    'winter': {
        'start': '2019-12-01',
        'end': '2019-12-31'
    }
}


# ==============================================================================
# DATA SOURCES
# ==============================================================================

# Training data
# Replace with your Earth Engine asset IDs
TRAINING_DATA = 'users/YOUR_USERNAME/training_points'

# Validation data
VALIDATION_DATA = 'users/YOUR_USERNAME/validation_points'

# Forest zones (for zonal statistics)
# Optional: set to None if not available
FOREST_ZONES = 'users/YOUR_USERNAME/forest_zones'
# FOREST_ZONES = None


# ==============================================================================
# CLASSIFICATION CONFIGURATION
# ==============================================================================

# Number of tree species classes
N_CLASSES = 7

# Class definitions
# Modify these to match your tree species
CLASS_NAMES = [
    'Oak',          # Class 0
    'Pine',         # Class 1
    'Spruce',       # Class 2
    'Beech',        # Class 3
    'Birch',        # Class 4
    'Fir',          # Class 5
    'Mixed Forest'  # Class 6
]

# Class property name in training data
CLASS_PROPERTY = 'class'

# Random Forest parameters
RF_N_TREES = 71                    # Number of decision trees
RF_VARIABLES_PER_SPLIT = None      # Features per split (None = sqrt of total features)
RF_MIN_LEAF_POPULATION = 1         # Minimum samples per leaf node
RF_BAG_FRACTION = 0.5              # Fraction of input to bag per tree
RF_MAX_NODES = None                # Maximum number of leaf nodes (None = unlimited)
RF_SEED = 42                       # Random seed for reproducibility


# ==============================================================================
# FEATURE EXTRACTION CONFIGURATION
# ==============================================================================

# Spatial resolution (meters)
# Options: 10 (high quality, slower) or 20 (faster)
SPATIAL_RESOLUTION = 10

# Percentile composites to extract
PERCENTILES = [20, 80]

# GLCM texture window size
GLCM_WINDOW_SIZE = 7

# Cloud cover threshold for Sentinel-2 (percent)
# Images with more cloud cover will be filtered out
CLOUD_COVER_THRESHOLD = 20


# ==============================================================================
# FEATURE SELECTION
# ==============================================================================

# Toggle feature groups on/off
FEATURES = {
    'sentinel2_bands': True,        # Original Sentinel-2 bands
    'spectral_indices': True,       # NDVI, EVI, GNDVI, etc.
    'texture': True,                # GLCM texture features
    'sentinel1_bands': True,        # VV, VH backscatter
    'radar_indices': True,          # VH/VV ratio, etc.
    'temporal_gradients': True,     # EVI and VH gradients
    'terrain': True,                # Slope and aspect from DEM
}

# Specific spectral indices to compute
# Set to False to disable individual indices
SPECTRAL_INDICES = {
    'NDVI': True,   # Normalized Difference Vegetation Index
    'EVI': True,    # Enhanced Vegetation Index
    'IPVI': True,   # Infrared Percentage Vegetation Index
    'TNDVI': True,  # Transformed NDVI
    'GNDVI': True,  # Green NDVI
    'BI2': True,    # Brightness Index 2
    'MTCI': True,   # MERIS Terrestrial Chlorophyll Index
    'REIP': True,   # Red Edge Inflection Point
    'IRECI': True,  # Inverted Red-Edge Chlorophyll Index
}


# ==============================================================================
# EXPORT CONFIGURATION
# ==============================================================================

# Export settings
EXPORT_PREFIX = 'tree_classification_2019'

# Google Drive folder for exports
EXPORT_FOLDER = 'GEE_Exports'

# Maximum pixels for export
# Increase for larger areas (may cause memory errors)
MAX_PIXELS = 1e13

# Tile scale for processing
# Increase (e.g., 8 or 16) if you encounter memory errors
TILE_SCALE = 4

# Output coordinate reference system
OUTPUT_CRS = 'EPSG:4326'  # WGS84


# ==============================================================================
# PROCESSING CONFIGURATION
# ==============================================================================

# Train/validation split ratio
# Only used if splitting data programmatically
TRAIN_RATIO = 0.7

# Balance training classes
# Set to True to use equal samples per class
BALANCE_CLASSES = True

# Samples per class (if balancing)
# None = use minimum class size
SAMPLES_PER_CLASS = None

# Random seed for data splitting
DATA_SPLIT_SEED = 42


# ==============================================================================
# VISUALIZATION CONFIGURATION
# ==============================================================================

# Color palette for visualization (one color per class)
# Format: Hex color codes
CLASS_COLORS = [
    '#1f77b4',  # Class 0 - Blue
    '#ff7f0e',  # Class 1 - Orange
    '#2ca02c',  # Class 2 - Green
    '#d62728',  # Class 3 - Red
    '#9467bd',  # Class 4 - Purple
    '#8c564b',  # Class 5 - Brown
    '#e377c2',  # Class 6 - Pink
]


# ==============================================================================
# ADVANCED CONFIGURATION
# ==============================================================================

# DEM source
# Options: 'USGS/SRTMGL1_003' (30m SRTM) or 'USGS/3DEP/10m' (US only)
DEM_SOURCE = 'USGS/SRTMGL1_003'

# Aspect categories
# 8 cardinal directions
ASPECT_CATEGORIES = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']

# Sentinel-1 orbit direction
# Options: 'ASCENDING', 'DESCENDING', or None (both)
S1_ORBIT_DIRECTION = None

# Sentinel-2 processing level
# 'COPERNICUS/S2_SR' (Surface Reflectance) recommended
S2_COLLECTION = 'COPERNICUS/S2_SR'

# Sentinel-1 collection
S1_COLLECTION = 'COPERNICUS/S1_GRD'


# ==============================================================================
# VALIDATION
# ==============================================================================

def validate_config():
    """Validate configuration settings"""
    errors = []
    warnings = []
    
    # Check required fields
    if 'YOUR_USERNAME' in TRAINING_DATA:
        errors.append("Please update TRAINING_DATA with your Earth Engine username")
    
    if 'YOUR_USERNAME' in VALIDATION_DATA:
        errors.append("Please update VALIDATION_DATA with your Earth Engine username")
    
    # Check class configuration
    if len(CLASS_NAMES) != N_CLASSES:
        errors.append(f"Number of CLASS_NAMES ({len(CLASS_NAMES)}) must match N_CLASSES ({N_CLASSES})")
    
    if len(CLASS_COLORS) != N_CLASSES:
        warnings.append(f"Number of CLASS_COLORS ({len(CLASS_COLORS)}) should match N_CLASSES ({N_CLASSES})")
    
    # Check temporal configuration
    if YEAR < 2015:
        warnings.append("Sentinel-2 data is limited before 2015")
    
    # Check spatial resolution
    if SPATIAL_RESOLUTION < 10:
        warnings.append("Resolution finer than 10m may not improve results (Sentinel-2 native resolution)")
    
    if SPATIAL_RESOLUTION > 30:
        warnings.append("Resolution coarser than 30m may lose important details")
    
    # Check percentiles
    if not all(0 <= p <= 100 for p in PERCENTILES):
        errors.append("Percentiles must be between 0 and 100")
    
    # Print results
    if errors:
        print("❌ Configuration Errors:")
        for error in errors:
            print(f"   - {error}")
    
    if warnings:
        print("\n⚠️  Configuration Warnings:")
        for warning in warnings:
            print(f"   - {warning}")
    
    if not errors and not warnings:
        print("✅ Configuration validated successfully!")
    
    return len(errors) == 0


if __name__ == "__main__":
    print("="*70)
    print("Tree Species Classification - Configuration Check")
    print("="*70 + "\n")
    
    validate_config()
    
    print("\n" + "="*70)
    print("Configuration Summary:")
    print("="*70)
    print(f"Study Year: {YEAR}")
    print(f"Number of Classes: {N_CLASSES}")
    print(f"Spatial Resolution: {SPATIAL_RESOLUTION}m")
    print(f"Random Forest Trees: {RF_N_TREES}")
    print(f"Features Enabled: {sum(FEATURES.values())}/{len(FEATURES)}")
    print("="*70)
