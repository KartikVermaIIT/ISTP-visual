"""
Check Earth Engine username and account info
"""
import os
import ee

os.environ['EARTHENGINE_PROJECT'] = 'istp-489219'

try:
    ee.Initialize(project='istp-489219')
    
    print("=" * 70)
    print("EARTH ENGINE ACCOUNT INFORMATION")
    print("=" * 70)
    print()
    
    # Get root assets folder
    try:
        root_folder = ee.data.getAssetRoots()
        print("📁 Your Asset Roots:")
        for folder in root_folder:
            print(f"   {folder['id']}")
            
            # Extract username from asset root
            if 'users/' in folder['id']:
                username = folder['id'].replace('projects/earthengine-legacy/assets/users/', '')
                print()
                print(f"👤 Your EE Username: {username}")
                print()
                print(f"📝 Use this in the app: {username}")
    except Exception as e:
        print(f"Could not get asset roots: {e}")
    
    print()
    print("=" * 70)
    print("PROJECT INFORMATION")
    print("=" * 70)
    print()
    print(f"🔑 Project ID: istp-489219")
    print()
    
    # Try to list assets
    print("Checking your assets folder...")
    try:
        # Try to list assets in users folder
        assets = ee.data.listAssets({'parent': 'projects/earthengine-legacy/assets/users'})
        print(f"Found {len(assets.get('assets', []))} assets")
    except:
        print("Note: You may not have created any assets yet")
    
    print()
    print("=" * 70)
    
except Exception as e:
    print(f"Error: {e}")
