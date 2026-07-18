bl_info = {
    "name": "Zoetrope Tools (Auto-Updating)",
    "author": "Corridor Crew",
    "version": (1, 2, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Zoetrope",
    "description": "Auto-updating toolkit for Zoetrope Generation",
    "category": "Object",
}

import bpy
import urllib.request
import urllib.error
import os
import sys
import importlib
import json
import base64
import threading
from datetime import datetime

# ========================================================================
# SETTINGS - CHANGE THESE BEFORE DISTRIBUTING
# ========================================================================
GITHUB_USER = "CorridorCrew"
GITHUB_REPO = "Zoetrope_Tools"
GITHUB_BRANCH = "main"
GITHUB_FILE_PATH = "ADDON/zoetrope_generator_addon.py"

# Leave empty for public repos (requests go unauthenticated). Only paste a
# token here if the repo is private - and never commit a real token.
GITHUB_TOKEN = ""
CORE_MODULE_NAME = "zoetrope_generator_addon"
# ========================================================================

# Global state for background checker
remote_info = {
    'checked': False,
    'has_update': False,
    'sha': None,
    'date': None
}

def get_addon_dir():
    return os.path.dirname(os.path.realpath(__file__))

def get_core_path():
    return os.path.join(get_addon_dir(), CORE_MODULE_NAME + ".py")

def get_metadata_path():
    return os.path.join(get_addon_dir(), CORE_MODULE_NAME + "_meta.json")

def get_local_meta():
    path = get_metadata_path()
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {'sha': None, 'date': None}

def save_local_meta(sha, date_str):
    try:
        with open(get_metadata_path(), 'w', encoding='utf-8') as f:
            json.dump({'sha': sha, 'date': date_str}, f)
    except Exception as e:
        print(f"[Zoetrope Auto-Updater] Failed to save metadata: {e}")

def get_github_headers():
    headers = {
        'User-Agent': 'Mozilla/5.0 Blender Addon Updater',
        'Accept': 'application/vnd.github.v3+json'
    }
    if GITHUB_TOKEN and "XXXXX" not in GITHUB_TOKEN:
        headers['Authorization'] = f"Bearer {GITHUB_TOKEN}"
    return headers

def format_date(iso_str):
    if not iso_str: return "Unknown"
    try:
        # e.g., 2026-06-05T00:27:00Z
        dt = datetime.strptime(iso_str.replace("Z", ""), "%Y-%m-%dT%H:%M:%S")
        return dt.strftime("%b %d, %Y - %H:%M")
    except:
        return iso_str

def background_check_thread():
    """Runs in the background so it doesn't freeze Blender."""
    global remote_info
    
    # 1. Hit the commits API to get the latest commit for the file
    commits_url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/commits?path={GITHUB_FILE_PATH}&sha={GITHUB_BRANCH}&per_page=1"
    
    try:
        req = urllib.request.Request(commits_url, headers=get_github_headers())
        with urllib.request.urlopen(req) as response:
            commits = json.loads(response.read().decode('utf-8'))
            
        if commits:
            latest = commits[0]
            remote_sha = latest.get('sha')
            remote_date = latest.get('commit', {}).get('author', {}).get('date')
            
            local_meta = get_local_meta()
            local_sha = local_meta.get('sha')
            
            remote_info['sha'] = remote_sha
            remote_info['date'] = remote_date
            remote_info['has_update'] = (remote_sha != local_sha and local_sha is not None)
            remote_info['checked'] = True
            
    except Exception as e:
        print(f"[Zoetrope Auto-Updater] Background check failed: {e}")

def start_background_check():
    t = threading.Thread(target=background_check_thread)
    t.daemon = True
    t.start()

def force_download_update():
    """Downloads the actual file content synchronously. Called only when the user clicks 'Update'."""
    # We still need the commits API to get the latest SHA/date reliably, then we fetch raw file
    commits_url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/commits?path={GITHUB_FILE_PATH}&sha={GITHUB_BRANCH}&per_page=1"
    content_url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}?ref={GITHUB_BRANCH}"
    
    headers = get_github_headers()
    
    try:
        # Get SHA and Date
        req_c = urllib.request.Request(commits_url, headers=headers)
        with urllib.request.urlopen(req_c) as response:
            commits = json.loads(response.read().decode('utf-8'))
        
        if not commits:
            return False, "No commits found for file."
            
        remote_sha = commits[0].get('sha')
        remote_date = commits[0].get('commit', {}).get('author', {}).get('date')
        
        local_meta = get_local_meta()
        if remote_sha == local_meta.get('sha') and os.path.exists(get_core_path()):
            return True, "Already up to date."
            
        # Download Content
        req_f = urllib.request.Request(content_url, headers=headers)
        with urllib.request.urlopen(req_f) as response:
            data = json.loads(response.read().decode('utf-8'))
            
        content_b64 = data.get('content', '')
        if not content_b64:
            return False, "File content empty."
            
        code = base64.b64decode(content_b64).decode('utf-8')
        with open(get_core_path(), 'w', encoding='utf-8') as f:
            f.write(code)
            
        save_local_meta(remote_sha, remote_date)
        
        # Reset background check status
        remote_info['has_update'] = False
        return True, "Update successful."
        
    except Exception as e:
        return False, str(e)

