# ==============================================================================
#  GAMING LAN MANAGER - MIDNIGHT OBSIDIAN (TRUE DARK MODE)
#  ------------------------------------------------------------------------------
#  - TRUE DARK UI: Custom Title Bar, Custom Popups, Custom Menus.
#  - NO WHITE FLASHES: All standard message boxes replaced with dark equivalents.
#  - STRICT STATUS: Only shows "ONLINE" if tunnel is verified active.
#  - MANUAL ONLY: Secure, non-admin (mostly), manual control.
# ==============================================================================

import tkinter as tk
from tkinter import filedialog, simpledialog 
# Note: We are NOT using 'messagebox' anymore to avoid white windows.
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

# --- CONFIGURATION ---
APP_TITLE = "Gaming Lan Manager"
VERSION = "2026.40 (Obsidian Dark UI)"
CREDITS = """
Lead Developer: Uri S.
Co-Pilot / Assistance: Gemini AI (Google)

True Dark Mode Edition.
Secure & Manual Control.
"""
SERVER_PORT = 51820
BASE_SUBNET = "10.100.0.0/24"

# --- DARK THEME PALETTE ---
C_BG_MAIN = "#121212"       # Window Background
C_BG_PANEL = "#1E1E1E"      # Panel Background
C_BG_POPUP = "#252526"      # Popup Background
C_TXT_MAIN = "#E0E0E0"      # Main Text
C_TXT_DIM = "#A0A0A0"       # Dim Text
C_ACCENT_ORN = "#D35400"    # Orange
C_ACCENT_RED = "#C0392B"    # Red
C_ACCENT_GRN = "#27AE60"    # Green
C_BTN_BG = "#2D2D30"        # Dark Button
C_BTN_HOVER = "#3E3E42"     # Button Hover
C_OFFLINE = "#505050"       # Offline/Disabled

# --- PATH CONFIG ---
if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
    # Fix for icon resource in frozen mode
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

