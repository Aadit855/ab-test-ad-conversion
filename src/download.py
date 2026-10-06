"""Download the marketing A/B test dataset (Kaggle 'marketing AB testing', mirrored) and verify its checksum."""
import hashlib
import urllib.request
from pathlib import Path

URL = "https://github.com/jszymon/uplift_sklearn_data/releases/download/marketing_AB/marketing_AB.csv.gz"
SHA256 = "a318767a73785b7e54fbf36cbf3004115f61e943844b7ac8d3753a893e093d9d"
DEST = Path(__file__).resolve().parents[1] / "data" / "raw" / "marketing_AB.csv.gz"


def main() -> None:
    DEST.parent.mkdir(parents=True, exist_ok=True)
    if not DEST.exists():
        urllib.request.urlretrieve(URL, DEST)
    digest = hashlib.sha256(DEST.read_bytes()).hexdigest()
    if digest != SHA256:
        raise SystemExit(f"Checksum mismatch for {DEST}: {digest}")
    print(f"Verified {DEST.name} ({digest[:12]}...)")


if __name__ == "__main__":
    main()
