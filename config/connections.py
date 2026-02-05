"""Kayıtlı bağlantı yönetimi."""

import json
import os
from pathlib import Path


CONFIG_DIR = Path.home() / ".config" / "ducktransfer"
CONNECTIONS_FILE = CONFIG_DIR / "connections.json"


def _ensure_config_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_connections() -> list[dict]:
    """Kayıtlı bağlantıları yükle."""
    _ensure_config_dir()
    if not CONNECTIONS_FILE.exists():
        return []
    try:
        with open(CONNECTIONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("connections", [])
    except (json.JSONDecodeError, IOError):
        return []


def save_connections(connections: list[dict]) -> None:
    """Bağlantıları kaydet."""
    _ensure_config_dir()
    with open(CONNECTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump({"connections": connections}, f, indent=2, ensure_ascii=False)


def add_connection(name: str, config: dict) -> None:
    """Yeni bağlantı ekle veya güncelle."""
    connections = load_connections()
    config_copy = {**config, "name": name}
    # Aynı isimde varsa güncelle
    connections = [c for c in connections if c.get("name") != name]
    connections.append(config_copy)
    save_connections(connections)


def remove_connection(name: str) -> None:
    """Bağlantıyı sil."""
    connections = [c for c in load_connections() if c.get("name") != name]
    save_connections(connections)
