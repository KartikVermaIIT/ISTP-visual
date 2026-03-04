"""
Check and set up Earth Engine project
"""
import subprocess
import sys

print("=" * 60)
print("Google Earth Engine Project Setup")
print("=" * 60)
print()

print("Checking your Earth Engine configuration...")
print()

# Try to get current project
result = subprocess.run(
    ["earthengine", "project", "list"],
    capture_output=True,
    text=True
)

if result.returncode == 0 and result.stdout.strip():
    print("✅ Available Earth Engine projects:")
    print(result.stdout)
    print()
    print("To set a default project, run:")
    print("  earthengine set_project YOUR-PROJECT-ID")
else:
    print("No Earth Engine projects found or earthengine CLI not available.")
    print()
    print("📌 Steps to set up:")
    print()
    print("1. Go to Google Cloud Console: https://console.cloud.google.com/")
    print("2. Create a new project or select an existing one")
    print("3. Enable Earth Engine API for your project")
    print("4. Note your project ID (visible in the project selector)")
    print()
    print("5. Then run one of these commands:")
    print("   a) Set default project:")
    print("      earthengine set_project YOUR-PROJECT-ID")
    print()
    print("   b) Or set environment variable (Windows PowerShell):")
    print("      $env:EARTHENGINE_PROJECT='YOUR-PROJECT-ID'")
    print()
    print("   c) Or set permanently in Windows:")
    print("      setx EARTHENGINE_PROJECT \"YOUR-PROJECT-ID\"")
    print()

print("=" * 60)
