"""
Tree Species Classification Pipeline
Implements the full methodology from the paper:
  "Multi-seasonal Sentinel-1 and Sentinel-2 based Random Forest classification
   of tree species at 10 m resolution"

Features used (all computed in Google Earth Engine):
  - Sentinel-2: 4 seasonal composites (spring/summer/autumn/winter)
      Bands: B2 B3 B4 B5 B6 B7 B8 B8A B11 B12
      Indices: NDVI EVI IPVI TNDVI GNDVI BI2 MTCI REIP IRECI
  - Sentinel-1: 4 seasonal composites   Bands: VV VH
      Radar indices: VH/VV VH-VV amplitude normalized-difference
  - Temporal gradients: EVI (3) + VH (3)
  - GLCM textures (8 features from NIR band)
  - 20th + 80th annual percentiles for all S2 and S1 features
  - DEM: slope + aspect (8-direction one-hot encoded)
Classifier: Random Forest, 71 trees, trained and run entirely in GEE.
"""

import ee
import numpy as np
import pandas as pd
from datetime import datetime

# ─── Constants ────────────────────────────────────────────────────────────────
RF_TREES    = 71
CLASS_NAMES = ['Oak', 'Pine', 'Spruce', 'Beech', 'Birch', 'Fir', 'Mixed Forest']
N_CLASSES   = len(CLASS_NAMES)

SEASONS = [
    ('spring', '03-01', '05-31'),
    ('summer', '06-01', '08-31'),
    ('autumn', '09-01', '11-30'),
    ('winter', '12-01', '12-31'),
]

S2_BANDS = ['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B11', 'B12']
S2_INDEX_BANDS = ['NDVI', 'EVI', 'IPVI', 'TNDVI', 'GNDVI', 'BI2', 'MTCI', 'REIP', 'IRECI']
S1_BANDS       = ['VV', 'VH']
RADAR_IDX_BANDS = ['VH_VV_ratio', 'VH_VV_diff', 'amplitude', 'radar_norm']
GLCM_KEYS      = ['asm', 'contrast', 'corr', 'var', 'idm', 'savg', 'ent', 'diss']


# ─── Sentinel-2 ───────────────────────────────────────────────────────────────
def _mask_s2_clouds(image):
    """Cloud/shadow masking using the SCL band (0-1 reflectance scaling)."""
    scl = image.select('SCL')
    # Keep: 4 (vegetation), 5 (bare), 6 (water), 7 (unclassified), 11 (snow)
    # Remove: 3 (cloud shadow), 8-10 (cloud / cirrus)
    clear = (scl.neq(3)
               .And(scl.neq(8))
               .And(scl.neq(9))
               .And(scl.neq(10)))
    return image.updateMask(clear).divide(10000).copyProperties(image, ['system:time_start'])


def _compute_s2_indices(img):
    """Compute the 9 spectral indices from the paper."""
    B2, B3, B4 = img.select('B2'), img.select('B3'), img.select('B4')
    B5, B6, B7, B8 = img.select('B5'), img.select('B6'), img.select('B7'), img.select('B8')

    NDVI  = img.normalizedDifference(['B8', 'B4']).rename('NDVI')

    EVI   = img.expression(
        '2.5 * (NIR - R) / (NIR + 6.0 * R - 7.5 * B + 1.0)',
        {'NIR': B8, 'R': B4, 'B': B2}
    ).rename('EVI')

    IPVI  = img.expression('NIR / (NIR + R)', {'NIR': B8, 'R': B4}).rename('IPVI')

    TNDVI = NDVI.add(0.5).sqrt().rename('TNDVI')

    GNDVI = img.normalizedDifference(['B8', 'B3']).rename('GNDVI')

    BI2   = img.expression(
        'sqrt((R*R + G*G + NIR*NIR) / 3.0)',
        {'R': B4, 'G': B3, 'NIR': B8}
    ).rename('BI2')

    MTCI  = img.expression(
        '(NIR - RE1) / (RE1 - R)',
        {'NIR': B8, 'RE1': B5, 'R': B4}
    ).rename('MTCI')

    REIP  = img.expression(
        '700.0 + 40.0 * ((R + NIR) / 2.0 - RE1) / (RE2 - RE1)',
        {'R': B4, 'NIR': B8, 'RE1': B5, 'RE2': B6}
    ).rename('REIP')

    IRECI = img.expression(
        '(RE3 - R) / (RE1 / RE2)',
        {'RE3': B7, 'R': B4, 'RE1': B5, 'RE2': B6}
    ).rename('IRECI')

    return img.addBands([NDVI, EVI, IPVI, TNDVI, GNDVI, BI2, MTCI, REIP, IRECI])


