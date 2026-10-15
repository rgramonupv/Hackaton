"""Run the unchanged app with disposable SQLite storage for browser acceptance tests.

From the repo root:
python -m streamlit run tests/astra_preview.py --server.address 127.0.0.1 --server.port 8511
Stop the server to discard this test database. Never use this entry point for real proposals.
"""
from pathlib import Path
import runpy
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
import db


@st.cache_resource
def temporary_database():
    return tempfile.TemporaryDirectory(prefix="valencia-astra-browser-")


db.DB_PATH = Path(temporary_database().name) / "proposals.db"
runpy.run_path(str(ROOT / "app.py"), run_name="__main__")
