# ==============================================================================
#  GAMING LAN MANAGER - MIDNIGHT OBSIDIAN (UI Fixed Edition)
#  ------------------------------------------------------------------------------
#  - Elastic layout with fixed button areas and a scrollable friend list that expands properly.
#  - ADDED: Scrollbar auto-appears only when needed.
#  - Enhanced dark theme with consistent colors and better spacing.
#  - Enhanced dark dialogs with icons, better text wrapping, and improved button layouts.
#  - Added port change and manual IP update features with user-friendly dialogs.
#  - VERSION: 2026.41
# ==============================================================================

import tkinter as tk
from tkinter import filedialog
import subprocess
import json
import os
import urllib.request
import ipaddress
import threading
import sys
import time
import ctypes 
import re 
from datetime import datetime

# --- CONFIGURATION ---
APP_TITLE = "Gaming Lan Manager"
VERSION = "2026.41"
CREDITS = """
Lead Developer: SovereignBit
Co-Pilot: Gemini AI (Google)
"""
DEFAULT_PORT = 52392 
BASE_SUBNET = "10.100.0.0/24"

# --- DARK THEME PALETTE ---
C_BG_MAIN = "#121212"       
C_BG_PANEL = "#1E1E1E"      
C_BG_POPUP = "#252526"      
C_TXT_MAIN = "#E0E0E0"      
C_TXT_DIM = "#A0A0A0"       
C_ACCENT_ORN = "#D35400"    
C_ACCENT_RED = "#C0392B"    
C_ACCENT_GRN = "#27AE60"    
C_ACCENT_PUR = "#8E44AD"    
C_ACCENT_BLU = "#2980B9"    
C_BTN_BG = "#2D2D30"        
C_OFFLINE = "#505050"       
C_INPUT_BG = "#333333"      

# --- PATH CONFIG ---
if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
    def resource_path(relative):
        try: return os.path.join(sys._MEIPASS, relative)
        except: return os.path.join(os.path.abspath("."), relative)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    def resource_path(relative): return os.path.join(APP_DIR, relative)

DEFAULT_DB = os.path.join(APP_DIR, "vpn_data.json")
SETTINGS_FILE = os.path.join(APP_DIR, "app_config.json")
CONFIG_DIR = os.path.join(APP_DIR, "Friend_Configs")
HOST_CONF = os.path.join(APP_DIR, "HOST_THIS_PC.conf")

# --- FALLBACK ICON ---
ICON_DATA = """
R0lGODlhIAAgAOMAAAAAAIB/f4uLi5ubm6Ghoaampra2tsfHx87Ozt7e3ufn5+/v7/f39////////////
yH+EUNyZWF0ZWQgd2l0aCBHSU1QACwAAAAAIAAgAAAEaHDISau9OOvNu/9gKI5kaZ5oqq5s675wLM90bd
94ru987//AoHBILBqPyKRyyWw6n9CodEqtWq/YrHbL7Xq/4LB4TC6bz+i0es1uu9/wuHxOr9vv+Lx+z+/
7/4CBgoOEhYaHiImKi4yNjo+QkZFMADs=
"""

# --- FONTS ---
FONT_HEADER = ("Segoe UI", 16, "bold")
FONT_BODY = ("Segoe UI", 10)
FONT_MONO = ("Consolas", 10)

