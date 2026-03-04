"""
Quick test to verify folium and Earth Engine work in Streamlit
"""
import streamlit as st
import os
from streamlit_folium import folium_static
import folium

st.title("🗺️ Earth Engine Map Test")

# Set project ID
os.environ['EARTHENGINE_PROJECT'] = 'istp-489219'

try:
    import ee
    
    st.success("✅ Imports successful!")
    
    # Initialize EE
    ee.Initialize(project='istp-489219')
    st.success("✅ Earth Engine initialized!")
    
    # Create folium map
    st.markdown("### Creating map with folium...")
    
    m = folium.Map(location=[37.7, -122.4], zoom_start=10, width='100%', height='600px')
    
    st.success("✅ Map object created!")
    
    # Add Earth Engine layer
    st.markdown("### Adding Earth Engine data...")
    
    # Create a simple EE geometry
    aoi = ee.Geometry.Point([-122.4, 37.7]).buffer(10000)
    
    # Get Sentinel-2 image
    s2 = ee.ImageCollection('COPERNICUS/S2_SR') \
        .filterBounds(aoi) \
        .filterDate('2023-06-01', '2023-09-30') \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
        .first()
    
    if s2:
        # Get the tile URL for visualization
        vis_params = {
            'min': 0,
            'max': 3000,
            'bands': ['B4', 'B3', 'B2']
        }
        
        map_id_dict = ee.Image(s2).getMapId(vis_params)
        
        # Add tile layer to folium
        folium.TileLayer(
            tiles=map_id_dict['tile_fetcher'].url_format,
            attr='Google Earth Engine',
            name='Sentinel-2 RGB',
            overlay=True,
            control=True
        ).add_to(m)
        
        st.success("✅ Earth Engine layer added!")
    else:
        st.warning("⚠️ No Sentinel-2 imagery found for this area/date")
    
    # Add a marker
    folium.Marker(
        [37.7, -122.4],
        popup='San Francisco Bay Area',
        tooltip='Click me!',
        icon=folium.Icon(color='red', icon='info-sign')
    ).add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    st.success("✅ Map configured!")
    
    # Display the map
    st.markdown("### 🗺️ Map Display:")
    
    folium_static(m, width=1200, height=600)
    
    st.success("✅ Map displayed successfully!")
    
    st.markdown("---")
    st.markdown("### 🎉 Success!")
    st.info("If you can see the map above with OpenStreetMap basemap and a red marker, then maps are working!")
    
except Exception as e:
    st.error(f"❌ Error: {e}")
    import traceback
    st.code(traceback.format_exc())
