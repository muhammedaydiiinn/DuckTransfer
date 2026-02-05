"""Connection dialog for FTP, SFTP, FTP-SSL and S3."""

import tkinter as tk
from tkinter import messagebox

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from config.connections import load_connections, add_connection, remove_connection

try:
    from connectors import HAS_SFTP
except ImportError:
    HAS_SFTP = False

PROTOCOLS = [
    ("ftp", "FTP (Dosya Aktarım İletişim Kuralı)", 21),
    ("ftp_ssl", "FTP-SSL (Explicit AUTH TLS)", 21),
    ("sftp", "SFTP (SSH Dosya Aktarım)", 22),
    ("s3", "Amazon S3", 0),
]


class ConnectionDialog(ttk.Toplevel):
    """Dialog to configure and establish connection."""

    def __init__(self, parent, on_connect, **kwargs):
        super().__init__(parent, **kwargs)
        self.on_connect = on_connect
        self.result = None

        self.title("Yeni Bağlantı")
        self.geometry("520x520")
        self.minsize(480, 450)
        self.resizable(True, True)

        self.transient(parent)
        self.grab_set()

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._cancel)

    def _build_ui(self):
        main = ttk.Frame(self)
        main.pack(fill=BOTH, expand=True, padx=20, pady=20)

        # Kayıtlı bağlantılar - scrollable alan için
        content = ttk.Frame(main)
        content.pack(fill=BOTH, expand=True)

        # Kayıtlı bağlantılar
        ttk.Label(content, text="Kayıtlı Bağlantılar", font=("Helvetica", 10, "bold")).pack(anchor=W, pady=(0, 5))
        saved_frame = ttk.Frame(content)
        saved_frame.pack(fill=X, pady=(0, 15))

        self.saved_var = tk.StringVar(value="")
        self.saved_combo = ttk.Combobox(
            saved_frame, textvariable=self.saved_var, width=45, state="readonly"
        )
        self.saved_combo.pack(side=LEFT, fill=X, expand=True, padx=(0, 5))
        self.saved_combo.bind("<<ComboboxSelected>>", self._on_saved_select)

        ttk.Button(saved_frame, text="Yükle", bootstyle=OUTLINE, command=self._load_saved).pack(side=LEFT, padx=2)
        ttk.Button(saved_frame, text="Sil", bootstyle=DANGER, command=self._delete_saved).pack(side=LEFT, padx=2)

        self._refresh_saved_list()

        ttk.Separator(content, orient=HORIZONTAL).pack(fill=X, pady=10)

        ttk.Label(content, text="Bağlantı Türü", font=("Helvetica", 10, "bold")).pack(anchor=W, pady=(0, 5))

        self.protocol_var = tk.StringVar(value="ftp")
        protocol_frame = ttk.Frame(content)
        protocol_frame.pack(fill=X, pady=(0, 10))

        for value, label, _ in PROTOCOLS:
            if value == "sftp" and not HAS_SFTP:
                continue
            ttk.Radiobutton(
                protocol_frame, text=label, variable=self.protocol_var,
                value=value, command=self._on_protocol_change
            ).pack(anchor=W)

        self._build_ftp_fields(content)
        self._build_s3_fields(content)
        self._on_protocol_change()

        # Kaydet seçeneği
        self.save_var = tk.BooleanVar(value=False)
        self.save_name_var = tk.StringVar(value="")
        save_frame = ttk.Frame(content)
        save_frame.pack(fill=X, pady=(15, 5))
        ttk.Checkbutton(save_frame, text="Bağlantıyı kaydet", variable=self.save_var).pack(side=LEFT, padx=(0, 10))
        ttk.Label(save_frame, text="İsim:").pack(side=LEFT, padx=(0, 5))
        ttk.Entry(save_frame, textvariable=self.save_name_var, width=20).pack(side=LEFT)

        btn_frame = ttk.Frame(content)
        btn_frame.pack(fill=X, pady=(15, 0))
        ttk.Button(btn_frame, text="Bağlan", bootstyle=SUCCESS, command=self._connect).pack(side=RIGHT, padx=5)
        ttk.Button(btn_frame, text="İptal", bootstyle=SECONDARY, command=self._cancel).pack(side=RIGHT)

    def _refresh_saved_list(self):
        conns = load_connections()
        names = [c.get("name", "İsimsiz") for c in conns if c.get("name")]
        self.saved_combo["values"] = names
        if names:
            self.saved_combo.current(0)
        else:
            self.saved_var.set("")

    def _on_saved_select(self, event=None):
        pass

    def _load_saved(self):
        name = self.saved_var.get().strip()
        if not name:
            return
        conns = load_connections()
        for c in conns:
            if c.get("name") == name:
                proto = c.get("protocol", "ftp")
                self.protocol_var.set(proto)
                self._on_protocol_change()
                if proto in ("ftp", "ftp_ssl", "sftp"):
                    self.ftp_host.delete(0, tk.END)
                    self.ftp_host.insert(0, c.get("host", ""))
                    self.ftp_port.delete(0, tk.END)
                    self.ftp_port.insert(0, str(c.get("port", 21 if proto != "sftp" else 22)))
                    self.ftp_user.delete(0, tk.END)
                    self.ftp_user.insert(0, c.get("username", ""))
                    self.ftp_pass.delete(0, tk.END)
                    self.ftp_pass.insert(0, c.get("password", ""))
                else:
                    self.s3_access.delete(0, tk.END)
                    self.s3_access.insert(0, c.get("access_key", ""))
                    self.s3_secret.delete(0, tk.END)
                    self.s3_secret.insert(0, c.get("secret_key", ""))
                    self.s3_region.delete(0, tk.END)
                    self.s3_region.insert(0, c.get("region", "us-east-1"))
                    self.s3_bucket.delete(0, tk.END)
                    self.s3_bucket.insert(0, c.get("bucket", ""))
                self.save_name_var.set(name)
                break

    def _delete_saved(self):
        name = self.saved_var.get().strip()
        if not name or not messagebox.askyesno("Onay", f"'{name}' silinsin mi?"):
            return
        remove_connection(name)
        self._refresh_saved_list()

    def _build_ftp_fields(self, parent):
        self.ftp_frame = ttk.LabelFrame(parent, text="Sunucu Ayarları (FTP / SFTP)")
        self.ftp_frame.pack(fill=BOTH, expand=True, pady=5)
        ftp_inner = ttk.Frame(self.ftp_frame)
        ftp_inner.pack(fill=X, padx=15, pady=15)

        ttk.Label(ftp_inner, text="Sunucu:").grid(row=0, column=0, sticky=W, pady=3, padx=(0, 10))
        self.ftp_host = ttk.Entry(ftp_inner, width=35)
        self.ftp_host.grid(row=0, column=1, sticky=EW, pady=3)
        self.ftp_host.insert(0, "ftp.example.com")

        ttk.Label(ftp_inner, text="Port:").grid(row=1, column=0, sticky=W, pady=3, padx=(0, 10))
        self.ftp_port = ttk.Entry(ftp_inner, width=10)
        self.ftp_port.grid(row=1, column=1, sticky=W, pady=3)
        self.ftp_port.insert(0, "21")

        ttk.Label(ftp_inner, text="Kullanıcı:").grid(row=2, column=0, sticky=W, pady=3, padx=(0, 10))
        self.ftp_user = ttk.Entry(ftp_inner, width=35)
        self.ftp_user.grid(row=2, column=1, sticky=EW, pady=3)

        ttk.Label(ftp_inner, text="Şifre:").grid(row=3, column=0, sticky=W, pady=3, padx=(0, 10))
        self.ftp_pass = ttk.Entry(ftp_inner, width=35, show="•")
        self.ftp_pass.grid(row=3, column=1, sticky=EW, pady=3)

        ftp_inner.columnconfigure(1, weight=1)

    def _build_s3_fields(self, parent):
        self.s3_frame = ttk.LabelFrame(parent, text="Amazon S3 Ayarları")
        self.s3_frame.pack(fill=BOTH, expand=True, pady=5)
        s3_inner = ttk.Frame(self.s3_frame)
        s3_inner.pack(fill=X, padx=15, pady=15)

        ttk.Label(s3_inner, text="Access Key:").grid(row=0, column=0, sticky=W, pady=3, padx=(0, 10))
        self.s3_access = ttk.Entry(s3_inner, width=35)
        self.s3_access.grid(row=0, column=1, sticky=EW, pady=3)

        ttk.Label(s3_inner, text="Secret Key:").grid(row=1, column=0, sticky=W, pady=3, padx=(0, 10))
        self.s3_secret = ttk.Entry(s3_inner, width=35, show="•")
        self.s3_secret.grid(row=1, column=1, sticky=EW, pady=3)

        ttk.Label(s3_inner, text="Bölge:").grid(row=2, column=0, sticky=W, pady=3, padx=(0, 10))
        self.s3_region = ttk.Entry(s3_inner, width=35)
        self.s3_region.grid(row=2, column=1, sticky=EW, pady=3)
        self.s3_region.insert(0, "us-east-1")

        ttk.Label(s3_inner, text="Bucket:").grid(row=3, column=0, sticky=W, pady=3, padx=(0, 10))
        self.s3_bucket = ttk.Entry(s3_inner, width=35)
        self.s3_bucket.grid(row=3, column=1, sticky=EW, pady=3)

        s3_inner.columnconfigure(1, weight=1)

    def _on_protocol_change(self):
        proto = self.protocol_var.get()
        if proto == "s3":
            self.ftp_frame.pack_forget()
            self.s3_frame.pack(fill=BOTH, expand=True, pady=5)
        else:
            self.s3_frame.pack_forget()
            self.ftp_frame.pack(fill=BOTH, expand=True, pady=5)
            default_port = 22 if proto == "sftp" else 21
            self.ftp_port.delete(0, tk.END)
            self.ftp_port.insert(0, str(default_port))

    def _connect(self):
        proto = self.protocol_var.get()
        try:
            if proto == "s3":
                config = {
                    "protocol": "s3",
                    "access_key": self.s3_access.get().strip(),
                    "secret_key": self.s3_secret.get(),
                    "region": self.s3_region.get().strip() or "us-east-1",
                    "bucket": self.s3_bucket.get().strip(),
                }
                if not config["bucket"]:
                    messagebox.showwarning("Uyarı", "Bucket adı girin.")
                    return
            else:
                port = int(self.ftp_port.get() or (22 if proto == "sftp" else 21))
                config = {
                    "protocol": proto,
                    "host": self.ftp_host.get().strip(),
                    "port": port,
                    "username": self.ftp_user.get().strip(),
                    "password": self.ftp_pass.get(),
                }
                if not config["host"]:
                    messagebox.showwarning("Uyarı", "Sunucu adresi girin.")
                    return

            if self.save_var.get():
                name = self.save_name_var.get().strip() or config.get("host", config.get("bucket", "Bağlantı"))
                add_connection(name, {**config, "name": name})

            self.on_connect(config)
            self.result = config
            self.destroy()
        except ValueError:
            messagebox.showerror("Hata", "Geçersiz port numarası.")
        except Exception as e:
            messagebox.showerror("Bağlantı Hatası", str(e))

    def _cancel(self):
        self.result = None
        self.destroy()
