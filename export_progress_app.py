import customtkinter as ctk
from tkinter import filedialog
import subprocess
import threading
import os
import re

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class ZoetropeExporterApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Zoetrope High-Poly Exporter")
        self.geometry("500x350")
        
        self.blend_path = ctk.StringVar()
        self.out_dir = ctk.StringVar()
        
        # UI Layout
        self.title_label = ctk.CTkLabel(self, text="Zoetrope Frame Exporter", font=ctk.CTkFont(size=20, weight="bold"))
        self.title_label.pack(pady=(20, 10))
        
        # Blend File Selection
        self.blend_frame = ctk.CTkFrame(self)
        self.blend_frame.pack(fill="x", padx=20, pady=10)
        
        self.blend_entry = ctk.CTkEntry(self.blend_frame, textvariable=self.blend_path, placeholder_text="Select .blend file...")
        self.blend_entry.pack(side="left", fill="x", expand=True, padx=(10, 10), pady=10)
        
        self.blend_btn = ctk.CTkButton(self.blend_frame, text="Browse", width=80, command=self.browse_blend)
        self.blend_btn.pack(side="right", padx=(0, 10), pady=10)
        
        # Output Directory Selection
        self.out_frame = ctk.CTkFrame(self)
        self.out_frame.pack(fill="x", padx=20, pady=10)
        
        self.out_entry = ctk.CTkEntry(self.out_frame, textvariable=self.out_dir, placeholder_text="Select output folder...")
        self.out_entry.pack(side="left", fill="x", expand=True, padx=(10, 10), pady=10)
        
        self.out_btn = ctk.CTkButton(self.out_frame, text="Browse", width=80, command=self.browse_out)
        self.out_btn.pack(side="right", padx=(0, 10), pady=10)
        
        # Options
        self.skip_frame_var = ctk.BooleanVar(value=False)
        self.skip_frame_cb = ctk.CTkCheckBox(self, text="Skip Every Other Frame", variable=self.skip_frame_var)
        self.skip_frame_cb.pack(pady=(0, 10))
        
        # Progress and Status
        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.pack(fill="x", padx=20, pady=(20, 5))
        self.progress_bar.set(0)
        
        self.status_label = ctk.CTkLabel(self, text="Ready", text_color="gray")
        self.status_label.pack(pady=0)
        
        # Start Button
        self.start_btn = ctk.CTkButton(self, text="Start Export", font=ctk.CTkFont(size=14, weight="bold"), command=self.start_export)
        self.start_btn.pack(pady=20)
        
    def browse_blend(self):
        filepath = filedialog.askopenfilename(title="Select Blend File", filetypes=[("Blender Files", "*.blend")])
        if filepath:
            self.blend_path.set(filepath)
            
    def browse_out(self):
        dirpath = filedialog.askdirectory(title="Select Output Folder")
        if dirpath:
            self.out_dir.set(dirpath)
            
    def start_export(self):
        blend = self.blend_path.get()
        out = self.out_dir.get()
        
        if not blend or not os.path.exists(blend):
            self.status_label.configure(text="Error: Valid .blend file required.", text_color="red")
            return
            
        if not out or not os.path.exists(out):
            self.status_label.configure(text="Error: Valid output directory required.", text_color="red")
            return
            
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zoetrope_export_headless.py")
        if not os.path.exists(script_path):
            self.status_label.configure(text="Error: Cannot find headless script.", text_color="red")
            return

        self.start_btn.configure(state="disabled")
        self.status_label.configure(text="Starting Blender...", text_color="white")
        self.progress_bar.set(0)
        
        skip = self.skip_frame_var.get()
        
        # Run in a background thread so UI doesn't freeze
        threading.Thread(target=self.run_blender_process, args=(blend, script_path, out, skip), daemon=True).start()
        
    def run_blender_process(self, blend, script, out, skip):
        try:
            # Assuming blender is in the system PATH. 
            # If not, users might need to specify the full path to blender.exe
            cmd = ["blender", "-b", blend, "--python", script, "--", out]
            if skip:
                cmd.append("--skip-every-other")
            
            # On windows, we might want to hide the console window creation for subprocess
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                text=True,
                startupinfo=startupinfo
            )
            
            # Read stdout line by line
            regex = re.compile(r"PROGRESS:\s+(\d+)/(\d+)")
            for line in process.stdout:
                line = line.strip()
                if not line:
                    continue
                    
                match = regex.search(line)
                if match:
                    current = int(match.group(1))
                    total = int(match.group(2))
                    if total > 0:
                        progress = current / total
                        # Use after() to update UI from background thread safely
                        self.after(0, self.update_progress, progress, f"Exporting: {current} / {total} frames")
                        
            process.wait()
            
            if process.returncode == 0:
                self.after(0, self.finish_export, True, "Export Complete!")
            else:
                self.after(0, self.finish_export, False, "Export Failed. Check console.")
                
        except FileNotFoundError:
            # Blender not in PATH
            self.after(0, self.finish_export, False, "Error: 'blender' not found in PATH.")
        except Exception as e:
            self.after(0, self.finish_export, False, f"Error: {str(e)}")
            
    def update_progress(self, val, text):
        self.progress_bar.set(val)
        self.status_label.configure(text=text, text_color="white")
        
    def finish_export(self, success, text):
        self.start_btn.configure(state="normal")
        self.status_label.configure(text=text, text_color="green" if success else "red")
        if success:
            self.progress_bar.set(1.0)

if __name__ == "__main__":
    app = ZoetropeExporterApp()
    app.mainloop()
