"""
Clear Streamlit cache and restart application
"""
import os
import shutil
import subprocess
import sys

def clear_streamlit_cache():
    """Clear all Streamlit cache directories"""
    cache_paths = [
        '.streamlit/cache',
        os.path.expanduser('~/.streamlit/cache'),
        os.path.expanduser('~\\AppData\\Local\\streamlit\\cache'),
        os.path.expanduser('~\\AppData\\Roaming\\streamlit\\cache')
    ]
    
    print("🧹 Clearing Streamlit cache...")
    for cache_path in cache_paths:
        if os.path.exists(cache_path):
            try:
                shutil.rmtree(cache_path)
                print(f"  ✓ Cleared: {cache_path}")
            except Exception as e:
                print(f"  ⚠ Could not clear {cache_path}: {e}")
    
    print("\n✅ Cache clearing complete!")
    print("\n📝 Next steps:")
    print("1. Close all browser tabs with the Streamlit app")
    print("2. Run: streamlit run streamlit_app.py")
    print("3. Press Ctrl+Shift+R in your browser to hard refresh")

if __name__ == "__main__":
    clear_streamlit_cache()
