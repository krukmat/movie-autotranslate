from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
PROC_DIR = DATA_DIR / "proc"
RAW_DIR = DATA_DIR / "raw"
PUB_DIR = DATA_DIR / "pub"


def asset_workspace(asset_external_id: str) -> Path:
    path = PROC_DIR / asset_external_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def asset_public_dir(asset_external_id: str) -> Path:
    path = PUB_DIR / asset_external_id
    path.mkdir(parents=True, exist_ok=True)
    return path
