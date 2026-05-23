from pathlib import Path
import sys

当前目录 = str(Path(__file__).resolve().parent)
if 当前目录 not in sys.path:
    sys.path.insert(0, 当前目录)

from src.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
