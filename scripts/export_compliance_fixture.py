from __future__ import annotations

import argparse
from pathlib import Path

from backend.app.contracts import CapabilityFlags
from backend.app.services.export import export_docx
from backend.app.services.parse import normalize_text_input


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = PROJECT_ROOT / "examples" / "compliance" / "sample-text-basic.md"


def build_fixture(output_path: Path, source_path: Path = DEFAULT_SOURCE) -> Path:
    thesis = normalize_text_input(source_path.read_text(encoding="utf-8"), CapabilityFlags(docx_export=True, profile="undergraduate"))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(export_docx(thesis))
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Export a SCNU DOCX fixture for compliance CI.")
    parser.add_argument("output_path", type=Path)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    args = parser.parse_args()
    path = build_fixture(args.output_path, args.source)
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