# --- CUSTOM DARK POPUP CLASS ---
class DarkPopup(tk.Toplevel):
    """Replaces standard white message boxes with a dark themed window."""
    def __init__(self, parent, title, message, style="info", callback=None):
        super().__init__(parent)
        self.callback = callback
        self.result = False
        
        self.configure(bg=C_BG_POPUP)
        self.title(title)
        self.geometry("400x200")
        self.resizable(False, False)
        self.transient(parent) # Keep on top of main window
        self.grab_set()        # Modal (block other input)
        
        # Center the popup
        x = parent.winfo_x() + (parent.winfo_width() // 2) - 200
        y = parent.winfo_y() + (parent.winfo_height() // 2) - 100
        self.geometry(f"+{x}+{y}")

        # Dark Title Bar Hack for Popup
        try:
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(ctypes.c_int(1)), 4)
        except: pass

        # Icon & Color Setup
        icon_char = "ℹ"
        icon_col = C_TXT_MAIN
        if style == "error": icon_char = "⚠️"; icon_col = C_ACCENT_RED
        elif style == "question": icon_char = "?"; icon_col = C_ACCENT_ORN

        # UI Layout
        main_frame = tk.Frame(self, bg=C_BG_POPUP, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)

        tk.Label(main_frame, text=icon_char, font=("Arial", 24), bg=C_BG_POPUP, fg=icon_col).pack(side="left", anchor="n", padx=(0, 15))
        msg_lbl = tk.Label(main_frame, text=message, font=FONT_BODY, bg=C_BG_POPUP, fg=C_TXT_MAIN, wraplength=300, justify="left")
        msg_lbl.pack(side="left", fill="both", expand=True)

        # Buttons
        btn_frame = tk.Frame(self, bg=C_BG_POPUP, pady=15)
        btn_frame.pack(fill="x")

        if style == "question":
            tk.Button(btn_frame, text="Yes", bg=C_ACCENT_GRN, fg="white", font=("Segoe UI", 9, "bold"), relief="flat", width=10, command=self.on_yes).pack(side="right", padx=20)
            tk.Button(btn_frame, text="No", bg=C_BTN_BG, fg="white", font=("Segoe UI", 9), relief="flat", width=10, command=self.on_close).pack(side="right")
        else:
            tk.Button(btn_frame, text="OK", bg=C_BTN_BG, fg="white", font=("Segoe UI", 9), relief="flat", width=10, command=self.on_close).pack(side="bottom")

    def on_yes(self):
        self.result = True
        self.destroy()
        if self.callback: self.callback(True)

    def on_close(self):
        self.destroy()
        if self.callback: self.callback(False)

# --- HELPER FUNCTIONS FOR DARK MSGBOXES ---
def show_dark_info(parent, title, msg): DarkPopup(parent, title, msg, "info")
def show_dark_error(parent, title, msg): DarkPopup(parent, title, msg, "error")
def ask_dark_yesno(parent, title, msg): 
    # This blocks until closed, simulating askyesno
    popup = DarkPopup(parent, title, msg, "question")
    parent.wait_window(popup)
    return popup.result

# --- MAIN APPLICATION ---
class VPNApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("500x750")
        self.root.configure(bg=C_BG_MAIN)
        self.root.resizable(False, False)
        
        # FORCE DARK TITLE BAR (Windows 10/11)
        try:
            # DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
            value = ctypes.c_int(1) # 1 = True
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(value), 4)
        except: pass

        self.public_ip = "Initializing..."
        self.is_online = False
        self.peer_status = {} 
        self.current_db_path = self.load_preferences()

        # Load Icons
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

    # --- LOGIC ---
    def check_tunnel_active(self):
        try:
            output = self.run_wg("wg show")
            return (output and "interface:" in output.lower())
        except: return False

    def scan_for_external_configs(self):
        if not os.path.exists(CONFIG_DIR): return
        existing_names = [p['name'] for p in self.data['peers']]
        existing_ips = [p['ip'] for p in self.data['peers']]
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
                    if ip in existing_ips: continue
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
            for p in self.data['peers']:
                if p['ip'] == ip: 
                    show_dark_error(self.root, "Error", f"IP {ip} already exists.")
                    return
                if p['name'] == name: name += "_Imp"
            
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
        
        # --- CUSTOM MENU BAR (To ensure it is dark) ---
        menu_frame = tk.Frame(self.root, bg=C_BG_MAIN, height=30)
        menu_frame.pack(fill="x", padx=10, pady=(5,0))
        
        # "File" Button
        btn_file = tk.Menubutton(menu_frame, text="File / Configs", font=("Segoe UI", 9), bg=C_BG_MAIN, fg=C_TXT_DIM, activebackground=C_BG_PANEL, activeforeground="white", relief="flat")
        file_menu = tk.Menu(btn_file, tearoff=0, bg=C_BG_POPUP, fg="white", activebackground=C_ACCENT_ORN, activeforeground="white", borderwidth=0)
        file_menu.add_command(label="📂 Open Config Folder", command=self.open_config_folder)
        file_menu.add_command(label="🔄 Load Different DB", command=self.load_other_db)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        btn_file.config(menu=file_menu)
        btn_file.pack(side="left")

        # "Help" Button
        btn_help = tk.Button(menu_frame, text="About", font=("Segoe UI", 9), bg=C_BG_MAIN, fg=C_TXT_DIM, activebackground=C_BG_PANEL, activeforeground="white", relief="flat", command=self.show_about)
        btn_help.pack(side="right")

        # --- HEADER ---
        header = tk.Frame(self.root, bg=C_BG_MAIN, pady=10)
        header.pack(fill="x", padx=20)
        tk.Label(header, text=APP_TITLE.upper(), font=FONT_HEADER, bg=C_BG_MAIN, fg=C_TXT_MAIN).pack(anchor="w")
        tk.Label(header, text=f"📂 {os.path.basename(self.current_db_path)}", font=("Segoe UI", 9), bg=C_BG_MAIN, fg=C_TXT_DIM).pack(anchor="w")

        # --- STATUS ---
        stat_frame = tk.Frame(self.root, bg=C_BG_PANEL, padx=15, pady=15)
        stat_frame.pack(fill="x", padx=20, pady=10)
        
        s_txt = "ONLINE (Verified)" if self.is_online else "OFFLINE"
        s_col = C_ACCENT_GRN if self.is_online else C_OFFLINE
        
        row = tk.Frame(stat_frame, bg=C_BG_PANEL)
        row.pack(anchor="w", fill="x")
        tk.Label(row, text="●", font=("Arial", 16), bg=C_BG_PANEL, fg=s_col).pack(side="left")
        tk.Label(row, text=f" STATUS: {s_txt}", font=("Segoe UI", 11, "bold"), bg=C_BG_PANEL, fg=s_col).pack(side="left", padx=5)
        self.lbl_ip = tk.Label(stat_frame, text=f"Public IP: {self.public_ip}", font=FONT_MONO, bg=C_BG_PANEL, fg=C_TXT_DIM)
        self.lbl_ip.pack(anchor="w", pady=(5,0))

        # --- CONTROLS ---
        tk.Label(self.root, text="Server Controls", font=("Segoe UI", 9, "bold"), bg=C_BG_MAIN, fg=C_TXT_MAIN).pack(anchor="w", padx=20)
        btn_frame = tk.Frame(self.root, bg=C_BG_MAIN)
        btn_frame.pack(fill="x", padx=20, pady=(5, 10))
        
        self.btn_go = tk.Button(btn_frame, text="🛠 GO ONLINE (Manual)", font=FONT_BODY, bg=C_ACCENT_ORN, fg="white", relief="flat", pady=10, cursor="hand2", command=self.go_online_manual)
        self.btn_go.pack(fill="x")
        
        self.btn_stop = tk.Button(self.root, text="🔴 GO OFFLINE", font=FONT_BODY, bg=C_ACCENT_RED, fg="white", relief="flat", pady=8, cursor="hand2", command=self.go_offline, state="disabled")
        self.btn_stop.pack(fill="x", padx=20, pady=(5, 20))

        if self.is_online: 
            self.btn_go.config(state="disabled", bg=C_BG_PANEL)
            self.btn_stop.config(state="normal", bg=C_ACCENT_RED)
        else: 
            self.btn_stop.config(state="disabled", bg=C_BG_PANEL)

        # --- FRIENDS ---
        tk.Label(self.root, text="Connected Friends", font=("Segoe UI", 9, "bold"), bg=C_BG_MAIN, fg=C_TXT_MAIN).pack(anchor="w", padx=20)
        f_frame = tk.Frame(self.root, bg=C_BG_PANEL)
        f_frame.pack(fill="both", expand=True, padx=20, pady=(5, 10))
        
        btn_row = tk.Frame(f_frame, bg=C_BG_PANEL)
        btn_row.pack(fill="x")
        tk.Button(btn_row, text="+ Add New Friend", font=FONT_BODY, bg=C_BTN_BG, fg="white", relief="flat", command=self.add_friend, anchor="w", padx=10).pack(side="left", fill="x", expand=True)
        tk.Button(btn_row, text="📥 Import", font=FONT_BODY, bg="#475569", fg="white", relief="flat", command=self.manual_import_file, padx=10).pack(side="right", padx=5)

        self.list_frame = tk.Frame(f_frame, bg=C_BG_PANEL)
        self.list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.refresh_friend_list()

    def refresh_friend_list(self):
        for w in self.list_frame.winfo_children(): w.destroy()
        if not self.data['peers']:
            tk.Label(self.list_frame, text="No friends added.", bg=C_BG_PANEL, fg=C_TXT_DIM, font=FONT_BODY).pack(pady=10)
            return
        for i, p in enumerate(self.data['peers']):
            active = self.peer_status.get(p['public_key'], False)
            row = tk.Frame(self.list_frame, bg=C_BG_PANEL)
            row.pack(fill="x", pady=2)
            col = C_ACCENT_GRN if active else C_OFFLINE
            tk.Label(row, text="●", font=("Arial", 12), bg=C_BG_PANEL, fg=col).pack(side="left", padx=5)
            tk.Label(row, text=p['name'], font=("Segoe UI", 10, "bold"), bg=C_BG_PANEL, fg=C_TXT_MAIN).pack(side="left")
            
            btn_kick = tk.Button(row, text="❌", font=("Arial", 8), bg=C_ACCENT_RED, fg="white", relief="flat", cursor="hand2", command=lambda idx=i: self.kick_user(idx))
            btn_kick.pack(side="right", padx=5)
            tk.Label(row, text=f"[{p['ip']}]", font=FONT_MONO, bg=C_BG_PANEL, fg=C_TXT_DIM).pack(side="right", padx=5)

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

    def add_friend(self):
        if "Initializing" in self.public_ip:
            self.public_ip = simpledialog.askstring("Input", "Enter Public IP:") or "YOUR_IP"
        name = simpledialog.askstring("Input", "Friend Name:")
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

    # --- SHARED UTILS (Copying logic from previous steps) ---
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
        # (Same logic as previous, compacted for length)
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
        endpoint = self.public_ip if "Initializing" not in self.public_ip else "YOUR_PUBLIC_IP"
        c = f"[Interface]\nPrivateKey={priv}\nAddress={ip}/32\nDNS=1.1.1.1\nMTU=1280\n[Peer]\nPublicKey={pub}\nEndpoint={endpoint}:{SERVER_PORT}\nAllowedIPs={BASE_SUBNET}\nPersistentKeepalive=25"
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
        try: self.public_ip = urllib.request.urlopen('https://api.ipify.org').read().decode('utf8'); self.root.after(0, lambda: self.lbl_ip.config(text=f"Public IP: {self.public_ip}"))
        except: pass
    def generate_config(self):
        if not self.data['server']: return
        c = f"[Interface]\nPrivateKey={self.data['server']['private_key']}\nAddress=10.100.0.1/24\nListenPort={SERVER_PORT}\nMTU=1280\n"
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
            self.peer_status = new_stat; self.root.after(0, self.refresh_friend_list)
        except: pass

if __name__ == "__main__":
    root = tk.Tk()
    app = VPNApp(root)
    root.mainloop()