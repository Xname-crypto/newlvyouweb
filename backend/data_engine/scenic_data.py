from __future__ import annotations

from pathlib import Path


SCENIC_INFO_XLSX = "旅游景点_含开放信息_配图.xlsx"
SCENIC_XLSX_SIZE = 479040


def find_scenic_xlsx() -> Path:
    data_engine_dir = Path(__file__).resolve().parent
    backend_dir = data_engine_dir.parent
    repo_root = backend_dir.parent

    candidates = [
        data_engine_dir / "data" / SCENIC_INFO_XLSX,
        backend_dir / SCENIC_INFO_XLSX,
        repo_root / SCENIC_INFO_XLSX,
    ]

    for path in candidates:
        if path.exists():
            return path

    for root in (data_engine_dir / "data", backend_dir, repo_root):
        if not root.exists():
            continue
        for path in root.glob("*.xlsx"):
            try:
                if path.stat().st_size == SCENIC_XLSX_SIZE:
                    return path
            except OSError:
                continue

    raise FileNotFoundError("scenic xlsx file not found")
