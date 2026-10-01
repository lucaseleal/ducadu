"""
Ducadu — demonstração iFood homologação (Financial + Analytics + Review, read-only).

Run from repo root:
  uv run --project apps/ifood_homolog streamlit run apps/ifood_homolog/app.py

Embutido no admin TanStack (apps/admin) via iframe — ver apps/admin/README.md.
"""
from __future__ import annotations

import streamlit as st

from ifood_dashboard import render_homolog_dashboard


def main() -> None:
    st.set_page_config(
        page_title="Ducadu × iFood — Homologação",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.title("Ducadu — Painel iFood (homologação)")
    render_homolog_dashboard(show_page_header=False)


if __name__ == "__main__":
    main()
