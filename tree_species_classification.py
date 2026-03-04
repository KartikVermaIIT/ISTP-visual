"""
Tree Species Classification using Multi-seasonal Sentinel-1 and Sentinel-2 Imagery
Implements classification pipeline with spectral indices, texture, and radar features
"""

import ee
import numpy as np
import pandas as pd
from datetime import datetime

# Note: Earth Engine initialized in main() or when needed
# Users should call ee.Initialize() before using the pipeline

# Configuration
CONFIG = {
    'year': 2019,
    'seasons': {
        'spring': {'start': '2019-03-01', 'end': '2019-03-31'},
        'summer': {'start': '2019-06-01', 'end': '2019-06-30'},
        'autumn': {'start': '2019-09-01', 'end': '2019-09-30'},
        'winter': {'start': '2019-12-01', 'end': '2019-12-31'}
    },
    'scale': 10,  # 10m resolution
    'n_trees': 71,  # Random Forest trees
    'n_classes': 7,  # Number of tree species classes
    'percentiles': [20, 80]
}


class SentinelProcessor:
    """Process Sentinel-1 and Sentinel-2 imagery"""
    
    def __init__(self, aoi, seasons):
        """
        Args:
            aoi: Area of interest (ee.Geometry)
            seasons: Dictionary of seasonal date ranges
        """
        self.aoi = aoi
        self.seasons = seasons
        
    def load_sentinel2(self, start_date, end_date):
        """Load and cloud-mask Sentinel-2 imagery"""
        def mask_s2_clouds(image):
            qa = image.select('QA60')
            # Bits 10 and 11 are clouds and cirrus
            cloud_bit_mask = 1 << 10
            cirrus_bit_mask = 1 << 11
            mask = qa.bitwiseAnd(cloud_bit_mask).eq(0).And(
                   qa.bitwiseAnd(cirrus_bit_mask).eq(0))
            return image.updateMask(mask).divide(10000)
        
        s2 = ee.ImageCollection('COPERNICUS/S2_SR') \
            .filterBounds(self.aoi) \
            .filterDate(start_date, end_date) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
            .map(mask_s2_clouds)
        
        return s2
    
    def load_sentinel1(self, start_date, end_date):
        """Load Sentinel-1 GRD imagery"""
        s1 = ee.ImageCollection('COPERNICUS/S1_GRD') \
            .filterBounds(self.aoi) \
            .filterDate(start_date, end_date) \
            .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV')) \
            .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH')) \
            .filter(ee.Filter.eq('instrumentMode', 'IW')) \
            .select(['VV', 'VH'])
        
        return s1
    
    def compute_spectral_indices(self, image):
        """Compute all spectral indices"""
        # Extract bands
        nir = image.select('B8')
        red = image.select('B4')
        green = image.select('B3')
        blue = image.select('B2')
        red_edge1 = image.select('B5')
        red_edge2 = image.select('B6')
        red_edge3 = image.select('B7')
        
        # NDVI: Normalized Difference Vegetation Index
        ndvi = nir.subtract(red).divide(nir.add(red)).rename('NDVI')
        
        # EVI: Enhanced Vegetation Index
        evi = nir.subtract(red).divide(
            nir.add(red.multiply(6)).subtract(blue.multiply(7.5)).add(1)
        ).multiply(2.5).rename('EVI')
        
        # IPVI: Infrared Percentage Vegetation Index
        ipvi = nir.divide(nir.add(red)).rename('IPVI')
        
        # TNDVI: Transformed NDVI
        tndvi = ndvi.add(0.5).sqrt().rename('TNDVI')
        
        # GNDVI: Green NDVI
        gndvi = nir.subtract(green).divide(nir.add(green)).rename('GNDVI')
        
        # BI2: Brightness Index 2
        bi2 = red.pow(2).add(green.pow(2)).add(nir.pow(2)).sqrt().rename('BI2')
        
        # MTCI: MERIS Terrestrial Chlorophyll Index
        mtci = red_edge2.subtract(red_edge1).divide(
            red_edge1.subtract(red)
        ).rename('MTCI')
        
        # REIP: Red Edge Inflection Point
        reip = red_edge1.add(
            red_edge3.subtract(red_edge1).multiply(
                nir.add(red).divide(2).subtract(red_edge1)
            ).divide(red_edge3.subtract(red_edge1))
        ).multiply(705).rename('REIP')
        
        # IRECI: Inverted Red-Edge Chlorophyll Index
        ireci = red_edge3.subtract(red).divide(
            red_edge1.divide(red_edge2)
        ).rename('IRECI')
        
        return image.addBands([ndvi, evi, ipvi, tndvi, gndvi, bi2, mtci, reip, ireci])
    
    def compute_glcm_texture(self, image, window_size=7):
        """Compute GLCM texture features from NIR band"""
        nir = image.select('B8').multiply(100).int()
        
        glcm = nir.glcmTexture(size=window_size)
        
        # Select relevant texture features
        texture_bands = [
            'B8_asm',      # Angular Second Moment (Energy)
            'B8_contrast',  # Contrast
            'B8_corr',      # Correlation
            'B8_var',       # Variance
            'B8_idm',       # Inverse Difference Moment (Homogeneity)
            'B8_savg',      # Sum Average
            'B8_ent',       # Entropy
            'B8_diss'       # Dissimilarity
        ]
        
        return image.addBands(glcm.select(texture_bands))
    
    def compute_radar_indices(self, image):
        """Compute radar indices from Sentinel-1"""
        vh = image.select('VH')
        vv = image.select('VV')
        
        # VH/VV ratio
        ratio = vh.divide(vv).rename('VH_VV_ratio')
        
        # VH - VV difference
        diff = vh.subtract(vv).rename('VH_VV_diff')
        
        # Amplitude
        amplitude = vh.add(vv).divide(2).rename('Amplitude')
        
        # Normalized Difference (VV - VH) / (VV + VH)
        nd = vv.subtract(vh).divide(vv.add(vh)).rename('VV_VH_ND')
        
        return image.addBands([ratio, diff, amplitude, nd])
    
    def compute_temporal_gradient(self, collection, band_name):
        """Compute temporal gradient between consecutive observations"""
        def calc_gradient(current, previous):
            prev = ee.Image(ee.List(previous).get(-1))
            gradient = current.select(band_name).subtract(
                prev.select(band_name)
            ).rename(f'{band_name}_gradient')
            return ee.List(previous).add(current.addBands(gradient))
        
        # Get first image
        first = ee.List([collection.first()])
        # Iterate and compute gradients
        gradients = ee.ImageCollection(
            ee.List(collection.iterate(calc_gradient, first))
        )
        return gradients
    
    def extract_percentiles(self, collection, percentiles=[20, 80]):
        """Extract percentile composites from image collection"""
        composites = []
        
        for percentile in percentiles:
            composite = collection.reduce(
                ee.Reducer.percentile([percentile])
            ).rename(
                collection.first().bandNames().map(
                    lambda name: ee.String(name).cat(f'_p{percentile}')
                )
            )
            composites.append(composite)
        
        return composites