def _load_s2_season(aoi, year, month_start, month_end):
    """Cloud-masked, index-enriched seasonal median composite."""
    return (
        ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        .filterBounds(aoi)
        .filterDate(f'{year}-{month_start}', f'{year}-{month_end}')
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
        .map(_mask_s2_clouds)
        .map(_compute_s2_indices)
        .median()
        .clip(aoi)
    )


# ─── Sentinel-1 ───────────────────────────────────────────────────────────────
def _compute_radar_indices(img):
    """VH/VV ratio, difference, amplitude, normalized difference."""
    vv = img.select('VV')
    vh = img.select('VH')
    ratio = vh.divide(vv).rename('VH_VV_ratio')
    diff  = vh.subtract(vv).rename('VH_VV_diff')
    amp   = vv.pow(2).add(vh.pow(2)).sqrt().rename('amplitude')
    norm  = vv.subtract(vh).divide(vv.add(vh)).rename('radar_norm')
    return img.addBands([ratio, diff, amp, norm]).copyProperties(img, ['system:time_start'])


def _load_s1_season(aoi, year, month_start, month_end):
    """IW-mode, dual-pol Sentinel-1 seasonal median composite."""
    return (
        ee.ImageCollection('COPERNICUS/S1_GRD')
        .filterBounds(aoi)
        .filterDate(f'{year}-{month_start}', f'{year}-{month_end}')
        .filter(ee.Filter.eq('instrumentMode', 'IW'))
        .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
        .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'))
        .select(['VV', 'VH'])
        .map(_compute_radar_indices)
        .median()
        .clip(aoi)
    )


# ─── Temporal gradients ───────────────────────────────────────────────────────
def _temporal_gradients(sp, su, au, wi, band):
    """Compute three temporal gradients: spring→summer, summer→autumn, autumn→winter."""
    g1 = su.select(band).subtract(sp.select(band)).rename(f'{band}_grad_sp_su')
    g2 = au.select(band).subtract(su.select(band)).rename(f'{band}_grad_su_au')
    g3 = wi.select(band).subtract(au.select(band)).rename(f'{band}_grad_au_wi')
    return ee.Image([g1, g2, g3])


# ─── GLCM textures ────────────────────────────────────────────────────────────
def _glcm_textures(s2_summer):
    """8 GLCM features from the NIR (B8) summer composite."""
    nir_int = s2_summer.select('B8').multiply(10000).toInt32()
    glcm    = nir_int.glcmTexture(size=1)
    wanted  = [f'B8_{k}' for k in GLCM_KEYS]
    # Only keep bands that actually exist (safe across regions)
    available = [b for b in wanted if b in glcm.bandNames().getInfo()]
    return glcm.select(available) if available else ee.Image([])


# ─── DEM terrain features ─────────────────────────────────────────────────────
def _dem_features(aoi):
    """Slope + 8-direction aspect one-hot encoded from SRTM DEM."""
    dem     = ee.Image('USGS/SRTMGL1_003').clip(aoi)
    terrain = ee.Algorithms.Terrain(dem)
    slope   = terrain.select('slope').rename('slope')
    aspect  = terrain.select('aspect')

    # 8 cardinal directions
    dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    bounds = [
        (337.5, 360, 'wrap_N'), (0, 22.5, 'N'),
        (22.5,  67.5,  'NE'),
        (67.5,  112.5, 'E'),
        (112.5, 157.5, 'SE'),
        (157.5, 202.5, 'S'),
        (202.5, 247.5, 'SW'),
        (247.5, 292.5, 'W'),
        (292.5, 337.5, 'NW'),
    ]
    # Build N mask (wraps around 360)
    n_mask  = aspect.lt(22.5).Or(aspect.gte(337.5)).rename('aspect_N').toFloat()
    ne_mask = aspect.gte(22.5).And(aspect.lt(67.5)).rename('aspect_NE').toFloat()
    e_mask  = aspect.gte(67.5).And(aspect.lt(112.5)).rename('aspect_E').toFloat()
    se_mask = aspect.gte(112.5).And(aspect.lt(157.5)).rename('aspect_SE').toFloat()
    s_mask  = aspect.gte(157.5).And(aspect.lt(202.5)).rename('aspect_S').toFloat()
    sw_mask = aspect.gte(202.5).And(aspect.lt(247.5)).rename('aspect_SW').toFloat()
    w_mask  = aspect.gte(247.5).And(aspect.lt(292.5)).rename('aspect_W').toFloat()
    nw_mask = aspect.gte(292.5).And(aspect.lt(337.5)).rename('aspect_NW').toFloat()

    return ee.Image([
        slope, n_mask, ne_mask, e_mask, se_mask,
        s_mask, sw_mask, w_mask, nw_mask
    ])


