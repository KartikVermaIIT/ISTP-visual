"""
Authenticate Google Earth Engine
"""
import ee

print("Starting Google Earth Engine authentication...")
print("This will open a browser window for you to log in.")
print()

try:
    ee.Authenticate()
    print("\n✅ Authentication successful!")
    print("Now initializing Earth Engine...")
    ee.Initialize()
    print("✅ Earth Engine initialized successfully!")
except Exception as e:
    print(f"\n❌ Authentication failed: {e}")
    print("\nPlease try the following:")
    print("1. Make sure you have a Google account")
    print("2. Sign up for Earth Engine at: https://earthengine.google.com/signup/")