class DEMProcessor:
    """Process Digital Elevation Model features"""
    
    def __init__(self):
        self.dem = ee.Image('USGS/SRTMGL1_003')
    
    def compute_slope_aspect(self, aoi):
        """Compute slope and aspect from DEM"""
        terrain = ee.Algorithms.Terrain(self.dem)
        slope = terrain.select('slope').rename('slope')
        aspect = terrain.select('aspect').rename('aspect_raw')
        
        # Categorize aspect into 8 directions (one-hot encoding)
        aspect_categories = self.categorize_aspect(aspect)
        
        return slope.addBands(aspect_categories)
    
    def categorize_aspect(self, aspect):
        """
        Categorize aspect into 8 directions with one-hot encoding
        N, NE, E, SE, S, SW, W, NW
        """
        categories = []
        directions = [
            ('N', 0, 22.5, 337.5, 360),
            ('NE', 22.5, 67.5),
            ('E', 67.5, 112.5),
            ('SE', 112.5, 157.5),
            ('S', 157.5, 202.5),
            ('SW', 202.5, 247.5),
            ('W', 247.5, 292.5),
            ('NW', 292.5, 337.5)
        ]
        
        for direction in directions:
            if direction[0] == 'N':
                # North wraps around
                mask = aspect.gte(direction[2]).Or(aspect.lt(direction[1]))
            else:
                mask = aspect.gte(direction[1]).And(aspect.lt(direction[2]))
            
            categories.append(mask.rename(f'aspect_{direction[0]}'))
        
        # Stack all category bands
        aspect_onehot = ee.Image.cat(categories)
        return aspect_onehot


