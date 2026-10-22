import streamlit as st


def show_main_page(manager):
    """Render the main landing and login page."""
    st.title("Foodshare Tracker - Main Page")
    st.write("Welcome to Foodshare Tracker. System is ready.")


# Functional alias
main_page = show_main_page
