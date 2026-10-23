import sys
from pathlib import Path
import streamlit as st

# Ensure project root directory is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.app.FoodBank import FoodBankManager
from src.gui.new_system_page import show_new_system_page
from src.gui.main_page import show_main_page
from src.gui.admin_page import show_admin_page
from src.gui.staff_page import show_staff_page
from src.gui.donor_page import show_donor_page
from src.gui.volunteer_page import show_volunteer_page
from src.gui.client_page import show_client_page


def launch():
    """Main application entry point and router."""
    st.set_page_config(
        page_title="Foodshare Tracker",
        page_icon="🍲",
        layout="wide"
    )

    if "manager" not in st.session_state:
        st.session_state.manager = FoodBankManager()

    manager = st.session_state.manager

    # Load data from file if data file exists
    if manager.data_path.exists():
        manager.load_data()
        if not manager.get_all_users():
            next_user_id = 0
        else:
            next_user_id = manager.food_bank_data.get("next_user_id", 1)
    else:
        # No data file exists yet; treat system as brand new (next_user_id == 0)
        next_user_id = 0

    # Initialize current_page state if not yet set
    if "current_page" not in st.session_state:
        st.session_state.current_page = "new_system" if next_user_id == 0 else "main"

    # Route based on system status and session page
    if next_user_id == 0:
        st.session_state.current_page = "new_system"
        show_new_system_page(manager)
    elif st.session_state.current_page == "admin":
        user = st.session_state.get("user")
        if user is None:
            # If not logged in, redirect to main/login page
            st.session_state.current_page = "main"
            st.rerun()
        else:
            show_admin_page(manager, user)
    elif st.session_state.current_page == "staff":
        user = st.session_state.get("user")
        if user is None:
            # If not logged in, redirect to main/login page
            st.session_state.current_page = "main"
            st.rerun()
        else:
            show_staff_page(manager, user)
    elif st.session_state.current_page == "donor":
        user = st.session_state.get("user")
        if user is None:
            # If not logged in, redirect to main/login page
            st.session_state.current_page = "main"
            st.rerun()
        else:
            show_donor_page(manager, user)
    elif st.session_state.current_page == "volunteer":
        user = st.session_state.get("user")
        if user is None:
            # If not logged in, redirect to main/login page
            st.session_state.current_page = "main"
            st.rerun()
        else:
            show_volunteer_page(manager, user)
    elif st.session_state.current_page == "client":
        user = st.session_state.get("user")
        if user is None:
            # If not logged in, redirect to main/login page
            st.session_state.current_page = "main"
            st.rerun()
        else:
            show_client_page(manager, user)
    else:
        st.session_state.current_page = "main"
        show_main_page(manager)


if __name__ == "__main__":
    launch()
