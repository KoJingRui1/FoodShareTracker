import streamlit as st
import pandas as pd
import datetime

def show_admin_page(manager):
    """Render the administrator dashboard page."""
    user = st.session_state.get("user")
    user_name = user.name if user else "Admin"

    st.title(f"Admin Dashboard - Welcome, {user_name}!")
    st.info("Administrator panel initialized.")

    if st.button("Logout"):
        st.session_state.user = None
        st.session_state.current_page = "main"
        st.rerun()


# Functional alias
admin_page = show_admin_page
