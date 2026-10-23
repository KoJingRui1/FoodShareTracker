import os
import base64
import streamlit as st
from src.app.utils import verify_password
from src.app.admin import AdminUser
from src.app.staff import StaffUser
from src.app.volunteer import VolunteerUser
from src.app.donor import DonorUser
from src.app.client import ClientUser


def show_main_page(manager):
    """Render the public landing page with continuous vertical scroll and anchor navigation."""
    # Load hero banner background
    banner_path = os.path.join("assets", "hero_banner.png")
    b64_bg = ""
    if os.path.exists(banner_path):
        with open(banner_path, "rb") as f:
            b64_bg = base64.b64encode(f.read()).decode("utf-8")

    bg_css = f'url("data:image/png;base64,{b64_bg}") center center / cover no-repeat' if b64_bg else 'linear-gradient(135deg, rgba(255,75,75,0.08) 0%, rgba(30,144,255,0.08) 100%)'

    # Enable smooth scrolling and sidebar navigation styling
    st.markdown(
        f"""
        <style>
        html {{
            scroll-behavior: smooth;
        }}
        .nav-anchor-link {{
            display: block;
            padding: 9px 14px;
            margin: 4px 0;
            border-radius: 8px;
            text-decoration: none !important;
            color: inherit;
            font-size: 0.95rem;
            font-weight: 500;
            border: 1px solid rgba(128, 128, 128, 0.2);
            background: rgba(128, 128, 128, 0.05);
            transition: all 0.2s ease-in-out;
        }}
        .nav-anchor-link:hover {{
            background: rgba(255, 75, 75, 0.1);
            border-color: #ff4b4b;
            color: #ff4b4b !important;
            transform: translateX(3px);
        }}
        .hero-container {{
            padding: 55px 35px;
            border-radius: 14px;
            background: linear-gradient(rgba(0, 0, 0, 0.55), rgba(0, 0, 0, 0.65)), {bg_css};
            border: 1px solid rgba(255, 255, 255, 0.2);
            margin-bottom: 30px;
            box-shadow: 0 4px 18px rgba(0, 0, 0, 0.2);
        }}
        .hero-title {{
            color: #ffffff !important;
            font-size: 2.2rem !important;
            font-weight: 700;
            margin-bottom: 14px;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
        }}
        .hero-subtitle {{
            font-size: 1.15rem;
            color: #f5f5f5 !important;
            line-height: 1.6;
            margin-bottom: 0px;
            text-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
        }}
        .stat-card {{
            padding: 16px;
            border-radius: 10px;
            background: rgba(128, 128, 128, 0.06);
            border: 1px solid rgba(128, 128, 128, 0.15);
            text-align: center;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

    # =========================================================
    # Sidebar Anchor Navigation
    # =========================================================
    st.sidebar.markdown("**Navigation Menu**")
    st.sidebar.markdown(
        """
        <a class="nav-anchor-link" href="#hero" target="_self">🏠 Home & Welcome</a>
        <a class="nav-anchor-link" href="#about" target="_self">ℹ️ About Our Mission</a>
        <a class="nav-anchor-link" href="#stations" target="_self">📍 Drop-off Stations</a>
        <a class="nav-anchor-link" href="#impact" target="_self">📊 Community Impact</a>
        <a class="nav-anchor-link" href="#volunteer" target="_self">🤝 Volunteer With Us</a>
        <a class="nav-anchor-link" href="#portal" target="_self">🔐 Portal Login & Register</a>
        <a class="nav-anchor-link" href="#contacts" target="_self">👥 Team & Contacts</a>
        """,
        unsafe_allow_html=True
    )

    st.sidebar.divider()
    st.sidebar.info("💡 Tip: Click any menu item above to glide straight to that section.")

    # =========================================================
    # Section 1: Hero Banner (#hero)
    # =========================================================
    st.markdown('<div id="hero"></div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="hero-container">
            <div class="hero-title">FoodShare Tracker- A Human-Centred Food Bank Management system.</div>
            <div class="hero-subtitle">
                A lightweight, Python-based software solution designed to support community food banks, charities, and local support organisations in managing food donations, stock, client needs, volunteer tasks, and food distribution.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    col_cta1, col_cta2, col_cta3 = st.columns(3)
    with col_cta1:
        st.markdown(
            """
            <a href="#portal" target="_self" style="text-decoration:none;">
                <div class="stat-card" style="cursor:pointer;">
                    <h4>🎁 Donate Food</h4>
                    <p style="color:gray; font-size:0.9rem;">Contribute surplus groceries or items to our distribution stations.</p>
                </div>
            </a>
            """,
            unsafe_allow_html=True
        )
    with col_cta2:
        st.markdown(
            """
            <a href="#portal" target="_self" style="text-decoration:none;">
                <div class="stat-card" style="cursor:pointer;">
                    <h4>🍲 Request Assistance</h4>
                    <p style="color:gray; font-size:0.9rem;">Sign up confidentially to receive tailored food relief hampers.</p>
                </div>
            </a>
            """,
            unsafe_allow_html=True
        )
    with col_cta3:
        st.markdown(
            """
            <a href="#volunteer" target="_self" style="text-decoration:none;">
                <div class="stat-card" style="cursor:pointer;">
                    <h4>🤝 Join as Volunteer</h4>
                    <p style="color:gray; font-size:0.9rem;">Help us collect donations and deliver life-changing meal hampers.</p>
                </div>
            </a>
            """,
            unsafe_allow_html=True
        )

    st.write("")
    st.divider()

    # =========================================================
    # Section 2: About Our Mission (#about)
    # =========================================================

    st.markdown('<div id="about"></div>', unsafe_allow_html=True)
    st.subheader("ℹ️ About Our Mission")

    col_ab1, col_ab2 = st.columns(2)
    with col_ab1:
        st.markdown("#### Who We Are")
        desc = getattr(manager, "description", "") or "A community-driven food banking initiative dedicated to zero food waste and zero hunger."
        st.write(desc)
        addr = getattr(manager, "address", "") or "Central Distribution Center, Main Headquarters"
        st.write(f"**Main Headquarters:** {addr}")

    with col_ab2:
        st.markdown("#### Credits")
        st.write("Github Pages: https://github.com/KoJingRui1/FoodShareTracker")
        st.write("Made by: Monash University Malaysia FIT1056 Team 16 Ko Jing Rui")        
        st.write("Made in: 23/10/2026")
    st.write("")
    st.divider()

    # =========================================================
    # Section 3: Drop-off Stations & Collection Centers (#stations)
    # =========================================================

    st.markdown('<div id="stations"></div>', unsafe_allow_html=True)
    st.subheader("📍 Neighborhood Drop-off Stations")
    st.caption("Donors can bring non-perishable groceries and fresh produce to any of the verified collection centers below.")

    stations = manager.get_stations()
    if not stations:
        st.info("No regional collection centers registered at the moment. Please contact our main headquarters.")
    else:
        st_cols = st.columns(2)
        for i, s in enumerate(stations):
            with st_cols[i % 2]:
                with st.container(border=True):
                    s_name = s.get("name", "Station")
                    s_id = s.get("id", "N/A")
                    s_addr = s.get("address", "N/A")
                    st.markdown(f"##### 📍 {s_name}")
                    st.markdown(f"**Address:** {s_addr}")
                    st.caption(f"Station ID: #{s_id}")

    st.write("")
    st.divider()

    # =========================================================
    # Section 4: Live Community Impact & Statistics (#impact)
    # =========================================================

    st.markdown('<div id="impact"></div>', unsafe_allow_html=True)
    st.subheader("📊 Live Community Impact")
    st.caption("Transparent real-time statistics tracking our shared relief efforts.")

    m1, m2, m3, m4 = st.columns(4)
    total_donations = len(manager.donations)
    total_hampers = len(manager.food_hampers)
    total_volunteers = len(manager.volunteers)
    total_inventory_items = len(manager.get_inventory_items())

    with m1:
        st.metric("Total Donations", f"{total_donations}")
    with m2:
        st.metric("Hampers Distributed", f"{total_hampers}")
    with m3:
        st.metric("Active Volunteers", f"{total_volunteers}")
    with m4:
        st.metric("Catalogued Food Varieties", f"{total_inventory_items}")

    st.write("")
    st.divider()

    # =========================================================
    # Section 5: Volunteer Application Form (#volunteer)
    # =========================================================

    st.markdown('<div id="volunteer"></div>', unsafe_allow_html=True)
    st.subheader("🤝 Volunteer With Us")
    st.write(
        "Volunteers are the backbone of our mission! Whether you have a vehicle to pick up food donations "
        "or time on weekends to deliver hampers to vulnerable seniors, your support makes a profound difference."
    )

    with st.form("volunteer_application_form", clear_on_submit=True):
        st.markdown("##### Submit Volunteer Application")
        c_v1, c_v2 = st.columns(2)
        with c_v1:
            v_name = st.text_input("Full Name *", placeholder="Jane Doe")
            v_email = st.text_input("Email Address *", placeholder="jane@example.com")
            v_desc = st.text_input("Availability / Vehicle Details", placeholder="e.g. Free Saturdays, possess standard hatchback car")
        with c_v2:
            v_pwd = st.text_input("Desired Password *", type="password", placeholder="At least 6 chars, letters & numbers")
            v_pwd_conf = st.text_input("Confirm Password *", type="password", placeholder="Re-enter desired password")

        v_submit = st.form_submit_button("Submit Volunteer Application", width="stretch")

        if v_submit:
            if not v_name.strip() or not v_email.strip() or not v_pwd.strip() or not v_pwd_conf.strip():
                st.error("Please fill in your name, email, and password confirmation.")
            elif not manager.valid_name(v_name):
                st.error("Invalid name. Please enter a valid name.")
            elif not manager.valid_password(v_pwd):
                st.error("Password must be at least 6 characters and include letters and numbers.")
            elif v_pwd != v_pwd_conf:
                st.error("Passwords do not match. Please re-enter.")
            elif "@" not in v_email or "." not in v_email.split("@")[-1]:
                st.error("Please provide a valid email address.")
            elif manager.find_user_by_email(v_email.strip()) is not None:
                st.error(f"Email '{v_email.strip()}' is already registered in our system.")
            else:
                try:
                    manager.apply_volunteer(
                        name=v_name.strip(),
                        password=v_pwd,
                        email=v_email.strip(),
                        description=v_desc.strip()
                    )
                    st.success("🎉 Thank you! Your volunteer application has been submitted. Our team will review and approve it shortly.")
                except Exception as e:
                    st.error(f"Failed to submit application: {e}")

    st.write("")
    st.divider()

    # =========================================================
    # Section 6: Portal Login & Registration (#portal)
    # =========================================================

    st.markdown('<div id="portal"></div>', unsafe_allow_html=True)
    st.subheader("🔐 Member Portal: Sign In & Register")
    st.caption("Access your personal dashboard according to your role.")

    tab_signin, tab_reg_donor, tab_reg_client = st.tabs(["🔑 Sign In", "🎁 Register as Donor", "🍲 Register as Client"])

    # 1. Sign In Tab
    with tab_signin:
        st.markdown("##### Sign In to Your Account")
        with st.form("signin_form"):
            login_identifier = st.text_input("Email Address or User ID", placeholder="Enter your email or ID (e.g. user@example.com or 1)")
            login_password = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Sign In", width="stretch")

            if submit_login:
                if not login_identifier.strip() or not login_password:
                    st.error("Please enter both Email/ID and password.")
                else:
                    found_user = manager.find_user_by_email_or_id(login_identifier.strip())
                    if found_user is None or not verify_password(login_password, found_user.password):
                        st.error("Invalid email/ID or password.")
                    else:
                        st.session_state.user = found_user
                        # Determine role for routing
                        if isinstance(found_user, AdminUser):
                            st.session_state.current_page = "admin"
                        elif isinstance(found_user, StaffUser):
                            st.session_state.current_page = "staff"
                        elif isinstance(found_user, VolunteerUser):
                            st.session_state.current_page = "volunteer"
                        elif isinstance(found_user, DonorUser):
                            st.session_state.current_page = "donor"
                        elif isinstance(found_user, ClientUser):
                            st.session_state.current_page = "client"
                        else:
                            st.session_state.current_page = "admin"

                        st.success(f"Welcome back, {found_user.name}!")
                        st.rerun()

    # 2. Register as Donor Tab
    with tab_reg_donor:
        st.markdown("##### Create a Donor Account")
        with st.form("reg_donor_form"):
            c_d1, c_d2 = st.columns(2)
            with c_d1:
                d_name = st.text_input("Full Name *")
                d_email = st.text_input("Email Address *")
            with c_d2:
                d_pwd = st.text_input("Password *", type="password")
                d_pwd_conf = st.text_input("Confirm Password *", type="password")

            submit_donor_reg = st.form_submit_button("Register as Donor", width="stretch")

            if submit_donor_reg:
                if not d_name.strip() or not d_email.strip() or not d_pwd or not d_pwd_conf:
                    st.error("All fields are required including password confirmation.")
                elif not manager.valid_name(d_name):
                    st.error("Invalid name.")
                elif not manager.valid_password(d_pwd):
                    st.error("Password must be at least 6 characters and contain letters and numbers.")
                elif d_pwd != d_pwd_conf:
                    st.error("Passwords do not match.")
                elif "@" not in d_email or "." not in d_email.split("@")[-1]:
                    st.error("Please provide a valid email address.")
                elif manager.find_user_by_email(d_email.strip()) is not None:
                    st.error(f"Email '{d_email.strip()}' is already registered.")
                else:
                    try:
                        new_donor = manager.add_donor(d_name.strip(), d_pwd, d_email.strip())
                        st.session_state.user = new_donor
                        st.session_state.current_page = "donor"
                        st.success("Donor account created successfully! Redirecting...")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Registration failed: {e}")

    # 3. Register as Client Tab
    with tab_reg_client:
        st.markdown("##### Apply for Food Assistance (Confidential Registration)")
        with st.form("reg_client_form"):
            c_c1, c_c2 = st.columns(2)
            with c_c1:
                cl_name = st.text_input("Full Name *")
                cl_email = st.text_input("Email Address *")
                cl_address = st.text_input("Home / Delivery Address *")
            with c_c2:
                cl_pwd = st.text_input("Password *", type="password")
                cl_pwd_conf = st.text_input("Confirm Password *", type="password")
                cl_allergies = st.text_input("Allergies (comma-separated, optional)")

            cl_notes = st.text_area("Family Situation / Dietary Notes (Optional)", placeholder="e.g. Household of 3, seeking monthly support")

            submit_client_reg = st.form_submit_button("Register for Food Assistance", width="stretch")

            if submit_client_reg:
                if not cl_name.strip() or not cl_email.strip() or not cl_pwd or not cl_pwd_conf or not cl_address.strip():
                    st.error("Please provide your name, email, password, password confirmation, and home address.")
                elif not manager.valid_name(cl_name):
                    st.error("Invalid name.")
                elif not manager.valid_password(cl_pwd):
                    st.error("Password must be at least 6 characters and contain letters and numbers.")
                elif cl_pwd != cl_pwd_conf:
                    st.error("Passwords do not match.")
                elif "@" not in cl_email or "." not in cl_email.split("@")[-1]:
                    st.error("Please provide a valid email address.")
                elif manager.find_user_by_email(cl_email.strip()) is not None:
                    st.error(f"Email '{cl_email.strip()}' is already registered.")
                else:
                    try:
                        new_cl = manager.add_client(
                            name=cl_name.strip(),
                            password=cl_pwd,
                            email=cl_email.strip(),
                            description=cl_notes.strip(),
                            address=cl_address.strip()
                        )
                        if cl_allergies.strip():
                            parsed = [a.strip() for a in cl_allergies.split(",") if a.strip()]
                            manager.update_user(new_cl.id, allergy=parsed)

                        st.session_state.user = new_cl
                        st.session_state.current_page = "client"
                        st.success("Client account registered successfully! Redirecting...")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Registration failed: {e}")

    # =========================================================
    # Section 7: Team & Contact Information (#contacts)
    # =========================================================

    st.write("")
    st.divider()
    st.markdown('<div id="contacts"></div>', unsafe_allow_html=True)
    st.subheader("👥 Leadership & Operations Team")
    st.caption("Get in touch with our team members for program details, partnerships, and operational assistance.")

    col_adm, col_stf = st.columns(2)

    with col_adm:
        st.markdown("#### 🛡️ Administrators")
        admins = manager.admins
        if not admins:
            st.info("No administrators registered.")
        else:
            for a in admins:
                with st.container(border=True):
                    c1, c2 = st.columns([1, 3])
                    with c1:
                        img_path = getattr(a, "profile_image", "assets/default_avatar.png")
                        if os.path.exists(img_path):
                            st.image(img_path, width=70)
                        else:
                            st.markdown("🛡️")
                    with c2:
                        st.markdown(f"**{a.name}**")
                        st.caption(f"Admin Staff")
                        st.markdown(f"[{a.email}](mailto:{a.email})")

    with col_stf:
        st.markdown("#### 👷 Operational Staff")
        staffs = manager.staffs
        if not staffs:
            st.info("No operational staff registered currently.")
        else:
            for s in staffs:
                with st.container(border=True):
                    c1, c2 = st.columns([1, 3])
                    with c1:
                        img_path = getattr(s, "profile_image", "assets/default_avatar.png")
                        if os.path.exists(img_path):
                            st.image(img_path, width=70)
                        else:
                            st.markdown("👷")
                    with c2:
                        st.markdown(f"**{s.name}**")
                        st.caption(f"Food Bank Staff")
                        st.markdown(f"[{s.email}](mailto:{s.email})")


# Functional alias
main_page = show_main_page