# --- CUSTOM DARK DIALOGS ---
class DarkDialog(tk.Toplevel):
    def __init__(self, parent, title, message, style="info", is_input=False, default_val=""):
        super().__init__(parent)
        self.result = None
        self.is_input = is_input
        
        self.configure(bg=C_BG_POPUP)
        self.title(title)
        self.geometry("420x220")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        x = parent.winfo_x() + (parent.winfo_width() // 2) - 210
        y = parent.winfo_y() + (parent.winfo_height() // 2) - 110
        self.geometry(f"+{x}+{y}")

        self.after(10, lambda: self.darken_hwnd())

        main_frame = tk.Frame(self, bg=C_BG_POPUP, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)

        icon_char = "ℹ"
        icon_col = C_TXT_MAIN
        if style == "error": icon_char = "⚠️"; icon_col = C_ACCENT_RED
        elif style == "question": icon_char = "?"; icon_col = C_ACCENT_ORN
        
        tk.Label(main_frame, text=icon_char, font=("Arial", 28), bg=C_BG_POPUP, fg=icon_col).pack(side="left", anchor="n", padx=(0, 15))

        content_area = tk.Frame(main_frame, bg=C_BG_POPUP)
        content_area.pack(side="left", fill="both", expand=True)

        tk.Label(content_area, text=message, font=FONT_BODY, bg=C_BG_POPUP, fg=C_TXT_MAIN, wraplength=300, justify="left").pack(anchor="w", pady=(5, 10))

        if self.is_input:
            self.entry = tk.Entry(content_area, bg=C_INPUT_BG, fg="white", font=("Segoe UI", 11), insertbackground="white", relief="flat")
            self.entry.pack(fill="x", pady=5, ipady=3)
            self.entry.insert(0, default_val)
            self.entry.focus_set()
            self.entry.bind("<Return>", lambda e: self.on_ok())

        btn_frame = tk.Frame(self, bg=C_BG_POPUP, pady=15)
        btn_frame.pack(fill="x", side="bottom")

        if style == "question":
            tk.Button(btn_frame, text="Yes", bg=C_ACCENT_GRN, fg="white", font=("Segoe UI", 9, "bold"), relief="flat", width=10, command=self.on_ok).pack(side="right", padx=20)
            tk.Button(btn_frame, text="No", bg=C_BTN_BG, fg="white", font=("Segoe UI", 9), relief="flat", width=10, command=self.on_close).pack(side="right")
        elif style == "error":
             tk.Button(btn_frame, text="Close", bg=C_ACCENT_RED, fg="white", font=("Segoe UI", 9, "bold"), relief="flat", width=10, command=self.on_close).pack(side="bottom")
        else:
            tk.Button(btn_frame, text="OK", bg=C_ACCENT_BLU, fg="white", font=("Segoe UI", 9, "bold"), relief="flat", width=10, command=self.on_ok).pack(side="bottom")

    def darken_hwnd(self):
        try:
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            value = ctypes.c_int(1)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(value), 4)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 19, ctypes.byref(value), 4)
        except: pass

    def on_ok(self):
        if self.is_input: self.result = self.entry.get()
        else: self.result = True
        self.destroy()

    def on_close(self):
        self.result = None
        self.destroy()

def show_dark_info(parent, title, msg): DarkDialog(parent, title, msg, "info")
def show_dark_error(parent, title, msg): DarkDialog(parent, title, msg, "error")
def ask_dark_yesno(parent, title, msg): 
    d = DarkDialog(parent, title, msg, "question")
    parent.wait_window(d)
    return d.result
def ask_dark_string(parent, title, msg, default=""):
    d = DarkDialog(parent, title, msg, "info", is_input=True, default_val=default)
    parent.wait_window(d)
    return d.result

