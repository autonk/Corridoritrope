import bpy

def rename_vertex_colors_to_printcolor():
    selected_objects = bpy.context.selected_objects
    
    if not selected_objects:
        print("No objects selected.")
        return
        
    count = 0
    for obj in selected_objects:
        if obj.type == 'MESH':
            mesh = obj.data
            
            # Handle Blender 3.2+ Color Attributes
            if hasattr(mesh, 'color_attributes') and mesh.color_attributes:
                # Use the active color or the first one if none is active
                target_color = mesh.color_attributes.active_color or mesh.color_attributes[0]
                if target_color and target_color.name != "PRINTCOLOR":
                    print(f"[{obj.name}] Renaming Color Attribute '{target_color.name}' to 'PRINTCOLOR'")
                    target_color.name = "PRINTCOLOR"
                    count += 1
                    
            # Handle pre-3.2 Vertex Colors
            elif hasattr(mesh, 'vertex_colors') and mesh.vertex_colors:
                target_color = mesh.vertex_colors.active or mesh.vertex_colors[0]
                if target_color and target_color.name != "PRINTCOLOR":
                    print(f"[{obj.name}] Renaming Vertex Color '{target_color.name}' to 'PRINTCOLOR'")
                    target_color.name = "PRINTCOLOR"
                    count += 1

    print(f"Successfully renamed vertex colors on {count} objects to 'PRINTCOLOR'.")

if __name__ == "__main__":
    rename_vertex_colors_to_printcolor()