class TreeSpeciesClassifier:
    """Random Forest classifier for tree species"""
    
    def __init__(self, n_trees=71, n_classes=7):
        self.n_trees = n_trees
        self.n_classes = n_classes
        self.classifier = None
        self.feature_names = None
        
    def prepare_training_data(self, feature_image, training_points):
        """
        Prepare training data from feature image and training points
        
        Args:
            feature_image: Multi-band image with all features
            training_points: FeatureCollection with 'class' property
        """
        # Sample the feature image at training points
        training = feature_image.sampleRegions(
            collection=training_points,
            properties=['class'],
            scale=CONFIG['scale'],
            tileScale=16
        )
        
        return training
    
    def train(self, training_data, feature_bands):
        """Train Random Forest classifier"""
        self.feature_names = feature_bands
        
        self.classifier = ee.Classifier.smileRandomForest(
            numberOfTrees=self.n_trees,
            variablesPerSplit=None,  # sqrt of features (default)
            minLeafPopulation=1,
            bagFraction=0.5,
            maxNodes=None,
            seed=42
        ).train(
            features=training_data,
            classProperty='class',
            inputProperties=feature_bands
        )
        
        return self.classifier
    
    def classify(self, feature_image):
        """Classify the feature image"""
        classified = feature_image.select(self.feature_names).classify(self.classifier)
        return classified
    
    def compute_accuracy(self, validation_data):
        """Compute confusion matrix, overall accuracy, and kappa"""
        # Test the classifier
        validated = validation_data.classify(self.classifier)
        
        # Get confusion matrix
        confusion_matrix = validated.errorMatrix('class', 'classification')
        
        # Compute metrics
        overall_accuracy = confusion_matrix.accuracy()
        kappa = confusion_matrix.kappa()
        producers_accuracy = confusion_matrix.producersAccuracy()
        consumers_accuracy = confusion_matrix.consumersAccuracy()
        
        return {
            'confusion_matrix': confusion_matrix,
            'overall_accuracy': overall_accuracy,
            'kappa': kappa,
            'producers_accuracy': producers_accuracy,
            'consumers_accuracy': consumers_accuracy
        }


class ZonalStatistics:
    """Compute zonal statistics for forest types"""
    
    def __init__(self, classified_image, scale=10):
        self.classified_image = classified_image
        self.scale = scale
    
    def compute_area_statistics(self, zones, class_names=None):
        """
        Compute area statistics per class within zones
        
        Args:
            zones: FeatureCollection with 'type' property (e.g., natural vs plantation)
            class_names: List of class names for labeling
        """
        def calculate_areas(feature):
            # Get zone geometry
            zone_geom = feature.geometry()
            zone_type = feature.get('type')
            
            # Compute pixel counts per class
            class_areas = self.classified_image.reduceRegion(
                reducer=ee.Reducer.frequencyHistogram(),
                geometry=zone_geom,
                scale=self.scale,
                maxPixels=1e13
            )
            
            return ee.Feature(None, {
                'zone_type': zone_type,
                'class_areas': class_areas
            })
        
        area_stats = zones.map(calculate_areas)
        return area_stats
    
    def pixel_count_to_area(self, pixel_count, scale=10):
        """Convert pixel count to area in hectares"""
        pixel_area_m2 = scale * scale
        area_hectares = (pixel_count * pixel_area_m2) / 10000
        return area_hectares


