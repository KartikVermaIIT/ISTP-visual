"""
Test Earth Engine with project ID
"""
import os
import ee

# Set project ID
project_id = 'istp-489219'
os.environ['EARTHENGINE_PROJECT'] = project_id

print("=" * 70)
print("🌍 Testing Earth Engine Connection")
print("=" * 70)
print(f"\nProject ID: {project_id}")
print("\nInitializing Earth Engine...")

try:
    ee.Initialize(project=project_id)
    print("\n✅ SUCCESS! Earth Engine is connected!")
    print()
    print("=" * 70)
    print("🎉 You're all set!")
    print("=" * 70)
    print()
    print("Your Streamlit app can now use Earth Engine.")
    print()
    
    # Test a simple EE operation
    print("Testing EE operation...")
    test_image = ee.Image('COPERNICUS/S2_SR/20190101T000000_20190101T000000_T10SEG')
    print(f"✅ Successfully accessed Sentinel-2 image")
    print()
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print()
    if 'Earth Engine not enabled' in str(e) or 'API has not been used' in str(e):
        print("You need to enable the Earth Engine API:")
        print()
        print(f"1. Go to: https://console.cloud.google.com/apis/library/earthengine.googleapis.com?project={project_id}")
        print("2. Click 'ENABLE'")
        print("3. Wait a minute, then try again")
    elif 'not registered' in str(e).lower():
        print("You need to register for Earth Engine:")
        print()
        print("1. Go to: https://earthengine.google.com/signup/")
        print("2. Sign up with your Google account")
        print("3. Wait for approval (usually instant for Cloud projects)")
    print()

print("=" * 70)
