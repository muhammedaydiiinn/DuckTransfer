"""Progress dialog for file transfers."""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *


class ProgressDialog(ttk.Toplevel):
    """Modal progress dialog for upload/download operations."""

    def __init__(self, parent, title: str = "İşlem", **kwargs):
        super().__init__(parent, **kwargs)
        self.title(title)
        self.geometry("400x120")
        self.minsize(350, 100)
        self.resizable(True, True)

        self.transient(parent)
        self.grab_set()

        main = ttk.Frame(self)
        main.pack(fill=BOTH, expand=True, padx=20, pady=20)
        main.columnconfigure(0, weight=1)

        self.label_var = ttk.StringVar(value="Hazırlanıyor...")
        ttk.Label(main, textvariable=self.label_var).pack(anchor=W, pady=(0, 10))

        self.progress = ttk.Progressbar(main, bootstyle=SUCCESS, mode="determinate")
        self.progress.pack(fill=X, pady=5, expand=True)

        self.percent_var = ttk.StringVar(value="0%")
        ttk.Label(main, textvariable=self.percent_var).pack(anchor=E, pady=2)

    def update_progress(self, current: int, total: int, label: str = ""):
        if total > 0:
            pct = min(100, int(100 * current / total))
            self.progress["value"] = pct
            self.percent_var.set(f"{pct}%")
        if label:
            self.label_var.set(label)

    def set_complete(self, success: bool = True):
        self.progress["value"] = 100
        self.percent_var.set("100%")
        self.label_var.set("Tamamlandı!" if success else "Hata!")
