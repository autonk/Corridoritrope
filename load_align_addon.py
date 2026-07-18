import sys
import os
import importlib
import bpy

# Define the path where the addon script is located
addon_path = r"v:\01 PROJECTS\02 CORRIDOR CREW\01 Episodes\2026\01_JANUARY\01.05.2026_ZOETROPE\02_VFX\06_BLENDER\ZOETROPE PROJECT"

# Add it to sys.path so Blender can find the module
if addon_path not in sys.path:
    sys.path.append(addon_path)

# Try to unregister the old module if it exists (for hot-reloading)
if "align_to_z_addon" in sys.modules:
    try:
        importlib.reload(sys.modules["align_to_z_addon"])
        sys.modules["align_to_z_addon"].unregister()
    except Exception:
        pass

# Import the module
import align_to_z_addon

# Reload it to guarantee we have the latest version from disk
importlib.reload(align_to_z_addon)

# Register the classes
align_to_z_addon.register()

print("Successfully loaded and registered 'Align to Z' from external disk path!")
