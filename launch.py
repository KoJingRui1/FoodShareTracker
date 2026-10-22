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

    # Route to new system setup if next_user_id is 0, else go to main page
    if next_user_id == 0:
        st.session_state.current_page = "new_system"
        show_new_system_page(manager)
    else:
        st.session_state.current_page = "main"
        show_main_page(manager)


if __name__ == "__main__":
    launch()
