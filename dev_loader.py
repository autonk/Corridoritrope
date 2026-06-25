import sys
import os
import bpy
import importlib

# Absolute path to the ADDON directory
addon_dir = r"v:\01 PROJECTS\02 CORRIDOR CREW\01 Episodes\2026\01_JANUARY\01.05.2026_ZOETROPE\02_VFX\06_BLENDER\ZOETROPE PROJECT\ADDON"

print("-" * 40)
print("Starting Dev Loader...")

# Add the addon directory to sys.path so Python can find 'zoetrope_extension'
if addon_dir not in sys.path:
    sys.path.append(addon_dir)

# Import the addon package
import zoetrope_extension

# Try to unregister the existing version if it's already loaded
if hasattr(zoetrope_extension, "unregister"):
    try:
        zoetrope_extension.unregister()
        print("Unregistered existing zoetrope_extension.")
    except Exception as e:
        print(f"Could not unregister: {e}")

# Force reload the module so it reads the latest changes from disk
importlib.reload(zoetrope_extension)
print("Reloaded module from disk.")

# Register the updated module
if hasattr(zoetrope_extension, "register"):
    zoetrope_extension.register()
    print("Registered zoetrope_extension.")

print("Dev Load Complete! Extension is running directly from your source files.")
print("-" * 40)
