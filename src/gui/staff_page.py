import os
import zipfile
import datetime
import streamlit as st
import pandas as pd
from src.app.admin import AdminUser
from src.app.staff import StaffUser
from src.app.volunteer import VolunteerUser
from src.app.donor import DonorUser
from src.app.client import ClientUser
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
        st.session_state.staff_page = return_page
        if "selected_user_id" in st.session_state:
            del st.session_state.selected_user_id
        st.rerun()


# =========================================================
# Staff Page
# =========================================================

def show_staff_page(manager, user):
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
    st.sidebar.caption("Staff Member")
    st.sidebar.divider()

    if "staff_page" not in st.session_state:
        st.session_state.staff_page = "Profile"

    # Navigation buttons
    if st.sidebar.button("Profile", width="stretch"):
        st.session_state.staff_page = "Profile"

    if st.sidebar.button("Users", width="stretch"):
        st.session_state.staff_page = "Users"

    if st.sidebar.button("Applications", width="stretch"):
        st.session_state.staff_page = "Applications"

    if st.sidebar.button("Donations", width="stretch"):
        st.session_state.staff_page = "Donations"

    if st.sidebar.button("Food Hamper", width="stretch"):
        st.session_state.staff_page = "Food Hamper"

    if st.sidebar.button("Inventory", width="stretch"):
        st.session_state.staff_page = "Inventory"

    if st.sidebar.button("Reports", width="stretch"):
        st.session_state.staff_page = "Reports"

    if st.sidebar.button("System", width="stretch"):
        st.session_state.staff_page = "System"

    st.sidebar.divider()
    if st.sidebar.button("Logout", width="stretch"):
        st.session_state.user = None
        st.session_state.current_page = "main"
        st.rerun()

    page = st.session_state.staff_page

    # =========================================================
    # Staff Profile
    # =========================================================

    if page == "Profile":
        st.title("Staff Profile")

        col_img, col_info = st.columns([1, 3])
        with col_img:
            st.image(user.profile_image, width=150)
        with col_info:
            st.subheader(f"Name: {user.name}")
            st.write(f"**User ID:** {user.id}")
            st.write(f"**Email:** {user.email}")
            st.write(f"**Role:** Staff Member")
            st.write(f"**Profile Image:** `{user.profile_image}`")

        st.divider()
        if st.button("Update Profile"):
            st.session_state.staff_page = "Update Profile"
            st.rerun()

    # =========================================================
    # Update Current Staff Profile
    # =========================================================

    elif page == "Update Profile":
        st.title("Update Profile")
        choice = st.selectbox(
            "Update Term",
            ["Name", "Password", "Email", "Profile Image"]
        )

        if choice == "Name":
            new_name = st.text_input("Please enter your NEW NAME.")
            if st.button("Update"):
                if not manager.valid_name(new_name):
                    st.error("Invalid name.")
                elif new_name == user.name:
                    st.error("The new name is same as the current name.")
                else:
                    manager.update_user(user.id, name=new_name)
                    user.name = new_name
                    st.session_state.staff_page = "Profile Update Success"
                    st.rerun()

        elif choice == "Password":
            current_password = st.text_input(
                "Please enter your CURRENT PASSWORD",
                type="password"
            )
            new_password = st.text_input(
                "Please enter your NEW PASSWORD",
                type="password"
            )
            confirm_password = st.text_input(
                "Please confirm your NEW PASSWORD",
                type="password"
            )

            if st.button("Update"):
                if not verify_password(current_password, user.password):
                    st.error("Wrong password.")
                elif not manager.valid_password(new_password):
                    st.error("Invalid password. Password must be at least 6 characters and include letters and numbers.")
                elif new_password != confirm_password:
                    st.error("The confirmation is not the same as the new password.")
                elif current_password == new_password:
                    st.error("The new password is the same as the current password.")
                else:
                    manager.update_user(user.id, password=new_password)
                    st.session_state.staff_page = "Profile Update Success"
                    st.rerun()

        elif choice == "Email":
            new_email = st.text_input("Please enter your NEW EMAIL.", type="email")
            if st.button("Update"):
                clean_email = new_email.strip()
                if "@" not in clean_email or "." not in clean_email.split("@")[-1]:
                    st.error("Please enter a valid email address.")
                elif clean_email.lower() == user.email.lower():
                    st.error("The new email is the same as the current email.")
                elif manager.find_user_by_email(clean_email) is not None:
                    st.error(f"Email '{clean_email}' is already registered.")
                else:
                    manager.update_user(user.id, email=clean_email)
                    user.email = clean_email
                    st.session_state.staff_page = "Profile Update Success"
                    st.rerun()

        elif choice == "Profile Image":
            st.info("Upload a new image file to update your avatar.")
            uploaded_file = st.file_uploader("Choose an image (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"])
            if uploaded_file is not None:
                if st.button("Update Avatar"):
                    try:
                        assets_dir = os.path.join("assets", "avatars")
                        os.makedirs(assets_dir, exist_ok=True)
                        file_ext = uploaded_file.name.split(".")[-1]
                        save_filename = f"user_{user.id}_{int(datetime.datetime.now().timestamp())}.{file_ext}"
                        save_path = os.path.join(assets_dir, save_filename).replace("\\", "/")

                        with open(save_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())

                        manager.update_user(user.id, profile_image=save_path)
                        user.profile_image = save_path
                        st.session_state.staff_page = "Profile Update Success"
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to save uploaded image: {e}")

        st.divider()
        if st.button("Back to Profile"):
            st.session_state.staff_page = "Profile"
            st.rerun()

    elif page == "Profile Update Success":
        success_page(
            "Profile Updated",
            "Your profile has been updated successfully!",
            "Your account information has been saved.",
            "Profile"
        )

    # =========================================================
    # Users Directory (View Only - No Edit User / Delete User)
    # =========================================================

    elif page == "Users":
        st.title("Users Directory")
        st.caption("Browse registered user accounts across system roles.")

        user_list = st.selectbox(
            "Select User Role Directory",
            ["Staffs", "Volunteers", "Donors", "Clients", "Admins"]
        )

        left, right = st.columns([1, 6])
        with left:
            term = st.selectbox(
                "Search By",
                ["-", "ID", "NAME", "EMAIL"]
            )
        with right:
            if term == "ID":
                search_term = st.number_input("Please enter the user ID.", min_value=1, step=1)
            elif term == "NAME":
                search_term = st.text_input("Please enter the user name.")
            elif term == "EMAIL":
                search_term = st.text_input("Please enter the user email.")
            else:
                search_term = ""

        if user_list == "Admins":
            users = manager.admins
        elif user_list == "Staffs":
            users = manager.staffs
        elif user_list == "Volunteers":
            users = manager.volunteers
        elif user_list == "Donors":
            users = manager.donors
        elif user_list == "Clients":
            users = manager.clients
        else:
            users = []

        table_data = []
        for u in users:
            if term == "-":
                matched = True
            elif term == "ID":
                matched = (u.id == search_term)
            elif term == "NAME":
                matched = (search_term.lower() in u.name.lower())
            elif term == "EMAIL":
                matched = (search_term.lower() in u.email.lower())
            else:
                matched = True

            if matched:
                row = {
                    "ID": u.id,
                    "Name": u.name,
                    "Email": u.email,
                    "Role": type(u).__name__.replace("User", "")
                }
                if user_list == "Clients":
                    row["Address"] = getattr(u, "address", "") or "N/A"
                    allergies = getattr(u, "allergy", [])
                    if isinstance(allergies, list):
                        row["Allergies"] = ", ".join(allergies) if allergies else "None"
                    else:
                        row["Allergies"] = str(allergies) if allergies else "None"

                row["Select"] = False
                table_data.append(row)

        if not table_data:
            st.info(f"No {user_list} found matching search criteria.")
        else:
            user_df = pd.DataFrame(table_data)
            cols = [c for c in user_df.columns if c != "Select"] + ["Select"]
            user_df = user_df[cols]

            col_configs = {
                "ID": st.column_config.NumberColumn("ID", width="small", disabled=True),
                "Name": st.column_config.TextColumn("Name", width="medium", disabled=True),
                "Email": st.column_config.TextColumn("Email", width="medium", disabled=True),
                "Role": st.column_config.TextColumn("Role", width="small", disabled=True),
            }
            if "Address" in user_df.columns:
                col_configs["Address"] = st.column_config.TextColumn("Address", width="medium", disabled=True)
            if "Allergies" in user_df.columns:
                col_configs["Allergies"] = st.column_config.TextColumn("Allergies", width="medium", disabled=True)
            col_configs["Select"] = st.column_config.CheckboxColumn("Select", width="small")

            st.data_editor(
                user_df,
                column_config=col_configs,
                hide_index=True,
                width="stretch",
                key="staff_users_table"
            )

    # =========================================================
    # Applications (Volunteer Applications)
    # =========================================================

    elif page == "Applications":
        st.title("Volunteer Applications")

        all_apps = manager.get_volunteer_applications()

        left, right = st.columns([1, 6])
        with left:
            term = st.selectbox(
                "Search By",
                ["-", "ID", "NAME", "EMAIL", "STATUS"],
                key="app_term"
            )
        with right:
            if term == "ID":
                search_term = st.number_input("Please enter the Application ID.", min_value=1, step=1)
            elif term == "NAME":
                search_term = st.text_input("Please enter Applicant Name.")
            elif term == "EMAIL":
                search_term = st.text_input("Please enter Applicant Email.")
            elif term == "STATUS":
                search_term = st.selectbox("Please choose the status.", ["pending", "approved", "rejected"])
            else:
                search_term = ""

        filtered_apps = []
        for app in all_apps:
            matched = True
            if term == "ID":
                matched = (app.get("id") == search_term)
            elif term == "NAME":
                matched = (str(search_term).lower() in app.get("name", "").lower())
            elif term == "EMAIL":
                matched = (str(search_term).lower() in app.get("email", "").lower())
            elif term == "STATUS":
                matched = (app.get("status", "").lower() == str(search_term).lower())

            if matched:
                filtered_apps.append({
                    "ID": app.get("id"),
                    "Name": app.get("name"),
                    "Email": app.get("email"),
                    "Status": app.get("status", "pending"),
                    "Submitted At": app.get("submitted_at", "N/A"),
                    "Select": False
                })

        if len(filtered_apps) == 0:
            st.info("No applications found.")
        else:
            app_df = pd.DataFrame(filtered_apps)
            edited_apps = st.data_editor(
                app_df,
                column_config={
                    "ID": st.column_config.NumberColumn("ID", width="small", disabled=True),
                    "Name": st.column_config.TextColumn("Name", width="medium", disabled=True),
                    "Email": st.column_config.TextColumn("Email", width="medium", disabled=True),
                    "Status": st.column_config.TextColumn("Status", width="small", disabled=True),
                    "Submitted At": st.column_config.TextColumn("Submitted At", width="medium", disabled=True),
                    "Select": st.column_config.CheckboxColumn("Select", width="small")
                },
                hide_index=True,
                width="stretch",
                key="staff_application_table"
            )

            left_button, right_button = st.columns(2)

            with left_button:
                if st.button("Approve", width="stretch"):
                    selected_apps = edited_apps[edited_apps["Select"] == True]
                    if len(selected_apps) == 0:
                        st.error("Please select an application.")
                    elif len(selected_apps) > 1:
                        st.error("Please select only one application.")
                    else:
                        app_id = int(selected_apps.iloc[0]["ID"])
                        app_status = str(selected_apps.iloc[0]["Status"])
                        if app_status.lower() == "approved":
                            st.warning("This application is already approved.")
                        else:
                            try:
                                volunteer = manager.approve_volunteer_application(app_id)
                                st.success(f"Volunteer application approved! Volunteer '{volunteer.name}' created.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to approve application: {e}")

            with right_button:
                if st.button("Delete", width="stretch"):
                    selected_apps = edited_apps[edited_apps["Select"] == True]
                    if len(selected_apps) == 0:
                        st.error("Please select at least one application.")
                    else:
                        deleted_count = 0
                        for _, row in selected_apps.iterrows():
                            app_id = int(row["ID"])
                            if manager.delete_volunteer_application(app_id):
                                deleted_count += 1
                        st.success(f"Deleted {deleted_count} application(s).")
                        st.rerun()

    # =========================================================
    # Donations
    # =========================================================

    elif page == "Donations":
        st.title("Donations")

        left, right = st.columns([1, 6])
        with left:
            term = st.selectbox(
                "Term",
                ["-", "ID", "DONOR NAME", "STATION", "VOLUNTEER NAME", "STATUS"],
                key="staff_donation_term"
            )
        with right:
            if term == "ID":
                search_term = st.number_input("Please enter the Donation ID.", min_value=1, step=1, key="staff_don_id_search")
            elif term == "DONOR NAME":
                search_term = st.text_input("Please enter Donor Name.", key="staff_don_donor_search")
            elif term == "VOLUNTEER NAME":
                search_term = st.text_input("Please enter Volunteer Name.", key="staff_don_vol_search")
            elif term == "STATION":
                all_stations = manager.get_stations()
                station_filter_opts = ["All"] + [f"ID: {s.get('id')} - {s.get('name')}" for s in all_stations]
                search_term = st.selectbox("Select Station", station_filter_opts, key="staff_don_station_search")
            elif term == "STATUS":
                search_term = st.selectbox("Please choose the status.", ["created", "assigned", "collected", "stocked"], key="staff_don_status_search")
            else:
                search_term = ""

        donation_table = []
        for d in manager.donations:
            status_val = d.status[0] if isinstance(d.status, list) and d.status else (d.status or "created")
            donor_obj = manager.find_donor_by_id(d.donor_id)
            donor_name = donor_obj.name if donor_obj else f"ID: {d.donor_id}"
            vol_obj = manager.find_volunteer_by_id(d.volunteer_id) if d.volunteer_id else None
            vol_name = vol_obj.name if vol_obj else (f"ID: {d.volunteer_id}" if d.volunteer_id else "Unassigned")

            matched = True
            if term == "ID":
                matched = (d.id == search_term)
            elif term == "DONOR NAME":
                matched = (str(search_term).lower() in donor_name.lower())
            elif term == "VOLUNTEER NAME":
                matched = (str(search_term).lower() in vol_name.lower())
            elif term == "STATION":
                if search_term != "All":
                    selected_sid = search_term.split(" - ")[0].replace("ID: ", "").strip()
                    matched = (str(getattr(d, "station", "")) == str(selected_sid))
            elif term == "STATUS":
                matched = (str(status_val).lower() == str(search_term).lower())

            if matched:
                st_val = getattr(d, "station", None)
                if st_val is not None:
                    st_obj = manager.find_station_by_id(st_val)
                    station_display = f"ID: {st_val} - {st_obj['name']}" if st_obj else f"Station ID: {st_val}"
                else:
                    station_display = "Unassigned"

                donation_table.append({
                    "ID": d.id,
                    "Donor": donor_name,
                    "Station": station_display,
                    "Volunteer": vol_name,
                    "Status": status_val,
                    "Items Count": len(getattr(d, "items", [])),
                    "Select": False
                })

        if len(donation_table) == 0:
            st.info("No donations found.")
        else:
            donation_df = pd.DataFrame(donation_table)
            edited_donations = st.data_editor(
                donation_df,
                column_config={
                    "ID": st.column_config.NumberColumn("ID", width="small", disabled=True),
                    "Donor": st.column_config.TextColumn("Donor", width="medium", disabled=True),
                    "Station": st.column_config.TextColumn("Station", width="medium", disabled=True),
                    "Volunteer": st.column_config.TextColumn("Volunteer", width="medium", disabled=True),
                    "Status": st.column_config.TextColumn("Status", width="small", disabled=True),
                    "Items Count": st.column_config.NumberColumn("Items Count", width="small", disabled=True),
                    "Select": st.column_config.CheckboxColumn("Select", width="small")
                },
                hide_index=True,
                width="stretch",
                key="staff_donation_table"
            )

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Donation Detail", width="stretch"):
                    selected_rows = edited_donations[edited_donations["Select"] == True]
                    if len(selected_rows) == 0:
                        st.error("Please select a donation.")
                    elif len(selected_rows) > 1:
                        st.error("Please select only one donation.")
                    else:
                        st.session_state.selected_donation_id = int(selected_rows.iloc[0]["ID"])
                        st.session_state.staff_page = "Donation Detail"
                        st.rerun()

            with col2:
                if st.button("Delete Donation", width="stretch"):
                    selected_rows = edited_donations[edited_donations["Select"] == True]
                    if len(selected_rows) == 0:
                        st.error("Please select a donation.")
                    elif len(selected_rows) > 1:
                        st.error("Please select only one donation.")
                    else:
                        don_id = int(selected_rows.iloc[0]["ID"])
                        try:
                            manager.delete_donation(don_id)
                            st.success(f"Donation #{don_id} deleted successfully.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Cannot delete donation #{don_id}: {e}")

        st.divider()
        col_create, col_export = st.columns(2)
        with col_create:
            if st.button("Create Donation", width="stretch"):
                st.session_state.staff_page = "Create Donation"
                st.rerun()
        with col_export:
            if st.button("Export Donations Report", width="stretch"):
                try:
                    filepath = manager.export_donations_csv()
                    st.success(f"Donations report exported to '{filepath}'.")
                    with open(filepath, "rb") as f:
                        st.download_button(
                            label="Download Donations CSV",
                            data=f.read(),
                            file_name=os.path.basename(filepath),
                            mime="text/csv",
                            width="stretch"
                        )
                except Exception as e:
                    st.error(f"Failed to export donations: {e}")

    # =========================================================
    # Create Donation
    # =========================================================

    elif page == "Create Donation":
        st.title("Create Donation")

        donors = manager.donors
        if not donors:
            st.warning("No donors found in the system. Please register a donor first.")
        else:
            donor_options = {f"ID: {d.id} - {d.name}": d.id for d in donors}
            selected_donor_label = st.selectbox("Select Donor", list(donor_options.keys()))
            donor_id = donor_options[selected_donor_label]

            stations = manager.get_stations()
            station_options = {"Unassigned": None}
            for s in stations:
                station_options[f"ID: {s.get('id')} - {s.get('name')}"] = s.get("id")
            selected_station_label = st.selectbox("Select Station to Dropoff & Pickup", list(station_options.keys()))
            selected_station_id = station_options[selected_station_label]

            description = st.text_area("Description")

            st.subheader("Donation Items")
            available_items = [item.name for item in manager.get_inventory_items()]
            chosen_items = st.multiselect("Select Items to Donate", available_items)

            items_list = []
            if chosen_items:
                for it_name in chosen_items:
                    qty = st.number_input(f"Quantity for {it_name}", min_value=1.0, step=1.0, value=1.0, key=f"staff_don_item_{it_name}")
                    items_list.append({"name": it_name, "quantity": qty})

            vol_options = {"Unassigned": None}
            for v in manager.volunteers:
                vol_options[f"ID: {v.id} - {v.name}"] = v.id
            selected_vol_label = st.selectbox("Assign Volunteer (Optional)", list(vol_options.keys()))
            volunteer_id = vol_options[selected_vol_label]

            left_btn, right_btn = st.columns(2)
            with left_btn:
                if st.button("Submit Donation", width="stretch"):
                    if not items_list:
                        st.error("Please select at least one item to donate.")
                    else:
                        try:
                            don = manager.add_donation(
                                donor_id,
                                description=description.strip(),
                                items=items_list,
                                station=selected_station_id
                            )
                            if volunteer_id is not None:
                                manager.update_donation(don.id, volunteer_id=volunteer_id, status="assigned")
                            st.session_state.staff_page = "Donation Success"
                            st.session_state.donation_success_msg = f"Donation #{don.id} has been created successfully."
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to create donation: {e}")

            with right_btn:
                if st.button("Cancel", width="stretch"):
                    st.session_state.staff_page = "Donations"
                    st.rerun()

    elif page == "Donation Success":
        success_page(
            "Donation Saved",
            "The donation record has been processed successfully!",
            st.session_state.get("donation_success_msg", "Donation updated."),
            "Donations"
        )

    # =========================================================
    # Donation Detail (With Confirmation of Collected & Stock)
    # =========================================================

    elif page == "Donation Detail":
        st.title("Donation Detail")

        if "selected_donation_id" not in st.session_state:
            st.error("No donation selected.")
            if st.button("Back to Donations"):
                st.session_state.staff_page = "Donations"
                st.rerun()
        else:
            donation_id = st.session_state.selected_donation_id
            target_donation = manager.find_donation_by_id(donation_id)
            if target_donation is None:
                st.error("Donation not found.")
                if st.button("Back to Donations"):
                    del st.session_state.selected_donation_id
                    st.session_state.staff_page = "Donations"
                    st.rerun()
            else:
                curr_status = target_donation.status[0] if isinstance(target_donation.status, list) and target_donation.status else (target_donation.status or "created")
                donor_obj = manager.find_donor_by_id(target_donation.donor_id)
                donor_name = donor_obj.name if donor_obj else f"ID: {target_donation.donor_id}"
                donor_email = getattr(donor_obj, "email", "N/A") if donor_obj else "N/A"

                vol_obj = manager.find_volunteer_by_id(target_donation.volunteer_id) if target_donation.volunteer_id else None
                vol_name = vol_obj.name if vol_obj else (f"ID: {target_donation.volunteer_id}" if target_donation.volunteer_id else "Unassigned")
                vol_email = getattr(vol_obj, "email", "N/A") if vol_obj else "N/A"

                st_val = getattr(target_donation, "station", None)
                if st_val is not None:
                    st_obj = manager.find_station_by_id(st_val)
                    station_display = f"ID: {st_val} - {st_obj['name']} ({st_obj.get('address', '')})" if st_obj else f"Station ID: {st_val}"
                else:
                    station_display = "Unassigned"

                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("Donation ID", f"#{target_donation.id}")
                with c2:
                    st.metric("Current Status", str(curr_status).upper())
                with c3:
                    st.metric("Items Total", f"{len(target_donation.items)} type(s)")

                st.divider()

                col_left, col_right = st.columns(2)
                with col_left:
                    st.subheader("Donor & Station Info")
                    st.write(f"**Donor:** {donor_name} (Email: {donor_email})")
                    st.write(f"**Dropoff / Pickup Station:** {station_display}")
                    st.write(f"**Description / Notes:** {target_donation.description or 'None'}")

                with col_right:
                    st.subheader("Assignment & Tracking")
                    st.write(f"**Assigned Volunteer:** {vol_name} (Email: {vol_email})")
                    last_updated = target_donation.status_history[-1]["timestamp"] if getattr(target_donation, "status_history", None) else "N/A"
                    st.write(f"**Last Status Updated:** {last_updated}")
                    if getattr(target_donation, "flagged_issue", None):
                        st.warning(f"Flagged Issue: {target_donation.flagged_issue.get('issue')}")

                st.subheader("Donated Items Breakdown")
                if not target_donation.items:
                    st.info("No items recorded in this donation.")
                else:
                    items_rows = []
                    for it in target_donation.items:
                        if isinstance(it, dict):
                            items_rows.append({"Item Name": it.get("name"), "Quantity": it.get("quantity")})
                        else:
                            items_rows.append({"Item Name": getattr(it, "name", str(it)), "Quantity": getattr(it, "quantity", 1)})
                    st.dataframe(pd.DataFrame(items_rows), width="stretch", hide_index=True)

                if getattr(target_donation, "status_history", None):
                    st.subheader("Status Timeline History")
                    history_rows = [{"Status": h.get("status"), "Timestamp": h.get("timestamp")} for h in target_donation.status_history]
                    st.dataframe(pd.DataFrame(history_rows), width="stretch", hide_index=True)

                st.divider()

                # Staff Collection & Stocking Operations (Staff can confirm collected & stock into inventory)
                if curr_status.lower() in ("created", "assigned"):
                    st.subheader("Staff Operations")
                    st.info("Confirm reception of this donation once received at the station or food bank.")
                    col_d1, col_d2 = st.columns(2)
                    with col_d1:
                        if st.button("Mark as Collected", width="stretch"):
                            try:
                                manager.collect_donation(target_donation.id, target_donation.volunteer_id)
                                st.success(f"Donation #{target_donation.id} has been marked as collected!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Cannot mark donation as collected: {e}")
                    with col_d2:
                        if st.button("Collect & Stock into Inventory", width="stretch"):
                            try:
                                manager.collect_donation(target_donation.id, target_donation.volunteer_id)
                                manager.stock_donation(target_donation.id)
                                st.success(f"Donation #{target_donation.id} collected and items added to inventory!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Cannot collect and stock donation: {e}")

                elif curr_status.lower() == "collected":
                    st.subheader("Staff Operations")
                    st.info("Donation is collected. You can transfer donated items into inventory.")
                    if st.button("Stock Items into Inventory Now", width="stretch"):
                        try:
                            manager.stock_donation(target_donation.id)
                            st.success(f"Donation #{target_donation.id} items transferred to inventory!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Cannot stock donation: {e}")

                elif curr_status.lower() == "stocked":
                    st.success("This donation has been received and stocked into inventory.")

                st.write("")
                btn_edit, btn_back = st.columns(2)
                with btn_edit:
                    if st.button("Edit Donation", width="stretch"):
                        st.session_state.staff_page = "Edit Donation"
                        st.rerun()
                with btn_back:
                    if st.button("Back to Donations", width="stretch"):
                        del st.session_state.selected_donation_id
                        st.session_state.staff_page = "Donations"
                        st.rerun()

    # =========================================================
    # Edit / Reassign Donation
    # =========================================================

    elif page == "Edit Donation":
        st.title("Edit / Reassign Donation")

        if "selected_donation_id" not in st.session_state:
            st.error("No donation selected.")
            if st.button("Back to Donations"):
                st.session_state.staff_page = "Donations"
                st.rerun()
        else:
            donation_id = st.session_state.selected_donation_id
            target_donation = manager.find_donation_by_id(donation_id)
            if target_donation is None:
                st.error("Donation not found.")
                if st.button("Back to Donations"):
                    st.session_state.staff_page = "Donations"
                    del st.session_state.selected_donation_id
                    st.rerun()
            else:
                curr_status = target_donation.status[0] if isinstance(target_donation.status, list) and target_donation.status else (target_donation.status or "created")
                st.subheader(f"Editing Donation #{target_donation.id}")

                # Donor selector
                donor_options = {f"ID: {d.id} - {d.name}": d.id for d in manager.donors}
                curr_donor_label = None
                for lbl, did in donor_options.items():
                    if did == target_donation.donor_id:
                        curr_donor_label = lbl
                        break
                selected_donor_label = st.selectbox(
                    "Donor",
                    list(donor_options.keys()),
                    index=list(donor_options.keys()).index(curr_donor_label) if curr_donor_label in donor_options else 0
                )
                new_donor_id = donor_options[selected_donor_label]

                # Station / Collection Center selector
                stations = manager.get_stations()
                station_options = {"Unassigned": None}
                for s in stations:
                    station_options[f"ID: {s.get('id')} - {s.get('name')}"] = s.get("id")
                curr_station_id = getattr(target_donation, "station", None)
                curr_station_label = "Unassigned"
                for lbl, sid in station_options.items():
                    if sid == curr_station_id:
                        curr_station_label = lbl
                        break
                selected_st_label = st.selectbox(
                    "Station / Collection Center (Pickup Location)",
                    list(station_options.keys()),
                    index=list(station_options.keys()).index(curr_station_label)
                )
                new_station_id = station_options[selected_st_label]

                # Status selector
                status_choices = ["created", "assigned", "collected", "stocked"]
                new_status = st.selectbox(
                    "Status",
                    status_choices,
                    index=status_choices.index(curr_status) if curr_status in status_choices else 0
                )

                # Reassign Volunteer
                volunteer_options = {"Unassigned": None}
                for v in manager.volunteers:
                    volunteer_options[f"ID: {v.id} - {v.name}"] = v.id
                curr_vol_label = "Unassigned"
                for lbl, vid in volunteer_options.items():
                    if vid == target_donation.volunteer_id:
                        curr_vol_label = lbl
                        break
                selected_vol_label = st.selectbox(
                    "Assigned Volunteer (Reassign / Delegate)",
                    list(volunteer_options.keys()),
                    index=list(volunteer_options.keys()).index(curr_vol_label)
                )
                new_volunteer_id = volunteer_options[selected_vol_label]

                # Description
                new_description = st.text_area("Description", value=target_donation.description or "")

                # Items Modification (Allowed only when status is 'created')
                new_items_list = target_donation.items
                if curr_status.lower() == "created":
                    st.subheader("Modify Donation Items (Created Status Only)")
                    available_items = [item.name for item in manager.get_inventory_items()]
                    existing_item_names = [it.get("name") for it in target_donation.items if isinstance(it, dict) and it.get("name")]
                    for en in existing_item_names:
                        if en not in available_items:
                            available_items.append(en)

                    selected_edit_items = st.multiselect("Donated Items", available_items, default=existing_item_names)
                    new_items_list = []
                    for it_name in selected_edit_items:
                        prev_qty = 1.0
                        for it in target_donation.items:
                            if isinstance(it, dict) and it.get("name") == it_name:
                                prev_qty = float(it.get("quantity", 1.0))
                                break
                        qty = st.number_input(f"Quantity for {it_name}", min_value=1.0, step=1.0, value=prev_qty, key=f"staff_edit_don_item_{it_name}")
                        new_items_list.append({"name": it_name, "quantity": qty})
                else:
                    st.info(f"Items cannot be modified because this donation has already reached '{curr_status}' status.")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Save Changes", width="stretch"):
                        try:
                            manager.update_donation(
                                target_donation.id,
                                donor_id=new_donor_id,
                                volunteer_id=new_volunteer_id,
                                station=new_station_id,
                                description=new_description.strip(),
                                status=new_status,
                                items=new_items_list
                            )
                            if curr_status.lower() != new_status.lower():
                                if new_status.lower() == "collected":
                                    manager.collect_donation(target_donation.id, new_volunteer_id)
                                elif new_status.lower() == "stocked":
                                    if curr_status.lower() in ("created", "assigned"):
                                        manager.collect_donation(target_donation.id, new_volunteer_id)
                                    manager.stock_donation(target_donation.id)

                            st.session_state.staff_page = "Donation Success"
                            st.session_state.donation_success_msg = f"Donation #{target_donation.id} details and assignment have been updated."
                            del st.session_state.selected_donation_id
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to update donation: {e}")

                with col2:
                    if st.button("Cancel", width="stretch"):
                        del st.session_state.selected_donation_id
                        st.session_state.staff_page = "Donations"
                        st.rerun()

    # =========================================================
    # Food Hamper
    # =========================================================

    elif page == "Food Hamper":
        st.title("Food Hampers")

        left, right = st.columns([1, 6])
        with left:
            term = st.selectbox(
                "Term",
                ["-", "ID", "CLIENT NAME", "VOLUNTEER NAME", "STATUS"],
                key="staff_hamper_term"
            )
        with right:
            if term == "ID":
                search_term = st.number_input("Please enter the Hamper ID.", min_value=1, step=1, key="staff_hamper_id_search")
            elif term == "CLIENT NAME":
                search_term = st.text_input("Please enter Client Name.", key="staff_hamper_client_search")
            elif term == "VOLUNTEER NAME":
                search_term = st.text_input("Please enter Volunteer Name.", key="staff_hamper_vol_search")
            elif term == "STATUS":
                search_term = st.selectbox("Please choose the status.", ["created", "assigned", "packed", "delivered"], key="staff_hamper_status_search")
            else:
                search_term = ""

        hamper_table = []
        for h in manager.food_hampers:
            status_val = h.status[0] if isinstance(h.status, list) and h.status else (h.status or "created")
            client_obj = manager.find_client_by_id(h.client_id) if h.client_id else None
            client_name = client_obj.name if client_obj else (f"ID: {h.client_id}" if h.client_id else "Unassigned")
            vol_obj = manager.find_volunteer_by_id(h.volunteer_id) if h.volunteer_id else None
            vol_name = vol_obj.name if vol_obj else (f"ID: {h.volunteer_id}" if h.volunteer_id else "Unassigned")

            matched = True
            if term == "ID":
                matched = (h.id == search_term)
            elif term == "CLIENT NAME":
                matched = (str(search_term).lower() in client_name.lower())
            elif term == "VOLUNTEER NAME":
                matched = (str(search_term).lower() in vol_name.lower())
            elif term == "STATUS":
                matched = (str(status_val).lower() == str(search_term).lower())

            if matched:
                hamper_table.append({
                    "ID": h.id,
                    "Client": client_name,
                    "Volunteer": vol_name,
                    "Status": status_val,
                    "Items Count": len(getattr(h, "items", [])),
                    "Select": False
                })

        if len(hamper_table) == 0:
            st.info("No food hampers found.")
        else:
            hamper_df = pd.DataFrame(hamper_table)
            edited_hampers = st.data_editor(
                hamper_df,
                column_config={
                    "ID": st.column_config.NumberColumn("ID", width="small", disabled=True),
                    "Client": st.column_config.TextColumn("Client", width="medium", disabled=True),
                    "Volunteer": st.column_config.TextColumn("Volunteer", width="medium", disabled=True),
                    "Status": st.column_config.TextColumn("Status", width="small", disabled=True),
                    "Items Count": st.column_config.NumberColumn("Items Count", width="small", disabled=True),
                    "Select": st.column_config.CheckboxColumn("Select", width="small")
                },
                hide_index=True,
                width="stretch",
                key="staff_hamper_table"
            )

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Food Hamper Detail", width="stretch"):
                    selected_rows = edited_hampers[edited_hampers["Select"] == True]
                    if len(selected_rows) == 0:
                        st.error("Please select a food hamper.")
                    elif len(selected_rows) > 1:
                        st.error("Please select only one food hamper.")
                    else:
                        st.session_state.selected_hamper_id = int(selected_rows.iloc[0]["ID"])
                        st.session_state.staff_page = "Food Hamper Detail"
                        st.rerun()

            with col2:
                if st.button("Delete Food Hamper", width="stretch"):
                    selected_rows = edited_hampers[edited_hampers["Select"] == True]
                    if len(selected_rows) == 0:
                        st.error("Please select a food hamper.")
                    elif len(selected_rows) > 1:
                        st.error("Please select only one food hamper.")
                    else:
                        h_id = int(selected_rows.iloc[0]["ID"])
                        try:
                            manager.delete_food_hamper(h_id)
                            st.success(f"Food hamper #{h_id} deleted successfully.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Cannot delete food hamper #{h_id}: {e}")

        st.divider()
        col_create, col_export = st.columns(2)
        with col_create:
            if st.button("Create Food Hamper", width="stretch"):
                st.session_state.staff_page = "Create Food Hamper"
                st.rerun()
        with col_export:
            if st.button("Export Food Hampers Report", width="stretch"):
                try:
                    filepath = manager.export_hampers_csv()
                    st.success(f"Food hampers report exported to '{filepath}'.")
                    with open(filepath, "rb") as f:
                        st.download_button(
                            label="Download Food Hampers CSV",
                            data=f.read(),
                            file_name=os.path.basename(filepath),
                            mime="text/csv",
                            width="stretch"
                        )
                except Exception as e:
                    st.error(f"Failed to export food hampers report: {e}")

    # =========================================================
    # Create Food Hamper
    # =========================================================

    elif page == "Create Food Hamper":
        st.title("Create Food Hamper")

        client_options = {"Unassigned": None}
        for c in manager.clients:
            client_options[f"ID: {c.id} - {c.name}"] = c.id
        selected_client_label = st.selectbox("Select Target Client", list(client_options.keys()))
        client_id = client_options[selected_client_label]

        # Display Selected Client Information & Allergies
        if client_id is not None:
            chosen_client = manager.find_client_by_id(client_id)
            if chosen_client:
                st.markdown("---")
                st.subheader(f"Recipient Profile: {chosen_client.name}")

                client_allergies = getattr(chosen_client, "allergy", [])
                if isinstance(client_allergies, list) and client_allergies:
                    allergy_str = ", ".join([str(a) for a in client_allergies])
                    st.error(f"⚠️ **ALLERGY ALERT:** {allergy_str} (Please ensure NO matching allergen items are packed!)")
                elif isinstance(client_allergies, str) and client_allergies.strip():
                    st.error(f"⚠️ **ALLERGY ALERT:** {client_allergies.strip()} (Please ensure NO matching allergen items are packed!)")
                else:
                    st.success("✅ **Allergy Status:** No known allergies recorded for this client.")

                c_info1, c_info2 = st.columns(2)
                with c_info1:
                    st.write(f"**Delivery Address:** {getattr(chosen_client, 'address', '') or 'N/A'}")
                    st.write(f"**Email:** {getattr(chosen_client, 'email', '') or 'N/A'}")
                with c_info2:
                    st.write(f"**Description / Background:** {getattr(chosen_client, 'description', '') or 'N/A'}")
                    past_received = len(getattr(chosen_client, 'receive', []))
                    st.write(f"**Total Hampers Received:** {past_received}")
                st.markdown("---")

        volunteer_options = {"Unassigned": None}
        for v in manager.volunteers:
            volunteer_options[f"ID: {v.id} - {v.name}"] = v.id
        selected_vol_label = st.selectbox("Assign Volunteer to Deliver", list(volunteer_options.keys()))
        volunteer_id = volunteer_options[selected_vol_label]

        description = st.text_area("Description / Hamper Notes")

        st.subheader("Hamper Items from Inventory")
        inv_items = manager.get_inventory_items()
        inv_item_names = [it.name for it in inv_items]
        selected_hamper_items = st.multiselect("Select Items to Pack", inv_item_names)

        items_list = []
        if selected_hamper_items:
            for it_name in selected_hamper_items:
                inv_obj = manager.inventory.find_item_by_name(it_name)
                current_stock = inv_obj.quantity if inv_obj else 0
                qty = st.number_input(
                    f"Quantity for {it_name} (In stock: {current_stock} {getattr(inv_obj, 'unit', '')})",
                    min_value=1.0,
                    step=1.0,
                    value=1.0,
                    key=f"staff_hamper_item_{it_name}"
                )
                items_list.append({"name": it_name, "quantity": qty})

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Submit Hamper", width="stretch"):
                if not items_list:
                    st.error("Please select at least one item to pack in the food hamper.")
                else:
                    try:
                        hamper = manager.add_food_hamper(
                            client_id=client_id,
                            description=description.strip(),
                            items=items_list,
                            volunteer_id=volunteer_id
                        )
                        st.session_state.staff_page = "Hamper Success"
                        st.session_state.hamper_success_msg = f"Food Hamper #{hamper.id} created successfully."
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to create food hamper: {e}")

        with col2:
            if st.button("Cancel", width="stretch"):
                st.session_state.staff_page = "Food Hamper"
                st.rerun()

    elif page == "Hamper Success":
        success_page(
            "Food Hamper Saved",
            "The food hamper record has been processed successfully!",
            st.session_state.get("hamper_success_msg", "Hamper updated."),
            "Food Hamper"
        )

    # =========================================================
    # Food Hamper Detail (No Force Operations)
    # =========================================================

    elif page == "Food Hamper Detail":
        st.title("Food Hamper Detail")

        if "selected_hamper_id" not in st.session_state:
            st.error("No food hamper selected.")
            if st.button("Back to Food Hampers"):
                st.session_state.staff_page = "Food Hamper"
                st.rerun()
        else:
            hamper_id = st.session_state.selected_hamper_id
            target_hamper = manager.find_food_hamper_by_id(hamper_id)
            if target_hamper is None:
                st.error("Food hamper not found.")
                if st.button("Back to Food Hampers"):
                    del st.session_state.selected_hamper_id
                    st.session_state.staff_page = "Food Hamper"
                    st.rerun()
            else:
                curr_status = target_hamper.status[0] if isinstance(target_hamper.status, list) and target_hamper.status else (target_hamper.status or "created")
                client_obj = manager.find_client_by_id(target_hamper.client_id) if target_hamper.client_id else None
                client_name = client_obj.name if client_obj else (f"ID: {target_hamper.client_id}" if target_hamper.client_id else "Unassigned")
                client_email = getattr(client_obj, "email", "N/A") if client_obj else "N/A"
                client_address = getattr(client_obj, "address", "N/A") if client_obj else "N/A"

                vol_obj = manager.find_volunteer_by_id(target_hamper.volunteer_id) if target_hamper.volunteer_id else None
                vol_name = vol_obj.name if vol_obj else (f"ID: {target_hamper.volunteer_id}" if target_hamper.volunteer_id else "Unassigned")
                vol_email = getattr(vol_obj, "email", "N/A") if vol_obj else "N/A"

                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("Hamper ID", f"#{target_hamper.id}")
                with c2:
                    st.metric("Delivery Status", str(curr_status).upper())
                with c3:
                    st.metric("Items Pack Count", f"{len(target_hamper.items)} type(s)")

                st.divider()

                col_left, col_right = st.columns(2)
                with col_left:
                    st.subheader("Recipient Information")
                    st.write(f"**Client:** {client_name} (Email: {client_email})")
                    st.write(f"**Delivery Address:** {client_address}")
                    st.write(f"**Hamper Notes:** {target_hamper.description or 'None'}")

                    if client_obj:
                        client_allergies = getattr(client_obj, "allergy", [])
                        if isinstance(client_allergies, list) and client_allergies:
                            allergy_str = ", ".join([str(a) for a in client_allergies])
                            st.error(f"⚠️ **ALLERGY ALERT:** {allergy_str}")
                        elif isinstance(client_allergies, str) and client_allergies.strip():
                            st.error(f"⚠️ **ALLERGY ALERT:** {client_allergies.strip()}")

                with col_right:
                    st.subheader("Volunteer & Tracking")
                    st.write(f"**Assigned Volunteer:** {vol_name} (Email: {vol_email})")
                    last_updated = target_hamper.status_history[-1]["timestamp"] if getattr(target_hamper, "status_history", None) else "N/A"
                    st.write(f"**Last Status Updated:** {last_updated}")
                    if getattr(target_hamper, "flagged_issue", None):
                        st.warning(f"Flagged Issue: {target_hamper.flagged_issue.get('issue')}")

                st.subheader("Packed Food Items Breakdown")
                if not target_hamper.items:
                    st.info("No items packed in this hamper.")
                else:
                    items_rows = []
                    for it in target_hamper.items:
                        if isinstance(it, dict):
                            items_rows.append({"Item Name": it.get("name"), "Quantity": it.get("quantity")})
                        else:
                            items_rows.append({"Item Name": getattr(it, "name", str(it)), "Quantity": getattr(it, "quantity", 1)})
                    st.dataframe(pd.DataFrame(items_rows), width="stretch", hide_index=True)

                if getattr(target_hamper, "status_history", None):
                    st.subheader("Status Timeline History")
                    history_rows = [{"Status": h.get("status"), "Timestamp": h.get("timestamp")} for h in target_hamper.status_history]
                    st.dataframe(pd.DataFrame(history_rows), width="stretch", hide_index=True)

                st.divider()
                btn_edit, btn_back = st.columns(2)
                with btn_edit:
                    if st.button("Edit Food Hamper", width="stretch"):
                        st.session_state.staff_page = "Edit Food Hamper"
                        st.rerun()
                with btn_back:
                    if st.button("Back to Food Hampers", width="stretch"):
                        del st.session_state.selected_hamper_id
                        st.session_state.staff_page = "Food Hamper"
                        st.rerun()

    # =========================================================
    # Edit / Reassign Food Hamper
    # =========================================================

    elif page == "Edit Food Hamper":
        st.title("Edit / Reassign Food Hamper")

        if "selected_hamper_id" not in st.session_state:
            st.error("No food hamper selected.")
            if st.button("Back to Food Hampers"):
                st.session_state.staff_page = "Food Hamper"
                st.rerun()
        else:
            hamper_id = st.session_state.selected_hamper_id
            target_hamper = manager.find_food_hamper_by_id(hamper_id)
            if target_hamper is None:
                st.error("Food hamper not found.")
                if st.button("Back to Food Hampers"):
                    del st.session_state.selected_hamper_id
                    st.session_state.staff_page = "Food Hamper"
                    st.rerun()
            else:
                curr_status = target_hamper.status[0] if isinstance(target_hamper.status, list) and target_hamper.status else (target_hamper.status or "created")
                st.subheader(f"Editing Food Hamper #{target_hamper.id}")

                client_options = {"Unassigned": None}
                for c in manager.clients:
                    client_options[f"ID: {c.id} - {c.name}"] = c.id
                curr_client_label = "Unassigned"
                for lbl, cid in client_options.items():
                    if cid == target_hamper.client_id:
                        curr_client_label = lbl
                        break
                selected_client_label = st.selectbox(
                    "Target Client",
                    list(client_options.keys()),
                    index=list(client_options.keys()).index(curr_client_label)
                )
                new_client_id = client_options[selected_client_label]

                volunteer_options = {"Unassigned": None}
                for v in manager.volunteers:
                    volunteer_options[f"ID: {v.id} - {v.name}"] = v.id
                curr_vol_label = "Unassigned"
                for lbl, vid in volunteer_options.items():
                    if vid == target_hamper.volunteer_id:
                        curr_vol_label = lbl
                        break
                selected_vol_label = st.selectbox(
                    "Assigned Volunteer (Reassign / Delegate)",
                    list(volunteer_options.keys()),
                    index=list(volunteer_options.keys()).index(curr_vol_label)
                )
                new_volunteer_id = volunteer_options[selected_vol_label]

                new_description = st.text_area("Description", value=target_hamper.description or "")

                # Items Modification (Allowed only when status is 'created')
                new_hamper_items_list = target_hamper.items
                if curr_status.lower() == "created":
                    st.subheader("Modify Hamper Items (Created Status Only)")
                    inv_items = manager.get_inventory_items()
                    inv_names = [it.name for it in inv_items]
                    existing_hamper_item_names = [it.get("name") for it in target_hamper.items if isinstance(it, dict) and it.get("name")]
                    for en in existing_hamper_item_names:
                        if en not in inv_names:
                            inv_names.append(en)

                    selected_edit_hamper_items = st.multiselect("Hamper Items", inv_names, default=existing_hamper_item_names)
                    new_hamper_items_list = []
                    for it_name in selected_edit_hamper_items:
                        inv_obj = manager.inventory.find_item_by_name(it_name)
                        current_stock = inv_obj.quantity if inv_obj else 0
                        prev_qty = 1.0
                        for it in target_hamper.items:
                            if isinstance(it, dict) and it.get("name") == it_name:
                                prev_qty = float(it.get("quantity", 1.0))
                                break
                        qty = st.number_input(
                            f"Quantity for {it_name} (In stock: {current_stock} {getattr(inv_obj, 'unit', '')})",
                            min_value=1.0,
                            step=1.0,
                            value=prev_qty,
                            key=f"staff_edit_hamper_item_{it_name}"
                        )
                        new_hamper_items_list.append({"name": it_name, "quantity": qty})
                else:
                    st.info(f"Items cannot be modified because this hamper has already reached '{curr_status}' status.")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Save Changes", width="stretch"):
                        try:
                            manager.update_food_hamper(
                                target_hamper.id,
                                client_id=new_client_id,
                                volunteer_id=new_volunteer_id,
                                description=new_description.strip(),
                                items=new_hamper_items_list
                            )
                            st.session_state.staff_page = "Hamper Success"
                            st.session_state.hamper_success_msg = f"Food Hamper #{target_hamper.id} details and assignment updated."
                            del st.session_state.selected_hamper_id
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to update food hamper: {e}")

                with col2:
                    if st.button("Cancel", width="stretch"):
                        del st.session_state.selected_hamper_id
                        st.session_state.staff_page = "Food Hamper"
                        st.rerun()

    # =========================================================
    # Reports
    # =========================================================

    elif page == "Reports":
        st.title("System Reports & Data Export")
        st.info("Export master CSV activity reports for audit, record-keeping, and statistics.")

        report_type = st.selectbox(
            "Select Report Type",
            [
                "All Reports (ZIP / Batch Export)",
                "Inventory Report",
                "Stock Transactions History",
                "Food Hampers Distribution Report",
                "Donations Report",
                "Volunteers Performance Report"
            ]
        )

        st.write("")
        if st.button("Generate & Export Report", width="stretch"):
            try:
                if report_type == "All Reports (ZIP / Batch Export)":
                    results = manager.export_all_reports()
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    zip_path = os.path.join("reports", f"foodshare_all_reports_{timestamp}.zip")
                    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                        for rep_name, fp in results.items():
                            if fp and os.path.exists(fp):
                                zipf.write(fp, arcname=os.path.basename(fp))
                    st.success(f"All 5 master reports exported and packaged into '{zip_path}'.")
                    with open(zip_path, "rb") as zf:
                        st.download_button(
                            label="Download All Reports (ZIP Archive)",
                            data=zf.read(),
                            file_name=os.path.basename(zip_path),
                            mime="application/zip",
                            width="stretch"
                        )
                else:
                    if report_type == "Inventory Report":
                        filepath = manager.export_inventory_csv()
                    elif report_type == "Stock Transactions History":
                        filepath = manager.export_transactions_csv()
                    elif report_type == "Food Hampers Distribution Report":
                        filepath = manager.export_hampers_csv()
                    elif report_type == "Donations Report":
                        filepath = manager.export_donations_csv()
                    elif report_type == "Volunteers Performance Report":
                        filepath = manager.export_volunteers_csv()
                    else:
                        filepath = manager.export_inventory_csv()

                    if filepath and os.path.exists(filepath):
                        st.success(f"Report successfully generated at '{filepath}'.")
                        with open(filepath, "rb") as f:
                            st.download_button(
                                label=f"Download {os.path.basename(filepath)}",
                                data=f.read(),
                                file_name=os.path.basename(filepath),
                                mime="text/csv",
                                width="stretch"
                            )
            except Exception as e:
                st.error(f"Failed to generate report: {e}")

    # =========================================================
    # Food Inventory Management
    # =========================================================

    elif page == "Inventory":
        st.title("Food Inventory Management")

        left, right = st.columns([1, 6])
        with left:
            term = st.selectbox(
                "Term",
                ["-", "ID", "NAME", "CATEGORY", "STOCK STATUS"],
                key="staff_inventory_term"
            )
        with right:
            if term == "ID":
                search_term = st.number_input("Please enter the Item ID.", min_value=1, step=1, key="staff_inv_id_search")
            elif term == "NAME":
                search_term = st.text_input("Please enter the Item Name.", key="staff_inv_name_search")
            elif term == "CATEGORY":
                search_term = st.text_input("Please enter the Category.", key="staff_inv_cat_search")
            elif term == "STOCK STATUS":
                search_term = st.selectbox("Please choose stock status.", ["In Stock", "Low Stock", "Out of Stock"], key="staff_inv_status_search")
            else:
                search_term = ""

        all_items = manager.get_inventory_items()

        inv_data = []
        for item in all_items:
            stock_status = "In Stock"
            if item.quantity <= 0:
                stock_status = "Out of Stock"
            elif item.quantity <= item.min_quantity:
                stock_status = "Low Stock"

            matched = True
            if term == "ID":
                matched = (item.id == search_term)
            elif term == "NAME":
                matched = (search_term.lower() in item.name.lower())
            elif term == "CATEGORY":
                matched = (search_term.lower() in item.category.lower())
            elif term == "STOCK STATUS":
                matched = (stock_status == search_term)

            if matched:
                inv_data.append({
                    "ID": item.id,
                    "Name": item.name,
                    "Category": item.category,
                    "Quantity": float(item.quantity),
                    "Unit": item.unit,
                    "Min Qty": float(item.min_quantity),
                    "Status": stock_status,
                    "Select": False
                })

        if not inv_data:
            st.info("No inventory items found.")
        else:
            inv_df = pd.DataFrame(inv_data)
            edited_inv = st.data_editor(
                inv_df,
                column_config={
                    "ID": st.column_config.NumberColumn("ID", width="small", disabled=True),
                    "Name": st.column_config.TextColumn("Name", width="medium", disabled=True),
                    "Category": st.column_config.TextColumn("Category", width="small", disabled=True),
                    "Quantity": st.column_config.NumberColumn("Quantity", width="small", disabled=True),
                    "Unit": st.column_config.TextColumn("Unit", width="small", disabled=True),
                    "Min Qty": st.column_config.NumberColumn("Min Qty", width="small", disabled=True),
                    "Status": st.column_config.TextColumn("Status", width="small", disabled=True),
                    "Select": st.column_config.CheckboxColumn("Select", width="small")
                },
                hide_index=True,
                width="stretch",
                key="staff_inventory_table"
            )

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Adjust Stock (Add / Deduct)", width="stretch"):
                    selected_rows = edited_inv[edited_inv["Select"] == True]
                    if len(selected_rows) == 0:
                        st.error("Please select an item to adjust.")
                    elif len(selected_rows) > 1:
                        st.error("Please select only one item.")
                    else:
                        st.session_state.selected_item_id = int(selected_rows.iloc[0]["ID"])
                        st.session_state.staff_page = "Adjust Stock"
                        st.rerun()

            with col2:
                if st.button("Edit Item Details", width="stretch"):
                    selected_rows = edited_inv[edited_inv["Select"] == True]
                    if len(selected_rows) == 0:
                        st.error("Please select an item to edit.")
                    elif len(selected_rows) > 1:
                        st.error("Please select only one item.")
                    else:
                        st.session_state.selected_item_id = int(selected_rows.iloc[0]["ID"])
                        st.session_state.staff_page = "Edit Item"
                        st.rerun()

        st.divider()
        col_add_item, col_export_inv = st.columns(2)
        with col_add_item:
            if st.button("Add New Item Type", width="stretch"):
                st.session_state.staff_page = "Add Item"
                st.rerun()
        with col_export_inv:
            if st.button("Export Inventory CSV", width="stretch"):
                try:
                    filepath = manager.export_inventory_csv()
                    st.success(f"Inventory exported to '{filepath}'.")
                    with open(filepath, "rb") as f:
                        st.download_button(
                            label="Download Inventory CSV",
                            data=f.read(),
                            file_name=os.path.basename(filepath),
                            mime="text/csv",
                            width="stretch"
                        )
                except Exception as e:
                    st.error(f"Failed to export inventory: {e}")

    # =========================================================
    # Add New Item Type
    # =========================================================

    elif page == "Add Item":
        st.title("Add New Item to Inventory")

        item_name = st.text_input("Item Name")
        item_category = st.text_input("Category", placeholder="e.g., Grains, Canned Goods, Produce")
        initial_quantity = st.number_input("Initial Quantity", min_value=0.0, step=1.0, value=0.0)
        item_unit = st.text_input("Unit", value="pcs")
        min_quantity = st.number_input("Minimum Alert Quantity", min_value=0.0, step=1.0, value=5.0)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Add Item", width="stretch"):
                if not item_name.strip() or not item_category.strip() or not item_unit.strip():
                    st.error("Name, Category, and Unit are required.")
                else:
                    try:
                        manager.add_inventory_item(
                            name=item_name.strip(),
                            category=item_category.strip(),
                            quantity=initial_quantity,
                            unit=item_unit.strip(),
                            min_quantity=min_quantity
                        )
                        st.session_state.staff_page = "Inventory Success"
                        st.session_state.inv_success_msg = f"Item '{item_name.strip()}' successfully added to inventory."
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to add item: {e}")

        with col2:
            if st.button("Cancel", width="stretch"):
                st.session_state.staff_page = "Inventory"
                st.rerun()

    # =========================================================
    # Adjust Stock (Add / Deduct Stock)
    # =========================================================

    elif page == "Adjust Stock":
        st.title("Adjust Item Stock Quantity")

        if "selected_item_id" not in st.session_state:
            st.error("No item selected.")
            if st.button("Back to Inventory"):
                st.session_state.staff_page = "Inventory"
                st.rerun()
        else:
            item_id = st.session_state.selected_item_id
            target_item = manager.inventory.find_item_by_id(item_id)
            if target_item is None:
                st.error("Item not found.")
                if st.button("Back to Inventory"):
                    del st.session_state.selected_item_id
                    st.session_state.staff_page = "Inventory"
                    st.rerun()
            else:
                st.subheader(f"Item: {target_item.name} (Current Stock: {target_item.quantity} {target_item.unit})")

                action = st.radio("Adjustment Action", ["Add Stock (Stock In)", "Deduct Stock (Stock Out)"])
                amount = st.number_input("Quantity Amount", min_value=1.0, step=1.0, value=1.0)
                reason = st.text_input("Reason for Adjustment", placeholder="e.g., Weekly replenishment / Damaged items")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Apply Adjustment", width="stretch"):
                        try:
                            if "Add Stock" in action:
                                manager.add_stock(target_item.id, amount, reason=reason.strip() or "Manual Add Stock")
                                msg = f"Added {amount} {target_item.unit} to '{target_item.name}'. New total: {target_item.quantity}."
                            else:
                                if amount > target_item.quantity:
                                    st.error(f"Cannot deduct {amount}. Only {target_item.quantity} {target_item.unit} available.")
                                    return
                                manager.remove_stock(target_item.id, amount, reason=reason.strip() or "Manual Deduct Stock")
                                msg = f"Deducted {amount} {target_item.unit} from '{target_item.name}'. New total: {target_item.quantity}."

                            del st.session_state.selected_item_id
                            st.session_state.staff_page = "Inventory Success"
                            st.session_state.inv_success_msg = msg
                            st.rerun()
                        except Exception as e:
                            st.error(f"Stock adjustment failed: {e}")

                with col2:
                    if st.button("Cancel", width="stretch"):
                        del st.session_state.selected_item_id
                        st.session_state.staff_page = "Inventory"
                        st.rerun()

    # =========================================================
    # Edit Item Details
    # =========================================================

    elif page == "Edit Item":
        st.title("Edit Item Details")

        if "selected_item_id" not in st.session_state:
            st.error("No item selected.")
            if st.button("Back to Inventory"):
                st.session_state.staff_page = "Inventory"
                st.rerun()
        else:
            item_id = st.session_state.selected_item_id
            target_item = manager.inventory.find_item_by_id(item_id)
            if target_item is None:
                st.error("Item not found.")
                if st.button("Back to Inventory"):
                    del st.session_state.selected_item_id
                    st.session_state.staff_page = "Inventory"
                    st.rerun()
            else:
                st.subheader(f"Editing Item #{target_item.id}: {target_item.name}")

                new_name = st.text_input("Item Name", value=target_item.name)
                new_cat = st.text_input("Category", value=target_item.category)
                new_unit = st.text_input("Unit", value=target_item.unit)
                new_min_qty = st.number_input("Minimum Alert Quantity", min_value=0.0, step=1.0, value=float(target_item.min_quantity))

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Save Item Details", width="stretch"):
                        if not new_name.strip() or not new_cat.strip() or not new_unit.strip():
                            st.error("All fields are required.")
                        else:
                            try:
                                target_item.name = new_name.strip()
                                target_item.category = new_cat.strip()
                                target_item.unit = new_unit.strip()
                                target_item.min_quantity = new_min_qty
                                manager._save_data()

                                del st.session_state.selected_item_id
                                st.session_state.staff_page = "Inventory Success"
                                st.session_state.inv_success_msg = f"Item #{target_item.id} details updated successfully."
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to save item details: {e}")

                with col2:
                    if st.button("Cancel", width="stretch"):
                        del st.session_state.selected_item_id
                        st.session_state.staff_page = "Inventory"
                        st.rerun()

    elif page == "Inventory Success":
        success_page(
            "Inventory Updated",
            "Inventory has been updated successfully!",
            st.session_state.get("inv_success_msg", "Stock changes saved."),
            "Inventory"
        )

    # =========================================================
    # System Profile & Information (View Only for Staff)
    # =========================================================

    elif page == "System":
        st.title("System Information")

        current_address = getattr(manager, "address", "") or ""
        current_description = getattr(manager, "description", "") or ""
        stations = manager.get_stations()

        col1, col2 = st.columns([1, 1])
        with col1:
            st.subheader("FoodBank Address")
            st.info(current_address if current_address.strip() else "*(Not set)*")

        with col2:
            st.subheader("FoodBank Description")
            st.info(current_description if current_description.strip() else "*(Not set)*")

        st.markdown("---")
        st.subheader("Collection Centers / Stations Directory")

        stations_data = []
        for station in stations:
            stations_data.append({
                "ID": station.get("id"),
                "Station Name": station.get("name", ""),
                "Station Address": station.get("address", ""),
                "Select": False
            })

        if not stations_data:
            st.info("No collection centers/stations registered yet.")
        else:
            station_df = pd.DataFrame(stations_data)
            st.data_editor(
                station_df,
                column_config={
                    "ID": st.column_config.NumberColumn("ID", width="small", disabled=True),
                    "Station Name": st.column_config.TextColumn("Station Name", width="medium", disabled=True),
                    "Station Address": st.column_config.TextColumn("Station Address", width="large", disabled=True),
                    "Select": st.column_config.CheckboxColumn("Select", width="small")
                },
                hide_index=True,
                width="stretch",
                key="staff_stations_table"
            )


# Functional alias
staff_page = show_staff_page
