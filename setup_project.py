"""
Interactive Earth Engine Project Setup
"""
import subprocess
import os
import sys

print("=" * 70)
print("🌍 EARTH ENGINE PROJECT SETUP")
print("=" * 70)
print()
print("✅ You've successfully authenticated!")
print()
print("Now we need to set your Google Cloud Project ID.")
print()
print("=" * 70)
print("📋 HOW TO GET YOUR PROJECT ID:")
print("=" * 70)
print()
print("1. Open: https://console.cloud.google.com/")
print()
print("2. Look at the top of the page - you'll see a dropdown showing your")
print("   current project name with a PROJECT ID below it")
print()
print("3. If you don't have a project:")
print("   - Click 'Select a project' → 'New Project'")
print("   - Give it a name (e.g., 'earth-engine-project')")
print("   - Click 'Create'")
print("   - Copy the Project ID (not the name!)")
print()
print("4. Enable Earth Engine API:")
print("   - Go to: https://console.cloud.google.com/apis/library/earthengine.googleapis.com")
print("   - Click 'Enable'")
print()
print("=" * 70)
print()

project_id = input("Enter your Google Cloud Project ID: ").strip()

if not project_id:
    print("\n❌ No project ID entered. Please try again.")
    sys.exit(1)

print()
print(f"Setting project to: {project_id}")
print()

# Set environment variable for current session
os.environ['EARTHENGINE_PROJECT'] = project_id
print("✅ Environment variable set for current session")
print()

# Test the initialization
print("Testing Earth Engine connection...")
try:
    import ee
    ee.Initialize(project=project_id)
    print()
    print("=" * 70)
    print("🎉 SUCCESS! Earth Engine is now configured!")
    print("=" * 70)
    print()
    print("To make this permanent, run this command in PowerShell:")
    print()
    print(f'    setx EARTHENGINE_PROJECT "{project_id}"')
    print()
    print("Then restart your terminal and Streamlit app.")
    print("=" * 70)
except Exception as e:
    print()
    print("=" * 70)
    print("❌ Error initializing Earth Engine:")
    print(f"   {e}")
    print()
    print("Please check:")
    print("1. Your project ID is correct")
    print("2. You've enabled Earth Engine API for this project")
    print("3. You have Earth Engine access (sign up at earthengine.google.com)")
    print("=" * 70)
    sys.exit(1)
