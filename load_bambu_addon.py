import sys
import bpy

def load_addon():
    # The parent directory of the 'vertex_color_tool' package
    addon_dir = r"c:\Users\Corridor\Documents\Projects\VertexColorBambu\BambuVertex_Autonk"
    
    # 1. Unregister the currently loaded module if it exists
    if "vertex_color_tool" in sys.modules:
        try:
            sys.modules["vertex_color_tool"].unregister()
        except Exception:
            pass

    # 2. Nuke ALL loaded submodules from memory
    modules_to_delete = [m for m in sys.modules if m.startswith("vertex_color_tool")]
    for m in modules_to_delete:
        del sys.modules[m]

    # 3. Force Python to check our source folder first
    if addon_dir in sys.path:
        sys.path.remove(addon_dir)
    sys.path.insert(0, addon_dir)

    # 4. Import completely fresh and register!
    import vertex_color_tool
    vertex_color_tool.register()
    
    print(f"BambuVertex addon NUKED and reloaded fresh from: {vertex_color_tool.__file__}")

if __name__ == "__main__":
    load_addon()