def build_feature_stack(aoi, seasons, training_points=None):
    """
    Build complete feature stack for all seasons
    
    Args:
        aoi: Area of interest (ee.Geometry)
        seasons: Dictionary of seasonal date ranges
        training_points: Optional training points for classification
    
    Returns:
        feature_image: Multi-band image with all features
        feature_bands: List of band names
    """
    sentinel_proc = SentinelProcessor(aoi, seasons)
    dem_proc = DEMProcessor()
    
    feature_images = []
    
    # Process each season
    for season_name, dates in seasons.items():
        print(f"Processing {season_name}...")
        
        # Load Sentinel-2
        s2_collection = sentinel_proc.load_sentinel2(dates['start'], dates['end'])
        
        # Compute spectral indices
        s2_with_indices = s2_collection.map(sentinel_proc.compute_spectral_indices)
        
        # Compute GLCM texture
        s2_with_texture = s2_with_indices.map(sentinel_proc.compute_glcm_texture)
        
        # Load Sentinel-1
        s1_collection = sentinel_proc.load_sentinel1(dates['start'], dates['end'])
        
        # Compute radar indices
        s1_with_indices = s1_collection.map(sentinel_proc.compute_radar_indices)
        
        # Extract percentiles for Sentinel-2
        s2_percentiles = sentinel_proc.extract_percentiles(
            s2_with_texture, 
            CONFIG['percentiles']
        )
        
        # Extract percentiles for Sentinel-1
        s1_percentiles = sentinel_proc.extract_percentiles(
            s1_with_indices,
            CONFIG['percentiles']
        )
        
        # Combine season features
        season_features = ee.Image.cat([
            *s2_percentiles,
            *s1_percentiles
        ]).rename(
            [f'{season_name}_{band}' for band in 
             ee.Image.cat([*s2_percentiles, *s1_percentiles]).bandNames().getInfo()]
        )
        
        feature_images.append(season_features)
    
    # Compute temporal gradients for EVI and VH
    print("Computing temporal gradients...")
    
    # Get EVI for all seasons
    evi_images = []
    vh_images = []
    
    for season_name, dates in seasons.items():
        s2 = sentinel_proc.load_sentinel2(dates['start'], dates['end'])
        s2_indices = s2.map(sentinel_proc.compute_spectral_indices)
        evi_median = s2_indices.select('EVI').median().rename(f'{season_name}_EVI_median')
        evi_images.append(evi_median)
        
        s1 = sentinel_proc.load_sentinel1(dates['start'], dates['end'])
        vh_median = s1.select('VH').median().rename(f'{season_name}_VH_median')
        vh_images.append(vh_median)
    
    # Compute gradients between consecutive seasons
    evi_gradients = []
    vh_gradients = []
    
    season_order = ['spring', 'summer', 'autumn', 'winter']
    for i in range(len(season_order) - 1):
        curr_season = season_order[i]
        next_season = season_order[i + 1]
        
        evi_grad = evi_images[i + 1].subtract(evi_images[i]).rename(
            f'EVI_gradient_{curr_season}_to_{next_season}'
        )
        vh_grad = vh_images[i + 1].subtract(vh_images[i]).rename(
            f'VH_gradient_{curr_season}_to_{next_season}'
        )
        
        evi_gradients.append(evi_grad)
        vh_gradients.append(vh_grad)
    
    # Add DEM features
    print("Adding DEM features...")
    dem_features = dem_proc.compute_slope_aspect(aoi)
    
    # Combine all features
    print("Combining all features...")
    all_features = ee.Image.cat([
        *feature_images,
        *evi_gradients,
        *vh_gradients,
        dem_features
    ])
    
    feature_bands = all_features.bandNames().getInfo()
    
    return all_features, feature_bands


