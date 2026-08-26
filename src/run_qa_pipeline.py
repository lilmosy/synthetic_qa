from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "src" / "build_qa.py"), "--validate"],
        cwd=ROOT,
        check=True,
    )
    print("synthetic QA pipeline complete")


if __name__ == "__main__":
    main()
