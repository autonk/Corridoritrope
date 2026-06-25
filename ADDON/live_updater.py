import bpy
import os
import zipfile

# Absolute path to the ADDON directory
addon_dir = r"v:\01 PROJECTS\02 CORRIDOR CREW\01 Episodes\2026\01_JANUARY\01.05.2026_ZOETROPE\02_VFX\06_BLENDER\ZOETROPE PROJECT\ADDON"

# Paths
addon_zip = os.path.join(addon_dir, "zoetrope_generator_addon.zip")
addon_py = os.path.join(addon_dir, "zoetrope_generator_addon.py")
ext_dir = os.path.join(addon_dir, "zoetrope_extension")
ext_zip = os.path.join(addon_dir, "zoetrope_extension.zip")

print("-" * 40)
print("Starting Live Update...")

# 1. Zip the single-file Addon
with zipfile.ZipFile(addon_zip, 'w', zipfile.ZIP_DEFLATED) as z:
    z.write(addon_py, arcname="zoetrope_generator_addon.py")
print(f"Zipped: {os.path.basename(addon_zip)}")

# 2. Zip the Extension
with zipfile.ZipFile(ext_zip, 'w', zipfile.ZIP_DEFLATED) as z:
    for root, dirs, files in os.walk(ext_dir):
        for file in files:
            file_path = os.path.join(root, file)
            # The archive name should be relative to the ext_dir so it sits at the root of the zip
            arcname = os.path.relpath(file_path, ext_dir)
            z.write(file_path, arcname=arcname)
print(f"Zipped: {os.path.basename(ext_zip)}")

# 3. Re-install the Addon in Blender
module_name = "zoetrope_generator_addon"

# Disable if currently enabled
if module_name in bpy.context.preferences.addons:
    bpy.ops.preferences.addon_disable(module=module_name)
    print("Disabled existing addon.")

# Force Python to un-cache the module so it reads the new file
import sys
if module_name in sys.modules:
    del sys.modules[module_name]

# Install the updated zip (overwrite=True ensures it replaces the old one)
bpy.ops.preferences.addon_install(filepath=addon_zip, overwrite=True)
print("Installed updated addon.")

# Re-enable the addon
bpy.ops.preferences.addon_enable(module=module_name)
print("Enabled updated addon.")

print("Live Update Complete! You can now test your changes.")
print("-" * 40)
