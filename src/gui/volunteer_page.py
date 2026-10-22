import os
import streamlit as st
import pandas as pd
import datetime
from src.app.donor import DonorUser
from src.app.utils import verify_password


# =========================================================
# Success Page
# =========================================================

def success_page(title, message, detail, return_page):
    st.title(title)
    st.success(message)

    if detail:
        st.write(detail)

    if st.button("OK"):
        st.session_state.donor_page = return_page
        if "selected_donation_id" in st.session_state:
            del st.session_state.selected_donation_id
        st.rerun()


# =========================================================
# Donor Dashboard & Main Page
# =========================================================

def show_volunteer_page(manager, user):
    """Render the donor portal page with donation, history, and profile features."""
    # Sidebar avatar style
    st.sidebar.markdown(
        """
        <style>
        [data-testid="stSidebar"] img {
            border-radius: 50%;
            object-fit: cover;
            aspect-ratio: 1 / 1;
            margin: 0 auto;
            display: block;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.sidebar.image(user.profile_image, width="stretch")
    st.sidebar.markdown(f"### {user.name}")
    st.sidebar.caption("volunteer")
    st.sidebar.divider()

    if "volunteer_page" not in st.session_state:
        st.session_state.donor_page = "job"

    if st.sidebar.button("My Job", width="stretch"):
        st.session_state.donor_page = "job"

    if st.sidebar.button("Get a Job", width="stretch"):
        st.session_state.donor_page = "Donate"

    if st.sidebar.button("Profile", width="stretch"):
        st.session_state.donor_page = "Profile"

    st.sidebar.divider()
    if st.sidebar.button("Logout", width="stretch"):
        st.session_state.user = None
        st.session_state.current_page = "main"
        st.rerun()

    page = st.session_state.donor_page