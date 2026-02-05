"""Dual-pane file browser panels."""

import os
import tkinter as tk
from tkinter import messagebox
from typing import Callable, Optional

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from connectors.base import RemoteFile


def format_size(size: int) -> str:
    """Format file size for display."""
    if size == 0:
        return "-"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


class FilePanel(ttk.Frame):
    """Single file browser panel (local or remote)."""

    def __init__(
        self,
        parent,
        title: str,
        is_remote: bool = False,
        on_navigate: Optional[Callable[[str], None]] = None,
        on_select: Optional[Callable[[str, bool], None]] = None,
        on_double_click: Optional[Callable[[str, bool], None]] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        self.title = title
        self.is_remote = is_remote
        self.on_navigate = on_navigate
        self.on_select = on_select
        self.on_double_click = on_double_click
        self.current_path = "/" if is_remote else os.path.expanduser("~")
        self.selected_path: Optional[str] = None
        self.selected_is_dir: bool = False
        self._items: list[RemoteFile] = []
        self.show_hidden = False
        self._build_ui()

    def _build_ui(self):
        header = ttk.Frame(self)
        header.pack(fill=X, padx=5, pady=(5, 2))

        ttk.Label(header, text=self.title, font=("Helvetica", 11, "bold")).pack(side=LEFT)

        if not self.is_remote:
            self.show_hidden_var = tk.BooleanVar(value=False)
            self.hidden_cb = ttk.Checkbutton(
                header, text="Gizli dosyalar", variable=self.show_hidden_var,
                command=self._on_show_hidden_change
            )
            self.hidden_cb.pack(side=LEFT, padx=(10, 0))

        self.path_var = ttk.StringVar(value=self.current_path)
        path_entry = ttk.Entry(header, textvariable=self.path_var, width=50)
        path_entry.pack(side=LEFT, fill=X, expand=True, padx=(10, 5), pady=2)
        path_entry.bind("<Return>", lambda e: self._go_to_path())

        ttk.Button(header, text="↺", bootstyle=OUTLINE, width=3, command=self.refresh).pack(side=LEFT, padx=2)
        ttk.Button(header, text="↑", bootstyle=OUTLINE, width=3, command=self._go_up).pack(side=LEFT, padx=2)

        self.tree_frame = ttk.Frame(self)
        self.tree_frame.pack(fill=BOTH, expand=True, padx=5, pady=5)

        columns = ("name", "size", "modified")
        self.tree = ttk.Treeview(
            self.tree_frame,
            columns=columns,
            show="headings",
            height=15,
            selectmode="browse",
            bootstyle="secondary"
        )
        self.tree.heading("name", text="İsim")
        self.tree.heading("size", text="Boyut")
        self.tree.heading("modified", text="Değiştirilme")
        self.tree.column("name", width=250, minwidth=150)
        self.tree.column("size", width=80, minwidth=60)
        self.tree.column("modified", width=120, minwidth=80)

        scrollbar = ttk.Scrollbar(self.tree_frame)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.configure(command=self.tree.yview)

        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<BackSpace>", lambda e: self._go_up())

    def _on_show_hidden_change(self):
        if not self.is_remote and hasattr(self, "show_hidden_var"):
            self.show_hidden = self.show_hidden_var.get()
            self.refresh()

    def _go_to_path(self):
        path = self.path_var.get().strip()
        if self.on_navigate:
            self.on_navigate(path)

    def _go_up(self):
        if self.is_remote:
            parts = self.current_path.rstrip("/").split("/")
            if len(parts) > 1:
                parent = "/".join(parts[:-1]) or "/"
                if self.on_navigate:
                    self.on_navigate(parent)
        else:
            parent = os.path.dirname(self.current_path.rstrip("/")) or "/"
            if self.on_navigate:
                self.on_navigate(parent)

    def _on_select(self, event):
        sel = self.tree.selection()
        if sel:
            item = self.tree.item(sel[0])
            idx = self.tree.index(sel[0])
            if 0 <= idx < len(self._items):
                f = self._items[idx]
                self.selected_path = f.path
                self.selected_is_dir = f.is_directory
                if self.on_select:
                    self.on_select(f.path, f.is_directory)

    def _on_double_click(self, event):
        sel = self.tree.selection()
        if sel:
            idx = self.tree.index(sel[0])
            if 0 <= idx < len(self._items):
                f = self._items[idx]
                if self.on_double_click:
                    self.on_double_click(f.path, f.is_directory)

    def set_path(self, path: str):
        self.current_path = path
        self.path_var.set(path if path else "/")

    def refresh(self):
        if self.on_navigate:
            self.on_navigate(self.current_path)

    def load_items(self, items: list[RemoteFile]):
        self._items = items
        for i in self.tree.get_children():
            self.tree.delete(i)

        for f in items:
            size_str = format_size(f.size) if not f.is_directory else "<DIR>"
            mod_str = f.modified or "-"
            name = f.name + "/" if f.is_directory and not f.name.endswith("/") else f.name
            self.tree.insert("", END, values=(name, size_str, mod_str))

    def load_local_items(self, path: str):
        items = []
        show_hidden = getattr(self, "show_hidden", False)
        if not self.is_remote and hasattr(self, "show_hidden_var"):
            show_hidden = self.show_hidden_var.get()
        try:
            for entry in os.scandir(path):
                try:
                    if not show_hidden and entry.name.startswith("."):
                        continue
                    items.append(RemoteFile(
                        name=entry.name,
                        path=entry.path,
                        size=entry.stat().st_size if entry.is_file() else 0,
                        is_directory=entry.is_dir(),
                        modified=None
                    ))
                except OSError:
                    pass
            items.sort(key=lambda x: (not x.is_directory, x.name.lower()))
            self.load_items(items)
        except PermissionError:
            messagebox.showerror("Hata", "Bu dizine erişim izniniz yok.")
        except Exception as e:
            messagebox.showerror("Hata", str(e))

    def get_selected(self) -> Optional[tuple[str, bool]]:
        if self.selected_path:
            return (self.selected_path, self.selected_is_dir)
        return None