# ─── Annual percentiles ───────────────────────────────────────────────────────
def _annual_percentiles(aoi, year):
    """20th and 80th annual percentile for S2 and S1 features."""
    s2_col = (
        ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        .filterBounds(aoi)
        .filterDate(f'{year}-01-01', f'{year}-12-31')
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
        .map(_mask_s2_clouds)
        .map(_compute_s2_indices)
    )
    s1_col = (
        ee.ImageCollection('COPERNICUS/S1_GRD')
        .filterBounds(aoi)
        .filterDate(f'{year}-01-01', f'{year}-12-31')
        .filter(ee.Filter.eq('instrumentMode', 'IW'))
        .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
        .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'))
        .select(['VV', 'VH'])
        .map(_compute_radar_indices)
    )
    s2_p20 = s2_col.reduce(ee.Reducer.percentile([20]))
    s2_p80 = s2_col.reduce(ee.Reducer.percentile([80]))
    s1_p20 = s1_col.reduce(ee.Reducer.percentile([20]))
    s1_p80 = s1_col.reduce(ee.Reducer.percentile([80]))
    return s2_p20, s2_p80, s1_p20, s1_p80


# ─── Full feature stack ───────────────────────────────────────────────────────
def build_feature_stack(aoi, year, status_callback=None):
    """
    Assemble the complete feature stack used for classification:
      - 4 × S2 seasonal composites (10 spectral + 9 index bands each)
      - 4 × S1 seasonal composites (2 SAR + 4 radar-index bands each)
      - EVI temporal gradients (3)
      - VH temporal gradients (3)
      - GLCM textures (up to 8)
      - S2/S1 annual 20th + 80th percentiles
      - DEM slope + 8 one-hot aspect bands
    Returns an ee.Image with all bands flattened and named.
    """
    def cb(msg):
        if status_callback:
            status_callback(msg)

    cb("📡 Loading Sentinel-2 seasonal composites (4 seasons × cloud-masked)...")
    s2 = {name: _load_s2_season(aoi, year, ms, me) for name, ms, me in SEASONS}

    cb("📡 Loading Sentinel-1 seasonal composites (4 seasons × IW dual-pol)...")
    s1 = {name: _load_s1_season(aoi, year, ms, me) for name, ms, me in SEASONS}

    cb("📐 Computing EVI & VH temporal gradients...")
    evi_grads = _temporal_gradients(s2['spring'], s2['summer'], s2['autumn'], s2['winter'], 'EVI')
    vh_grads  = _temporal_gradients(s1['spring'], s1['summer'], s1['autumn'], s1['winter'], 'VH')

    cb("🔲 Computing GLCM texture features (NIR-band summer composite)...")
    glcm = _glcm_textures(s2['summer'])

    cb("📊 Computing annual 20th/80th percentiles (S2 + S1)...")
    s2_p20, s2_p80, s1_p20, s1_p80 = _annual_percentiles(aoi, year)

    cb("🏔️ Adding DEM slope + 8-direction one-hot aspect...")
    dem = _dem_features(aoi)

    # ── Assemble seasonal layers with consistent naming ──────────────────────
    s2_sel = S2_BANDS + S2_INDEX_BANDS
    s1_sel = S1_BANDS + RADAR_IDX_BANDS

    layer_list = []
    for season_name in ['spring', 'summer', 'autumn', 'winter']:
        # S2
        s2_s = s2[season_name].select(s2_sel)
        for b in s2_sel:
            layer_list.append(s2_s.select(b).rename(f's2_{season_name}_{b}'))
        # S1
        s1_s = s1[season_name].select(s1_sel)
        for b in s1_sel:
            layer_list.append(s1_s.select(b).rename(f's1_{season_name}_{b}'))

    # Temporal gradients + textures + percentiles + DEM
    layer_list.append(evi_grads)
    layer_list.append(vh_grads)
    if glcm.bandNames().size().getInfo() > 0:
        layer_list.append(glcm)
    layer_list.append(s2_p20)
    layer_list.append(s2_p80)
    layer_list.append(s1_p20)
    layer_list.append(s1_p80)
    layer_list.append(dem)

    stack = ee.Image(layer_list).toFloat()

    cb(f"✅ Feature stack ready ({stack.bandNames().size().getInfo()} bands total)")
    return stack


