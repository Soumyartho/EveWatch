"""Streamlit entry point.

Run with:  streamlit run app.py
"""

import streamlit as st

from evewatch.views import dashboard

st.set_page_config(page_title="EveWatch - BB84 simulator", page_icon=":material/key:", layout="wide")

dashboard.render()
