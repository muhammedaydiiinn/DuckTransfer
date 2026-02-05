#!/usr/bin/env python3
"""
DuckTransfer - FTP, SFTP & S3 Masaüstü İstemcisi
CyberDuck ve FileZilla benzeri çift panelli dosya yöneticisi.
"""

import os
import sys
import threading
from pathlib import Path
from tkinter import messagebox

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from connectors import FTPConnector, S3Connector, HAS_SFTP
try:
    from connectors import SFTPConnector
except ImportError:
    SFTPConnector = None
from connectors.base import BaseConnector, RemoteFile
from ui import FilePanel, ConnectionDialog, ProgressDialog


class CyberDuckApp(ttk.Window):
    """Ana uygulama penceresi."""

    def __init__(self):
        super().__init__(
            title="DuckTransfer - FTP, SFTP & S3 İstemcisi",
            themename="darkly",
            size=(1200, 750),
            minsize=(900, 500),
        )
        self.connector: BaseConnector | None = None
        self.connection_config: dict | None = None
        self._set_icon()
        self._build_ui()

    def _set_icon(self):
        """Pencere ikonunu ayarla. assets/icon.png dosyasını kullanır."""
        if getattr(sys, "frozen", False):
            base = Path(sys._MEIPASS)
        else:
            base = Path(__file__).parent
        icon_path = base / "assets" / "icon.png"
        if icon_path.exists():
            try:
                from tkinter import PhotoImage
                img = PhotoImage(file=str(icon_path))
                self.iconphoto(True, img)
            except Exception:
                pass

    def _build_ui(self):
        # Üst menü / araç çubuğu
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=X, padx=10, pady=10)

        ttk.Button(toolbar, text="🔌 Yeni Bağlantı", bootstyle=SUCCESS, command=self._open_connection_dialog).pack(side=LEFT, padx=5)
        ttk.Button(toolbar, text="⏏ Bağlantıyı Kes", bootstyle=DANGER, command=self._disconnect).pack(side=LEFT, padx=5)

        ttk.Separator(toolbar, orient=VERTICAL).pack(side=LEFT, fill=Y, padx=15)

        ttk.Button(toolbar, text="⬇ İndir", bootstyle=INFO, command=self._download).pack(side=LEFT, padx=5)
        ttk.Button(toolbar, text="⬆ Yükle", bootstyle=INFO, command=self._upload).pack(side=LEFT, padx=5)
        ttk.Button(toolbar, text="📁 Yeni Klasör", bootstyle=OUTLINE, command=self._create_folder).pack(side=LEFT, padx=5)
        ttk.Button(toolbar, text="🗑 Sil", bootstyle=OUTLINE, command=self._delete).pack(side=LEFT, padx=5)

        self.status_var = ttk.StringVar(value="Hazır - Bağlantı kurmak için 'Yeni Bağlantı' tıklayın")
        ttk.Label(toolbar, textvariable=self.status_var, bootstyle=INVERSE).pack(side=RIGHT, padx=10)

        # Ana içerik - çift panel
        content = ttk.Frame(self)
        content.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # Sol panel - Yerel
        left_frame = ttk.LabelFrame(content, text="Yerel Bilgisayar")
        left_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 5))

        self.local_panel = FilePanel(
            left_frame,
            title="Yerel",
            is_remote=False,
            on_navigate=self._on_local_navigate,
            on_select=self._on_local_select,
            on_double_click=self._on_local_double_click,
        )
        self.local_panel.pack(fill=BOTH, expand=True, padx=5, pady=5)
        self._on_local_navigate(os.path.expanduser("~"))

        # Orta butonlar
        center = ttk.Frame(content)
        center.pack(side=LEFT, fill=Y, padx=5)
        ttk.Button(center, text="→\nYükle", bootstyle=SUCCESS, width=8, command=self._upload).pack(pady=5)
        ttk.Button(center, text="←\nİndir", bootstyle=INFO, width=8, command=self._download).pack(pady=5)

        # Sağ panel - Uzak
        right_frame = ttk.LabelFrame(content, text="Uzak Sunucu (FTP / S3)")
        right_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(5, 0))

        self.remote_panel = FilePanel(
            right_frame,
            title="Uzak",
            is_remote=True,
            on_navigate=self._on_remote_navigate,
            on_select=self._on_remote_select,
            on_double_click=self._on_remote_double_click,
        )
        self.remote_panel.pack(fill=BOTH, expand=True, padx=5, pady=5)
        self.remote_panel.load_items([])  # Başlangıçta boş

    def _open_connection_dialog(self):
        def on_connect(config: dict):
            self.connection_config = config
            self._connect()

        dlg = ConnectionDialog(self, on_connect=on_connect)
        self.wait_window(dlg)

    def _connect(self):
        if not self.connection_config:
            return

        config = self.connection_config
        proto = config.get("protocol", "ftp")

        try:
            if proto in ("ftp", "ftp_ssl"):
                self.connector = FTPConnector()
                self.connector.connect(
                    host=config["host"],
                    port=config.get("port", 21),
                    username=config.get("username", ""),
                    password=config.get("password", ""),
                    use_ssl=(proto == "ftp_ssl"),
                )
                path = self.connector.get_current_path()
            elif proto == "sftp" and SFTPConnector:
                self.connector = SFTPConnector()
                self.connector.connect(
                    host=config["host"],
                    port=config.get("port", 22),
                    username=config.get("username", ""),
                    password=config.get("password", ""),
                )
                path = self.connector.get_current_path()
            elif proto == "s3":
                self.connector = S3Connector()
                self.connector.connect(
                    access_key=config.get("access_key", ""),
                    secret_key=config.get("secret_key", ""),
                    region=config.get("region", "us-east-1"),
                    bucket=config["bucket"],
                )
                path = "" if config.get("protocol") == "s3" else "/"

            display = config.get("host") or config.get("bucket", "S3")
            self.status_var.set(f"Bağlı: {display}")
            self._on_remote_navigate(path)
        except Exception as e:
            messagebox.showerror("Bağlantı Hatası", str(e))
            self.connector = None

    def _disconnect(self):
        if self.connector:
            self.connector.disconnect()
            self.connector = None
        self.remote_panel.load_items([])
        self.remote_panel.set_path("/")
        self.status_var.set("Bağlantı kesildi")

    def _on_local_navigate(self, path: str):
        if not path:
            path = os.path.expanduser("~")
        path = os.path.abspath(path)
        if not os.path.isdir(path):
            path = os.path.dirname(path) or os.path.expanduser("~")
        self.local_panel.set_path(path)
        self.local_panel.load_local_items(path)

    def _on_local_select(self, path: str, is_dir: bool):
        pass

    def _on_local_double_click(self, path: str, is_dir: bool):
        if is_dir:
            self._on_local_navigate(path)
        else:
            # Dosya seçildi - yükleme için
            pass

    def _on_remote_navigate(self, path: str):
        if not self.connector:
            return
        try:
            items = self.connector.list_directory(path)
            self.remote_panel.set_path(path or "/")
            self.remote_panel.load_items(items)
        except Exception as e:
            messagebox.showerror("Hata", str(e))

    def _on_remote_select(self, path: str, is_dir: bool):
        pass

    def _on_remote_double_click(self, path: str, is_dir: bool):
        if is_dir:
            self._on_remote_navigate(path)
        else:
            pass

    def _download(self):
        if not self.connector:
            messagebox.showwarning("Uyarı", "Önce bir bağlantı kurun.")
            return

        sel = self.remote_panel.get_selected()
        if not sel:
            messagebox.showwarning("Uyarı", "İndirilecek dosyayı seçin.")
            return

        remote_path, is_dir = sel
        if is_dir:
            messagebox.showinfo("Bilgi", "Klasör indirme henüz desteklenmiyor. Sadece dosya seçin.")
            return

        local_dir = self.local_panel.current_path
        local_path = os.path.join(local_dir, os.path.basename(remote_path))

        prog = ProgressDialog(self, title="İndiriliyor...")
        prog.update_progress(0, 100, os.path.basename(remote_path))

        def cb(current, total):
            self.after(0, lambda: prog.update_progress(current, total))

        def do_download():
            try:
                self.connector.download_file(remote_path, local_path, progress_callback=cb)
                self.after(0, lambda: (prog.set_complete(True), prog.destroy(), self._on_local_navigate(local_dir)))
            except Exception as e:
                self.after(0, lambda: (prog.destroy(), messagebox.showerror("Hata", str(e))))

        threading.Thread(target=do_download, daemon=True).start()

    def _upload(self):
        if not self.connector:
            messagebox.showwarning("Uyarı", "Önce bir bağlantı kurun.")
            return

        sel = self.local_panel.get_selected()
        if not sel:
            messagebox.showwarning("Uyarı", "Yüklenecek dosyayı seçin.")
            return

        local_path, is_dir = sel
        if is_dir:
            messagebox.showinfo("Bilgi", "Klasör yükleme henüz desteklenmiyor. Sadece dosya seçin.")
            return

        remote_dir = self.remote_panel.current_path
        proto = self.connection_config.get("protocol", "") if self.connection_config else ""
        if proto == "s3":
            remote_path = f"{remote_dir.rstrip('/')}/{os.path.basename(local_path)}".lstrip("/")
        else:
            remote_path = f"{remote_dir.rstrip('/')}/{os.path.basename(local_path)}".replace("//", "/") or f"/{os.path.basename(local_path)}"

        prog = ProgressDialog(self, title="Yükleniyor...")
        prog.update_progress(0, 100, os.path.basename(local_path))

        def cb(current, total):
            self.after(0, lambda: prog.update_progress(current, total))

        def do_upload():
            try:
                self.connector.upload_file(local_path, remote_path, progress_callback=cb)
                self.after(0, lambda: (prog.set_complete(True), prog.destroy(), self._on_remote_navigate(remote_dir)))
            except Exception as e:
                self.after(0, lambda: (prog.destroy(), messagebox.showerror("Hata", str(e))))

        threading.Thread(target=do_upload, daemon=True).start()

    def _create_folder(self):
        if not self.connector:
            messagebox.showwarning("Uyarı", "Önce bir bağlantı kurun.")
            return

        from tkinter import simpledialog
        name = simpledialog.askstring("Yeni Klasör", "Klasör adı:")
        if not name or not name.strip():
            return

        remote_dir = self.remote_panel.current_path
        proto = self.connection_config.get("protocol", "") if self.connection_config else ""
        if proto == "s3":
            path = f"{remote_dir.rstrip('/')}/{name.strip()}".lstrip("/")
        else:
            path = f"{remote_dir.rstrip('/')}/{name.strip()}".replace("//", "/") or f"/{name.strip()}"

        try:
            if self.connector.create_directory(path):
                self._on_remote_navigate(remote_dir)
                self.status_var.set(f"Klasör oluşturuldu: {name}")
            else:
                messagebox.showerror("Hata", "Klasör oluşturulamadı.")
        except Exception as e:
            messagebox.showerror("Hata", str(e))

    def _delete(self):
        if not self.connector:
            messagebox.showwarning("Uyarı", "Önce bir bağlantı kurun.")
            return

        sel = self.remote_panel.get_selected()
        if not sel:
            messagebox.showwarning("Uyarı", "Silinecek öğeyi seçin.")
            return

        path, is_dir = sel
        if not messagebox.askyesno("Onay", f"'{os.path.basename(path)}' silinsin mi?"):
            return

        try:
            if self.connector.delete(path):
                self._on_remote_navigate(self.remote_panel.current_path)
                self.status_var.set("Silindi")
            else:
                messagebox.showerror("Hata", "Silinemedi.")
        except Exception as e:
            messagebox.showerror("Hata", str(e))


def main():
    app = CyberDuckApp()
    app.place_window_center()
    app.mainloop()


if __name__ == "__main__":
    main()