# --- MAIN APPLICATION ---
class VPNApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("500x750") # Slightly smaller default
        self.root.configure(bg=C_BG_MAIN)
        self.root.minsize(400, 500)   # Allow shrinking more vertically
        
        # --- ELASTIC GRID CONFIG ---
        self.root.columnconfigure(0, weight=1)
        # Rows 0-3 (Header, Status, Controls) weight=0 (Fixed Height)
        # Row 4 (Friend List) weight=1 (Expands)
        self.root.rowconfigure(4, weight=1)

        self.root.bind("<Map>", self.apply_dark_title_bar)
        self.root.after(100, self.apply_dark_title_bar)

        self.public_ip = "Initializing..."
        self.is_online = False
        self.peer_status = {} 
        self.last_check_time = None
        self.current_db_path = self.load_preferences()

        try:
            png_path = resource_path("clean_icon.png")
            if os.path.exists(png_path):
                img = tk.PhotoImage(file=png_path)
                self.root.iconphoto(True, img) 
            elif os.path.exists(resource_path("gaminglan.ico")):
                self.root.iconbitmap(resource_path("gaminglan.ico"))
            else:
                self.root.iconphoto(True, tk.PhotoImage(data=ICON_DATA))
        except: pass

        self.data = self.load_data()
        self.ensure_server_identity()
        self.scan_for_external_configs()
        self.check_and_repair_peers()
        self.check_ip_thread()
        self.render_ui()
        self.status_loop()

    def apply_dark_title_bar(self, event=None):
        try:
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            value = ctypes.c_int(1)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(value), 4)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 19, ctypes.byref(value), 4)
        except: pass

    # --- DETECTION LOGIC ---
    def check_tunnel_active(self):
        try:
            output = subprocess.check_output('tasklist /FI "IMAGENAME eq wireguard.exe"', shell=True).decode()
            if "wireguard.exe" in output: return True
        except: pass
        try:
            output = self.run_wg("wg show")
            if output and "Unable to access interface" not in output and "ERROR" not in output: return True
        except: pass
        return False

    def scan_for_external_configs(self):
        if not os.path.exists(CONFIG_DIR): return
        existing_names = [p['name'] for p in self.data['peers']]
        imported = 0
        files = [f for f in os.listdir(CONFIG_DIR) if f.endswith(".conf")]
        for f in files:
            name = f.replace("_VPN.conf", "").replace(".conf", "")
            if name in existing_names: continue
            try:
                path = os.path.join(CONFIG_DIR, f)
                with open(path, "r", encoding="utf-8") as fl: c = fl.read()
                ip_m = re.search(r"Address\s*=\s*([0-9\.]+)", c)
                k_m = re.search(r"PrivateKey\s*=\s*([a-zA-Z0-9+/=]+)", c)
                if ip_m and k_m:
                    ip, priv = ip_m.group(1), k_m.group(1)
                    pub = "PLACEHOLDER_KEY_NEED_UPDATE"
                    try: 
                        calc = self.run_wg(f"echo {priv} | wg pubkey")
                        if calc and "ERROR" not in calc: pub = calc
                    except: pass
                    self.data['peers'].append({"name": name, "ip": ip, "public_key": pub})
                    imported += 1
            except: pass
        if imported > 0:
            self.save_data(); self.generate_config()
            show_dark_info(self.root, "Import", f"Auto-imported {imported} friend config(s).")

    def manual_import_file(self):
        path = filedialog.askopenfilename(initialdir=CONFIG_DIR, filetypes=(("Conf", "*.conf"),))
        if not path: return
        try:
            with open(path, "r", encoding="utf-8") as f: c = f.read()
            fname = os.path.basename(path)
            name = fname.replace("_VPN.conf", "").replace(".conf", "")
            ip_m = re.search(r"Address\s*=\s*([0-9\.]+)", c)
            k_m = re.search(r"PrivateKey\s*=\s*([a-zA-Z0-9+/=]+)", c)
            if not ip_m or not k_m:
                show_dark_error(self.root, "Error", "Invalid Config File")
                return
            ip, priv = ip_m.group(1), k_m.group(1)
            pub = "PLACEHOLDER_KEY_NEED_UPDATE"
            try:
                calc = self.run_wg(f"echo {priv} | wg pubkey")
                if calc and "ERROR" not in calc: pub = calc
            except: pass
            
            self.data['peers'].append({"name": name, "ip": ip, "public_key": pub})
            self.save_data(); self.generate_config(); self.refresh_friend_list()
            show_dark_info(self.root, "Success", f"Imported {name}. Update WireGuard!")
        except Exception as e: show_dark_error(self.root, "Error", str(e))

    def render_ui(self):
        for w in self.root.winfo_children(): w.destroy()
        
        # 1. HEADER (Grid Row 0)
        header_frame = tk.Frame(self.root, bg=C_BG_MAIN)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(5,0))
        header_frame.columnconfigure(0, weight=1)

        btn_file = tk.Menubutton(header_frame, text="File / Configs", font=("Segoe UI", 9), bg=C_BG_MAIN, fg=C_TXT_DIM, activebackground=C_BG_PANEL, activeforeground="white", relief="flat")
        file_menu = tk.Menu(btn_file, tearoff=0, bg=C_BG_POPUP, fg="white", activebackground=C_ACCENT_ORN, activeforeground="white", borderwidth=0)
        file_menu.add_command(label="📂 Open Config Folder", command=self.open_config_folder)
        file_menu.add_command(label="🔄 Load Different DB", command=self.load_other_db)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        btn_file.config(menu=file_menu)
        btn_file.pack(side="left")

        btn_help = tk.Button(header_frame, text="About", font=("Segoe UI", 9), bg=C_BG_MAIN, fg=C_TXT_DIM, activebackground=C_BG_PANEL, activeforeground="white", relief="flat", command=self.show_about)
        btn_help.pack(side="right")

        # 2. TITLE (Grid Row 1)
        title_frame = tk.Frame(self.root, bg=C_BG_MAIN, pady=10)
        title_frame.grid(row=1, column=0, sticky="ew", padx=20)
        tk.Label(title_frame, text=APP_TITLE.upper(), font=FONT_HEADER, bg=C_BG_MAIN, fg=C_TXT_MAIN).pack(anchor="w")
        tk.Label(title_frame, text=f"📂 {os.path.basename(self.current_db_path)}", font=("Segoe UI", 9), bg=C_BG_MAIN, fg=C_TXT_DIM).pack(anchor="w")

        # 3. STATUS (Grid Row 2)
        stat_frame = tk.Frame(self.root, bg=C_BG_PANEL, padx=15, pady=15)
        stat_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=10)
        
        s_txt = "ONLINE (Verified)" if self.is_online else "OFFLINE"
        s_col = C_ACCENT_GRN if self.is_online else C_OFFLINE
        
        row = tk.Frame(stat_frame, bg=C_BG_PANEL)
        row.pack(anchor="w", fill="x")
        tk.Label(row, text="●", font=("Arial", 16), bg=C_BG_PANEL, fg=s_col).pack(side="left")
        tk.Label(row, text=f" STATUS: {s_txt}", font=("Segoe UI", 11, "bold"), bg=C_BG_PANEL, fg=s_col).pack(side="left", padx=5)
        
        try:
            with open(HOST_CONF, "r") as f:
                c = f.read()
                m = re.search(r"ListenPort\s*=\s*(\d+)", c)
                curr_port = m.group(1) if m else str(DEFAULT_PORT)
        except: curr_port = str(DEFAULT_PORT)

        self.lbl_ip = tk.Label(stat_frame, text=f"Public IP: {self.public_ip} | Port: {curr_port}", font=FONT_MONO, bg=C_BG_PANEL, fg=C_TXT_DIM)
        self.lbl_ip.pack(anchor="w", pady=(5,0))
        
        if self.is_online:
             check_txt = f"Last Check: {self.last_check_time}" if self.last_check_time else "Polling WireGuard..."
             tk.Label(stat_frame, text=check_txt, font=("Segoe UI", 8), bg=C_BG_PANEL, fg=C_TXT_DIM).pack(anchor="w")

        # 4. SERVER CONTROLS (Grid Row 3) - FIXED HEIGHT
        ctrl_container = tk.Frame(self.root, bg=C_BG_MAIN)
        ctrl_container.grid(row=3, column=0, sticky="ew", padx=20, pady=5)
        ctrl_container.columnconfigure(0, weight=1)

        tk.Label(ctrl_container, text="Server Controls", font=("Segoe UI", 9, "bold"), bg=C_BG_MAIN, fg=C_TXT_MAIN).pack(anchor="w", pady=(10,5))
        
        self.btn_go = tk.Button(ctrl_container, text="🛠 GO ONLINE (Manual)", font=FONT_BODY, bg=C_ACCENT_ORN, fg="white", relief="flat", pady=10, cursor="hand2", command=self.go_online_manual)
        self.btn_go.pack(fill="x", pady=(0, 5))
        
        self.btn_stop = tk.Button(ctrl_container, text="🔴 GO OFFLINE", font=FONT_BODY, bg=C_ACCENT_RED, fg="white", relief="flat", pady=8, cursor="hand2", command=self.go_offline, state="disabled")
        self.btn_stop.pack(fill="x", pady=(0, 5))

        sub_frame = tk.Frame(ctrl_container, bg=C_BG_MAIN)
        sub_frame.pack(fill="x", pady=(5,0))
        
        self.btn_port = tk.Button(sub_frame, text="⚙️ Change Port", font=FONT_BODY, bg=C_ACCENT_PUR, fg="white", relief="flat", pady=5, cursor="hand2", command=self.change_port_ui)
        self.btn_port.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.btn_ip = tk.Button(sub_frame, text="🔄 Update IP", font=FONT_BODY, bg=C_ACCENT_BLU, fg="white", relief="flat", pady=5, cursor="hand2", command=self.update_ip_only)
        self.btn_ip.pack(side="right", fill="x", expand=True, padx=(5, 0))

        if self.is_online: 
            self.btn_go.config(state="disabled", bg=C_BG_PANEL)
            self.btn_stop.config(state="normal", bg=C_ACCENT_RED)
        else: 
            self.btn_stop.config(state="disabled", bg=C_BG_PANEL)

        # 5. FRIEND LIST (Grid Row 4 - EXPANDABLE)
        friend_container_outer = tk.Frame(self.root, bg=C_BG_MAIN)
        friend_container_outer.grid(row=4, column=0, sticky="nsew", padx=20, pady=(10, 10))
        
        tk.Label(friend_container_outer, text="Connected Friends", font=("Segoe UI", 9, "bold"), bg=C_BG_MAIN, fg=C_TXT_MAIN).pack(anchor="w", pady=(5,0))

        outer_frame = tk.Frame(friend_container_outer, bg=C_BG_PANEL)
        outer_frame.pack(fill="both", expand=True, pady=(5, 0))

        btn_row = tk.Frame(outer_frame, bg=C_BG_PANEL)
        btn_row.pack(fill="x")
        tk.Button(btn_row, text="+ Add New Friend", font=FONT_BODY, bg=C_BTN_BG, fg="white", relief="flat", command=self.add_friend, anchor="w", padx=10).pack(side="left", fill="x", expand=True)
        tk.Button(btn_row, text="📥 Import", font=FONT_BODY, bg="#475569", fg="white", relief="flat", command=self.manual_import_file, padx=10).pack(side="right", padx=5)

        container = tk.Frame(outer_frame, bg=C_BG_PANEL)
        container.pack(fill="both", expand=True, pady=5)
        
        self.canvas = tk.Canvas(container, bg=C_BG_PANEL, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        
        self.list_frame = tk.Frame(self.canvas, bg=C_BG_PANEL)
        self.list_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        # NOTE: Removed the bind here that caused the lag loop.
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.list_frame, anchor="nw")
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)

        self.refresh_friend_list()

    def check_scrollbar_visibility(self):
        try:
            self.root.update_idletasks()
            content_h = self.list_frame.winfo_reqheight()
            visible_h = self.canvas.winfo_height()
            
            if content_h > visible_h:
                self.scrollbar.pack(side="right", fill="y")
            else:
                self.scrollbar.pack_forget()
        except: pass

    def refresh_friend_list(self):
        for w in self.list_frame.winfo_children(): w.destroy()
        if not self.data['peers']:
            tk.Label(self.list_frame, text="No friends added.", bg=C_BG_PANEL, fg=C_TXT_DIM, font=FONT_BODY).pack(pady=10, padx=10)
            self.check_scrollbar_visibility()
            return
        
        peers = self.data['peers']
        
        for i, p in enumerate(peers):
            active = self.peer_status.get(p['public_key'], False)
            row = tk.Frame(self.list_frame, bg=C_BG_PANEL)
            row.pack(fill="x", pady=2, padx=5)
            
            col = C_ACCENT_GRN if active else C_OFFLINE
            tk.Label(row, text="●", font=("Arial", 12), bg=C_BG_PANEL, fg=col).pack(side="left", padx=5)
            tk.Label(row, text=p['name'], font=("Segoe UI", 10, "bold"), bg=C_BG_PANEL, fg=C_TXT_MAIN).pack(side="left")
            
            btn_kick = tk.Button(row, text="❌", font=("Arial", 8), bg=C_ACCENT_RED, fg="white", relief="flat", cursor="hand2", command=lambda idx=i: self.kick_user(idx))
            btn_kick.pack(side="right", padx=5)
            tk.Label(row, text=f"[{p['ip']}]", font=FONT_MONO, bg=C_BG_PANEL, fg=C_TXT_DIM).pack(side="right", padx=5)
        
        # Only check visibility after list update
        self.check_scrollbar_visibility()

    def kick_user(self, index):
        name = self.data['peers'][index]['name']
        if ask_dark_yesno(self.root, "Ban User", f"Remove '{name}' from database?"):
            del self.data['peers'][index]
            self.save_data(); self.generate_config(); self.refresh_friend_list()
            try: os.remove(os.path.join(CONFIG_DIR, f"{name}_VPN.conf"))
            except: pass
            show_dark_info(self.root, "Important", f"Removed {name}.\n\nRe-import config in WireGuard to apply ban!")

    def go_online_manual(self):
        if not self.check_tunnel_active():
            show_dark_error(self.root, "Tunnel Stopped", "WireGuard is not running!\n\n1. Open WireGuard\n2. Click Activate\n3. Try again.")
            return
        self.generate_config()
        self.is_online = True
        self.render_ui()
        show_dark_info(self.root, "Online", "Status Verified: Tunnel is Active.\nUI updated.")

    def go_offline(self):
        self.is_online = False
        self.peer_status = {}
        self.render_ui()
        show_dark_info(self.root, "Offline", "UI is Offline.\n\n⚠️ Don't forget to Deactivate WireGuard manually!")

    def show_about(self):
        msg = f"{APP_TITLE}\nVersion: {VERSION}\n\n{CREDITS}"
        show_dark_info(self.root, "About", msg)

    # --- PORT CHANGER ---
    def change_port_ui(self):
        new_port = ask_dark_string(self.root, "Change Port", "Enter new UDP Port (49152-65535):", default="52392")
        if not new_port or not new_port.isdigit(): return
        port_num = int(new_port)
        if not (1024 <= port_num <= 65535):
            show_dark_error(self.root, "Error", "Invalid Port Range!\nStay above 1024.")
            return
        
        if os.path.exists(HOST_CONF):
            with open(HOST_CONF, 'r') as f: content = f.read()
            content = re.sub(r"ListenPort\s*=\s*\d+", f"ListenPort = {port_num}", content)
            with open(HOST_CONF, 'w') as f: f.write(content)
        
        if os.path.exists(CONFIG_DIR):
            for fname in os.listdir(CONFIG_DIR):
                if fname.endswith(".conf"):
                    path = os.path.join(CONFIG_DIR, fname)
                    with open(path, 'r') as f: c = f.read()
                    c = re.sub(r"(Endpoint\s*=\s*|Endpoint=)(.+):(\d+)", f"Endpoint=\\2:{port_num}", c)
                    with open(path, 'w') as f: f.write(c)

        self.render_ui()
        show_dark_info(self.root, "Success", f"Port updated to {port_num}.\n\nIMPORTANT: SEND NEW FILES TO FRIENDS.")
        self.open_config_folder()

    # --- UPDATE IP ONLY ---
    def update_ip_only(self):
        try:
            current_ip = urllib.request.urlopen('https://api.ipify.org', timeout=5).read().decode('utf8').strip()
        except:
            current_ip = ask_dark_string(self.root, "Manual IP", "Could not detect IP. Enter Public IP:")
            if not current_ip: return
        
        current_ip = re.sub(r"[^0-9\.]", "", current_ip)
        count = 0
        if os.path.exists(CONFIG_DIR):
            for fname in os.listdir(CONFIG_DIR):
                if fname.endswith(".conf"):
                    path = os.path.join(CONFIG_DIR, fname)
                    with open(path, 'r') as f: c = f.read()
                    
                    port_match = re.search(r"(Endpoint\s*=\s*|Endpoint=).*:(\d+)", c)
                    old_port = port_match.group(2) if port_match else str(DEFAULT_PORT)
                    c = re.sub(r"(Endpoint\s*=\s*|Endpoint=).*", f"Endpoint={current_ip}:{old_port}", c)
                    
                    with open(path, 'w') as f: f.write(c)
                    count += 1
        
        self.public_ip = current_ip
        self.render_ui()
        show_dark_info(self.root, "IP Updated", f"Public IP updated to {current_ip} in {count} files.\n\nSend these to your friends!")
        self.open_config_folder()

    def add_friend(self):
        if "Initializing" in self.public_ip:
            try: self.public_ip = urllib.request.urlopen('https://api.ipify.org', timeout=5).read().decode('utf8').strip()
            except: self.public_ip = ask_dark_string(self.root, "Input", "Enter Public IP:") or "YOUR_IP"
            
        name = ask_dark_string(self.root, "Input", "Friend Name:")
        if not name: return
        
        priv = self.run_wg("wg genkey")
        is_ph = False
        if "ERROR" in priv:
            show_dark_error(self.root, "No WireGuard", "WireGuard not found.\nUsing Placeholder keys.")
            priv = "PLACEHOLDER_KEY"; pub = "PLACEHOLDER_PUB"; is_ph = True
        else:
            pub = self.run_wg(f"echo {priv} | wg pubkey")

        used = [p['ip'] for p in self.data['peers']]
        net = ipaddress.ip_network(BASE_SUBNET)
        next_ip = next((str(net[i]) for i in range(2,254) if str(net[i]) not in used), None)
        
        try: self.write_peer_config_file(name, next_ip, priv)
        except Exception as e: show_dark_error(self.root, "Error", str(e)); return

        self.data['peers'].append({"name": name, "ip": next_ip, "public_key": pub})
        self.save_data(); self.generate_config(); self.refresh_friend_list()
        
        if not is_ph: show_dark_info(self.root, "Added", f"Created config for {name}.\n\nREMINDER: Update WireGuard!")

    # --- SHARED UTILS ---
    def load_preferences(self):
        try:
            with open(SETTINGS_FILE, 'r') as f: return json.load(f)['last_db_path']
        except: return DEFAULT_DB
    def save_preferences(self):
        try: 
            with open(SETTINGS_FILE, 'w') as f: json.dump({"last_db_path": self.current_db_path}, f)
        except: pass
    def open_config_folder(self):
        if not os.path.exists(CONFIG_DIR): os.makedirs(CONFIG_DIR)
        os.startfile(CONFIG_DIR)
    def load_other_db(self):
        f = filedialog.askopenfilename()
        if f: self.current_db_path = f; self.save_preferences(); self.data = self.load_data(); self.render_ui()
    def load_data(self):
        try: 
            with open(self.current_db_path, 'r', encoding='utf-8') as f: return json.load(f)
        except: return {"server": None, "peers": []}
    def save_data(self):
        with open(self.current_db_path, 'w', encoding='utf-8') as f: json.dump(self.data, f, indent=4)
    def check_and_repair_peers(self):
        if not self.data.get('server') or "PLACEHOLDER" in self.data['server'].get('private_key', ''): return
        changed = False
        for p in self.data['peers']:
            if "PLACEHOLDER" in p['public_key']:
                priv = self.run_wg("wg genkey")
                if "ERROR" not in priv:
                    p['public_key'] = self.run_wg(f"echo {priv} | wg pubkey")
                    self.write_peer_config_file(p['name'], p['ip'], priv)
                    changed = True
        if changed: self.save_data(); self.generate_config(); show_dark_info(self.root, "Repaired", "Fixed placeholder configs.")
    def write_peer_config_file(self, name, ip, priv):
        if not os.path.exists(CONFIG_DIR): os.makedirs(CONFIG_DIR)
        pub = self.data['server'].get('public_key', "PLACEHOLDER") if self.data['server'] else "PLACEHOLDER"
        endpoint = self.public_ip
        if "Initializing" in endpoint:
             try: endpoint = urllib.request.urlopen('https://api.ipify.org').read().decode('utf8').strip()
             except: endpoint = "YOUR_PUBLIC_IP"
        
        endpoint = re.sub(r"[^0-9\.]", "", endpoint)
        try:
            with open(HOST_CONF, "r") as f:
                c = f.read()
                m = re.search(r"ListenPort\s*=\s*(\d+)", c)
                curr_port = m.group(1) if m else str(DEFAULT_PORT)
        except: curr_port = str(DEFAULT_PORT)

        c = f"[Interface]\nPrivateKey={priv}\nAddress={ip}/32\nDNS=1.1.1.1\nMTU=1280\n[Peer]\nPublicKey={pub}\nEndpoint={endpoint}:{curr_port}\nAllowedIPs={BASE_SUBNET}\nPersistentKeepalive=25"
        with open(os.path.join(CONFIG_DIR, f"{name}_VPN.conf"), "w", encoding='utf-8') as f: f.write(c)
    def ensure_server_identity(self):
        if not self.data.get('server') or "PLACEHOLDER" in self.data['server'].get('private_key', ''):
            priv = self.run_wg("wg genkey")
            if "ERROR" not in priv:
                pub = self.run_wg(f"echo {priv} | wg pubkey")
                self.data['server'] = {"private_key": priv, "public_key": pub}
                self.save_data()
    def run_wg(self, cmd):
        try: return subprocess.check_output(cmd, shell=True).decode('utf-8').strip()
        except:
            paths = [r"C:\Program Files\WireGuard\wg.exe"]
            for p in paths:
                if os.path.exists(p):
                    try: return subprocess.check_output(cmd.replace("wg ", f'"{p}" '), shell=True).decode('utf-8').strip()
                    except: pass
            return "ERROR"
    def check_ip_thread(self): threading.Thread(target=self._fetch_ip, daemon=True).start()
    def _fetch_ip(self):
        try: self.public_ip = urllib.request.urlopen('https://api.ipify.org').read().decode('utf8').strip(); self.root.after(0, lambda: self.render_ui())
        except: pass
    def generate_config(self):
        if not self.data['server']: return
        curr_port = DEFAULT_PORT
        if os.path.exists(HOST_CONF):
            try:
                with open(HOST_CONF, "r") as f:
                    c = f.read()
                    m = re.search(r"ListenPort\s*=\s*(\d+)", c)
                    if m: curr_port = int(m.group(1))
            except: pass
        c = f"[Interface]\nPrivateKey={self.data['server']['private_key']}\nAddress=10.100.0.1/24\nListenPort={curr_port}\nMTU=1280\n"
        for p in self.data['peers']: c += f"\n[Peer]\n# {p['name']}\nPublicKey={p['public_key']}\nAllowedIPs={p['ip']}/32\n"
        with open(HOST_CONF, "w", encoding='utf-8') as f: f.write(c)
    def status_loop(self):
        if self.is_online: threading.Thread(target=self._check_wireguard_status, daemon=True).start()
        self.root.after(3000, self.status_loop)
    def _check_wireguard_status(self):
        try:
            out = self.run_wg("wg show all dump")
            if "ERROR" in out or not out: return
            now = time.time(); new_stat = {}
            for line in out.split('\n'):
                p = line.split('\t')
                if len(p)>5: new_stat[p[1]] = (now - int(p[5])) < 180
            self.peer_status = new_stat
            self.last_check_time = datetime.now().strftime("%H:%M:%S")
            self.root.after(0, self.render_ui) 
        except: pass

if __name__ == "__main__":
    root = tk.Tk()
    app = VPNApp(root)
    root.mainloop()