def main(aoi, training_points, validation_points, forest_zones, export_path='tree_classification'):
    """
    Main classification pipeline
    
    Args:
        aoi: Area of interest (ee.Geometry)
        training_points: FeatureCollection with training points
        validation_points: FeatureCollection with validation points
        forest_zones: FeatureCollection with forest type zones
        export_path: Path for exporting results
    """
    print("=== Tree Species Classification Pipeline ===\n")
    
    # Build feature stack
    print("Step 1: Building feature stack...")
    feature_image, feature_bands = build_feature_stack(aoi, CONFIG['seasons'])
    print(f"Total features: {len(feature_bands)}\n")
    
    # Initialize classifier
    print("Step 2: Training Random Forest classifier...")
    classifier = TreeSpeciesClassifier(
        n_trees=CONFIG['n_trees'],
        n_classes=CONFIG['n_classes']
    )
    
    # Prepare training data
    training_data = classifier.prepare_training_data(feature_image, training_points)
    
    # Train classifier
    classifier.train(training_data, feature_bands)
    print("Training complete!\n")
    
    # Classify the image
    print("Step 3: Classifying image...")
    classified_image = classifier.classify(feature_image)
    print("Classification complete!\n")
    
    # Compute accuracy
    print("Step 4: Computing accuracy metrics...")
    validation_data = classifier.prepare_training_data(feature_image, validation_points)
    accuracy_metrics = classifier.compute_accuracy(validation_data)
    
    print(f"Overall Accuracy: {accuracy_metrics['overall_accuracy'].getInfo():.4f}")
    print(f"Kappa Coefficient: {accuracy_metrics['kappa'].getInfo():.4f}")
    print(f"\nConfusion Matrix:")
    print(accuracy_metrics['confusion_matrix'].getInfo())
    print()
    
    # Compute zonal statistics
    print("Step 5: Computing zonal statistics...")
    zonal_stats = ZonalStatistics(classified_image, scale=CONFIG['scale'])
    area_statistics = zonal_stats.compute_area_statistics(forest_zones)
    
    print("Area statistics computed!\n")
    
    # Export classified image
    print("Step 6: Exporting results...")
    export_task = ee.batch.Export.image.toDrive(
        image=classified_image.toByte(),
        description=f'{export_path}_classified',
        folder='GEE_Exports',
        fileNamePrefix=f'{export_path}_classified_10m',
        region=aoi,
        scale=CONFIG['scale'],
        maxPixels=1e13,
        crs='EPSG:4326'
    )
    export_task.start()
    print(f"Export task started: {export_path}_classified")
    
    # Export accuracy metrics (as feature collection)
    accuracy_fc = ee.FeatureCollection([
        ee.Feature(None, {
            'overall_accuracy': accuracy_metrics['overall_accuracy'],
            'kappa': accuracy_metrics['kappa']
        })
    ])
    
    export_accuracy = ee.batch.Export.table.toDrive(
        collection=accuracy_fc,
        description=f'{export_path}_accuracy',
        folder='GEE_Exports',
        fileNamePrefix=f'{export_path}_accuracy_metrics'
    )
    export_accuracy.start()
    print(f"Export task started: {export_path}_accuracy")
    
    # Export area statistics
    export_stats = ee.batch.Export.table.toDrive(
        collection=area_statistics,
        description=f'{export_path}_area_stats',
        folder='GEE_Exports',
        fileNamePrefix=f'{export_path}_area_statistics'
    )
    export_stats.start()
    print(f"Export task started: {export_path}_area_stats")
    
    print("\n=== Pipeline Complete ===")
    print("Check Google Drive for exported results.")
    
    return {
        'classified_image': classified_image,
        'feature_image': feature_image,
        'accuracy_metrics': accuracy_metrics,
        'area_statistics': area_statistics,
        'classifier': classifier
    }


# Example usage
if __name__ == "__main__":
    # Define your area of interest
    # Example: Replace with your actual coordinates
    aoi = ee.Geometry.Rectangle([
        -122.5, 37.5,  # [lon_min, lat_min, lon_max, lat_max]
        -122.0, 38.0
    ])
    
    # Load your training and validation points
    # These should be FeatureCollections with a 'class' property (0-6 for 7 classes)
    # Example:
    # training_points = ee.FeatureCollection('users/your_username/training_points')
    # validation_points = ee.FeatureCollection('users/your_username/validation_points')
    # forest_zones = ee.FeatureCollection('users/your_username/forest_zones')
    
    # For demonstration, create dummy data
    # In practice, you should load your actual data
    print("Note: Replace dummy data with your actual training/validation points")
    print("Expected format:")
    print("  - Training/Validation points: FeatureCollection with 'class' property (0-6)")
    print("  - Forest zones: FeatureCollection with 'type' property ('natural' or 'plantation')")
    print("\nTo run the full pipeline, uncomment the main() call below and provide your data.")
    
    # Uncomment and modify the following to run:
    # results = main(
    #     aoi=aoi,
    #     training_points=training_points,
    #     validation_points=validation_points,
    #     forest_zones=forest_zones,
    #     export_path='tree_species_2019'
    # )
