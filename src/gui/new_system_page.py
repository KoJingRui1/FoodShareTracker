import streamlit as st


def show_new_system_page(manager):
    """Render the new system initialization page."""
    st.title("System Initialization")
    st.info("Welcome to Foodshare Tracker. Please enter the following information to initialize the system.")
    st.subheader("Create the First Admin")
    name = st.text_input("Please enter the name of the First Admin.")
    password = st.text_input("Please enter the password of the First Admin", type="password")
    confirm_password = st.text_input("Please confirm the password of the First Admin", type="password")
    email = st.text_input("Please enter the email of the First Admin", type="email")
    confirm_email = st.text_input("Please confirm the email of the First Admin", type="email")

    if confirm_password and password != confirm_password:
        st.error("The passwords do not match. Please re-enter.")

    if confirm_email and email.strip().lower() != confirm_email.strip().lower():
        st.error("The email addresses do not match. Please re-enter.")

    if st.button("Create First Admin", type="primary"):
        # Check required fields
        if not name or not password or not confirm_password or not email or not confirm_email:
            st.error("Please fill in all the required fields.")
            return

        # Check password match
        if password != confirm_password:
            st.error("The passwords do not match. Please re-enter.")
            return

        # Check email match
        if email.strip().lower() != confirm_email.strip().lower():
            st.error("The email addresses do not match. Please re-enter.")
            return

        # Validate name
        is_name_valid, name_reason = manager.validate_name(name)
        if not is_name_valid:
            st.error(f"Invalid name: {name_reason}")
            return

        # Validate password strength
        is_pwd_valid, pwd_reason = manager.validate_password(password)
        if not is_pwd_valid:
            st.error(f"Invalid password: {pwd_reason}")
            return

        # Validate email format
        clean_email = email.strip()
        if "@" not in clean_email or "." not in clean_email.split("@")[-1]:
            st.error("Please enter a valid email address.")
            return

        # Check for existing email
        if manager.find_user_by_email(clean_email) is not None:
            st.error(f"Email '{clean_email}' is already registered.")
            return

        try:
            admin = manager.add_admin(name=name.strip(), password=password, email=clean_email)
            st.success(f"First administrator '{admin.name}' successfully created!")
            st.session_state.user = admin
            st.session_state.current_page = "main"
            st.rerun()
        except Exception as e:
            st.error(f"Failed to create administrator: {e}")


