#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/00_fetch_assets.py
.venv/bin/python scripts/00_align.py
.venv/bin/python scripts/01_prepare.py
.venv/bin/python scripts/02_analyze.py
.venv/bin/python scripts/03_render.py
.venv/bin/python scripts/04_polish_pdf.py
.venv/bin/python scripts/05_validate.py