# ─── Training data conversion ─────────────────────────────────────────────────
def df_to_feature_collection(df, class_col='class'):
    """Convert lon/lat/class DataFrame to EE FeatureCollection."""
    features = []
    for _, row in df.iterrows():
        feat = ee.Feature(
            ee.Geometry.Point([float(row['longitude']), float(row['latitude'])]),
            {class_col: int(row[class_col])}
        )
        features.append(feat)
    return ee.FeatureCollection(features)


# ─── Training + classification ────────────────────────────────────────────────
def train_and_classify(feature_stack, training_df, class_col='class',
                       validation_split=0.2, status_callback=None):
    """
    1. Convert CSV training points → EE FeatureCollection
    2. Random 80/20 split inside GEE
    3. Sample feature stack at training points
    4. Train smileRandomForest(71 trees)
    5. Classify full image
    6. Evaluate on held-out validation points
    Returns: (classified_image, confusion_matrix_ee)
    """
    def cb(msg):
        if status_callback:
            status_callback(msg)

    cb(f"🗂️ Converting {len(training_df)} GPS training points to EE FeatureCollection...")
    all_fc = df_to_feature_collection(training_df, class_col)
    all_fc = all_fc.randomColumn(columnName='split_rand', seed=42)
    train_fc = all_fc.filter(ee.Filter.gt('split_rand', validation_split))
    val_fc   = all_fc.filter(ee.Filter.lte('split_rand', validation_split))

    cb("🌍 Sampling spectral/radar/texture features at training GPS points...")
    train_samples = feature_stack.sampleRegions(
        collection=train_fc,
        properties=[class_col],
        scale=10,
        tileScale=8,
        geometries=False
    )

    cb(f"🌲 Training Random Forest ({RF_TREES} trees) — running on GEE servers...")
    classifier = (
        ee.Classifier.smileRandomForest(
            numberOfTrees=RF_TREES,
            seed=42
        )
        .train(
            features=train_samples,
            classProperty=class_col,
            inputProperties=feature_stack.bandNames()
        )
    )

    cb("🗺️ Classifying full AOI (all pixels) using trained RF model...")
    classified = feature_stack.classify(classifier).rename('classification').toByte()

    cb("📏 Sampling validation points and computing confusion matrix...")
    val_samples = feature_stack.sampleRegions(
        collection=val_fc,
        properties=[class_col],
        scale=10,
        tileScale=8,
        geometries=False
    )
    validated = val_samples.classify(classifier)
    cm = validated.errorMatrix(class_col, 'classification')

    return classified, cm


# ─── Accuracy metrics ─────────────────────────────────────────────────────────
def get_accuracy_metrics(cm_ee, class_names=None):
    """
    Pull GEE confusion matrix to numpy and compute:
      overall accuracy, kappa, per-class producer/user accuracy, F1.
    Returns: (metrics_df, cm_array, overall_accuracy, kappa)
    """
    if class_names is None:
        class_names = CLASS_NAMES

    cm_list  = cm_ee.array().getInfo()
    cm_array = np.array(cm_list)
    oa       = float(cm_ee.accuracy().getInfo())
    kappa    = float(cm_ee.kappa().getInfo())

    n = min(cm_array.shape[0], len(class_names))
    row_sums = cm_array.sum(axis=1)
    col_sums = cm_array.sum(axis=0)
    diag     = np.diag(cm_array)

    producers = [
        float(diag[i] / row_sums[i]) if row_sums[i] > 0 else 0.0
        for i in range(n)
    ]
    users = [
        float(diag[i] / col_sums[i]) if col_sums[i] > 0 else 0.0
        for i in range(n)
    ]
    f1 = [
        2 * p * u / (p + u) if (p + u) > 0 else 0.0
        for p, u in zip(producers, users)
    ]
    sample_ct = [int(row_sums[i]) for i in range(n)]

    rows = []
    for i in range(n):
        rows.append({
            'Class': i,
            'Species': class_names[i],
            'Producer_Accuracy': round(producers[i], 4),
            'User_Accuracy':     round(users[i], 4),
            'F1_Score':          round(f1[i], 4),
            'Sample_Count':      sample_ct[i],
        })
    rows.append({
        'Class': 'Overall',
        'Species': 'All Species',
        'Producer_Accuracy': round(oa, 4),
        'User_Accuracy':     round(oa, 4),
        'F1_Score':          round(float(np.mean(f1)), 4),
        'Sample_Count':      int(sum(sample_ct)),
    })

    return pd.DataFrame(rows), cm_array, oa, kappa