class ZOETROPE_OT_update_core(bpy.types.Operator):
    bl_idname = "zoetrope.update_core"
    bl_label = "Update Now"
    bl_description = "Downloads and applies the latest update"
    
    def execute(self, context):
        global core_module
        
        success, msg = force_download_update()
        
        if not success:
            self.report({'ERROR'}, f"Update failed: {msg}")
            return {'CANCELLED'}
            
        # Reload module
        if core_module and hasattr(core_module, 'unregister'):
            try:
                core_module.unregister()
            except Exception:
                pass
                
        try:
            addon_dir = get_addon_dir()
            if addon_dir not in sys.path:
                sys.path.append(addon_dir)
                
            core_module = importlib.import_module(CORE_MODULE_NAME)
            importlib.reload(core_module)
            
            if hasattr(core_module, 'register'):
                core_module.register()
                
            self.report({'INFO'}, "Successfully updated to the latest commit!")
            
            # Restart the background checker to refresh UI
            start_background_check()
        except Exception as e:
            self.report({'ERROR'}, f"Module load failed: {e}")
            return {'CANCELLED'}
            
        return {'FINISHED'}

class ZOETROPE_PT_updater_panel(bpy.types.Panel):
    bl_label = "Zoetrope Updater"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Zoetrope'
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        local_meta = get_local_meta()
        
        # Current Version Box
        box = layout.box()
        box.label(text="Current Version:", icon='FILE_TICK')
        col = box.column(align=True)
        
        if local_meta.get('sha'):
            col.label(text=f"Commit: {local_meta['sha'][:7]}")
            col.label(text=f"Date: {format_date(local_meta['date'])}")
        else:
            col.label(text="Status: Core Script Missing")
            
        # Remote Update Status
        if remote_info['checked']:
            if remote_info['has_update']:
                warn_box = layout.box()
                warn_box.label(text="⚠️ Update Available!", icon='ERROR')
                wcol = warn_box.column(align=True)
                wcol.label(text=f"New Commit: {remote_info['sha'][:7]}")
                wcol.label(text=f"New Date: {format_date(remote_info['date'])}")
                layout.separator()
                layout.operator("zoetrope.update_core", icon='IMPORT', text="Download & Apply Update")
            else:
                layout.separator()
                layout.label(text="You are on the latest version.", icon='CHECKMARK')
                layout.operator("zoetrope.update_core", icon='FILE_REFRESH', text="Force Re-download")
        else:
            layout.separator()
            layout.label(text="Checking GitHub for updates...", icon='TIME')
            layout.operator("zoetrope.update_core", icon='FILE_REFRESH', text="Manual Update")

classes = (
    ZOETROPE_OT_update_core,
    ZOETROPE_PT_updater_panel
)

core_module = None

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    global core_module
    addon_dir = get_addon_dir()
    if addon_dir not in sys.path:
        sys.path.append(addon_dir)
        
    core_path = get_core_path()
    
    if not os.path.exists(core_path):
        print("[Zoetrope Auto-Updater] Core missing, downloading...")
        force_download_update()
        
    if os.path.exists(core_path):
        try:
            core_module = importlib.import_module(CORE_MODULE_NAME)
            if hasattr(core_module, 'register'):
                core_module.register()
        except Exception as e:
            print(f"[Zoetrope Auto-Updater] Failed to register core: {e}")
            
    # Start the async background checker 3 seconds after registration
    bpy.app.timers.register(start_background_check, first_interval=3.0)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
    global core_module
    if core_module and hasattr(core_module, 'unregister'):
        try:
            core_module.unregister()
        except Exception:
            pass

if __name__ == "__main__":
    register()