# ─── Area statistics per class ────────────────────────────────────────────────
def get_area_statistics(classified_ee, aoi, class_names=None):
    """
    Frequency histogram → hectares per class + percentage.
    Returns: area_df
    """
    if class_names is None:
        class_names = CLASS_NAMES

    hist_dict = (
        classified_ee
        .reduceRegion(
            reducer=ee.Reducer.frequencyHistogram(),
            geometry=aoi,
            scale=10,
            maxPixels=1e10,
            tileScale=8
        )
        .getInfo()
        .get('classification', {})
    )

    pixel_area_ha = 0.01   # 10 m × 10 m = 100 m² = 0.01 ha
    total_pixels  = sum(int(v) for v in hist_dict.values()) if hist_dict else 0

    rows = []
    for cid, name in enumerate(class_names):
        pix  = int(hist_dict.get(str(cid), 0))
        area = round(pix * pixel_area_ha, 2)
        pct  = round(pix / total_pixels * 100, 2) if total_pixels > 0 else 0.0
        rows.append({
            'Class':         cid,
            'Species':       name,
            'Pixel_Count':   pix,
            'Area_Hectares': area,
            'Percentage':    pct,
        })

    return pd.DataFrame(rows)


# ─── Master function ──────────────────────────────────────────────────────────
def run_full_pipeline(aoi_coords, year, training_df,
                      class_col='class',
                      class_names=None,
                      validation_split=0.2,
                      status_callback=None):
    """
    End-to-end pipeline:
      aoi_coords : [lon_min, lat_min, lon_max, lat_max]
      year       : int (e.g. 2023)
      training_df: pd.DataFrame with columns [longitude, latitude, <class_col>]
      class_col  : name of the integer class column in training_df
      class_names: list of N species names (must match integer labels 0..N-1)
      validation_split: fraction of points held out for accuracy assessment
      status_callback: callable(str) for progress messages

    Returns dict with keys:
      classified_ee, metrics_df, area_df, cm_array, overall_accuracy, kappa
    """
    if class_names is None:
        class_names = CLASS_NAMES

    aoi = ee.Geometry.Rectangle(aoi_coords)

    feature_stack = build_feature_stack(aoi, year, status_callback=status_callback)

    classified, cm_ee = train_and_classify(
        feature_stack, training_df,
        class_col=class_col,
        validation_split=validation_split,
        status_callback=status_callback,
    )

    if status_callback:
        status_callback("📈 Computing accuracy metrics from confusion matrix...")
    metrics_df, cm_array, oa, kappa = get_accuracy_metrics(cm_ee, class_names)

    if status_callback:
        status_callback("📐 Computing per-class area statistics...")
    area_df = get_area_statistics(classified, aoi, class_names)

    return {
        'classified_ee':    classified,
        'feature_stack':    feature_stack,
        'metrics_df':       metrics_df,
        'area_df':          area_df,
        'cm_array':         cm_array,
        'overall_accuracy': oa,
        'kappa':            kappa,
        'aoi':              aoi,
    }


# ─── GeoTIFF download helper ──────────────────────────────────────────────────
def download_classified_tif(classified_ee, aoi, scale=10, timeout=300):
    """
    Download the classified GeoTIFF from EE as bytes.
    Returns bytes or None on failure.
    """
    import requests, zipfile, io as _io

    try:
        url = classified_ee.getDownloadUrl({
            'region':      aoi,
            'scale':       scale,
            'filePerBand': False,
            'format':      'GEO_TIFF',
        })
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        # EE sometimes returns a zip
        ct = resp.headers.get('content-type', '')
        if 'zip' in ct or url.endswith('.zip'):
            with zipfile.ZipFile(_io.BytesIO(resp.content)) as z:
                tifs = [f for f in z.namelist() if f.endswith('.tif')]
                if tifs:
                    return z.read(tifs[0])
        return resp.content
    except Exception as e:
        return None
