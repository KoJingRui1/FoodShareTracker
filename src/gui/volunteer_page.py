import os
import streamlit as st
import pandas as pd
import datetime
from src.app.volunteer import VolunteerUser
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
        st.session_state.volunteer_page = return_page
        if "selected_task_id" in st.session_state:
            del st.session_state.selected_task_id
        if "selected_task_type" in st.session_state:
            del st.session_state.selected_task_type
        st.rerun()


# =========================================================
# Volunteer Portal Main Page
# =========================================================

def show_volunteer_page(manager, user):
    """Render the volunteer portal dashboard and task management interface."""
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

    avatar_path = user.profile_image if getattr(user, "profile_image", None) and os.path.exists(user.profile_image) else "assets/default_avatar.png"
    st.sidebar.image(avatar_path, width="stretch")
    st.sidebar.markdown(f"### {user.name}")
    st.sidebar.caption("Volunteer")
    st.sidebar.divider()

    if "volunteer_page" not in st.session_state:
        st.session_state.volunteer_page = "Active Jobs"

    if st.sidebar.button("Active Jobs", width="stretch"):
        st.session_state.volunteer_page = "Active Jobs"

    if st.sidebar.button("Claim Jobs", width="stretch"):
        st.session_state.volunteer_page = "Claim Jobs"

    if st.sidebar.button("Completed Jobs", width="stretch"):
        st.session_state.volunteer_page = "Completed Jobs"

    if st.sidebar.button("Profile", width="stretch"):
        st.session_state.volunteer_page = "Profile"

    st.sidebar.divider()
    if st.sidebar.button("Logout", width="stretch"):
        st.session_state.user = None
        st.session_state.current_page = "main"
        st.rerun()

    page = st.session_state.volunteer_page

    # =========================================================
    # Active Jobs (Now in progress)
    # =========================================================

    if page == "Active Jobs":
        st.title("My Active Jobs")
        st.info("View your ongoing delivery and collection assignments. Click 'View Task Details' to see instructions, client allergies, or report issues.")

        # Find active hampers assigned to this volunteer
        active_tasks = []
        user_id_str = str(user.id)

        for h in manager.food_hampers:
            curr_status = h.status[0] if isinstance(h.status, list) and h.status else (h.status or "created")
            is_assigned_to_me = (h.volunteer_id is not None and str(h.volunteer_id) == user_id_str)
            is_in_work_list = hasattr(user, "work") and (h.id in user.work or f"deliver_hamper_{h.id}" in user.work)

            if (is_assigned_to_me or is_in_work_list) and str(curr_status).lower() != "delivered":
                client_obj = manager.find_client_by_id(h.client_id) if h.client_id else None
                client_name = client_obj.name if client_obj else f"Client #{h.client_id}"
                client_addr = getattr(client_obj, "address", "") or "No address provided"

                active_tasks.append({
                    "Task Type": "Food Hamper Delivery",
                    "ID": h.id,
                    "Destination / Target": f"{client_name} ({client_addr})",
                    "Status": str(curr_status).upper(),
                    "Items Count": len(getattr(h, "items", [])),
                    "Select": False
                })

        for d in manager.donations:
            curr_status = d.status[0] if isinstance(d.status, list) and d.status else (d.status or "created")
            is_assigned_to_me = (d.volunteer_id is not None and str(d.volunteer_id) == user_id_str)
            is_in_work_list = hasattr(user, "work") and (d.id in user.work or f"collect_donation_{d.id}" in user.work)

            if (is_assigned_to_me or is_in_work_list) and str(curr_status).lower() not in ("collected", "stocked"):
                st_val = getattr(d, "station", None)
                if st_val is not None:
                    st_obj = manager.find_station_by_id(st_val)
                    loc = f"Station: {st_obj['name']}" if st_obj else f"Station ID: {st_val}"
                else:
                    donor_obj = manager.find_donor_by_id(d.donor_id)
                    loc = f"Donor: {donor_obj.name}" if donor_obj else f"Donor #{d.donor_id}"

                active_tasks.append({
                    "Task Type": "Donation Collection",
                    "ID": d.id,
                    "Destination / Target": loc,
                    "Status": str(curr_status).upper(),
                    "Items Count": len(getattr(d, "items", [])),
                    "Select": False
                })

        if not active_tasks:
            st.info("You currently have no active jobs assigned. Go to 'Claim Jobs' to pick up available tasks!")
        else:
            task_df = pd.DataFrame(active_tasks)
            edited_tasks = st.data_editor(
                task_df,
                column_config={
                    "Task Type": st.column_config.TextColumn("Task Type", width="medium", disabled=True),
                    "ID": st.column_config.NumberColumn("ID", width="small", disabled=True),
                    "Destination / Target": st.column_config.TextColumn("Destination / Target", width="large", disabled=True),
                    "Status": st.column_config.TextColumn("Status", width="small", disabled=True),
                    "Items Count": st.column_config.NumberColumn("Items Count", width="small", disabled=True),
                    "Select": st.column_config.CheckboxColumn("Select", width="small")
                },
                hide_index=True,
                width="stretch",
                key="active_jobs_table"
            )

            if st.button("View Task Details", width="stretch"):
                selected_rows = edited_tasks[edited_tasks["Select"] == True]
                if len(selected_rows) == 0:
                    st.error("Please select a task to view details.")
                elif len(selected_rows) > 1:
                    st.error("Please select only one task.")
                else:
                    st.session_state.selected_task_type = str(selected_rows.iloc[0]["Task Type"])
                    st.session_state.selected_task_id = int(selected_rows.iloc[0]["ID"])
                    st.session_state.volunteer_page = "Task Detail"
                    st.rerun()

        st.divider()
        if st.button("Find & Claim New Jobs", width="stretch"):
            st.session_state.volunteer_page = "Claim Jobs"
            st.rerun()

    # =========================================================
    # Task Details & Reporting
    # =========================================================

    elif page == "Task Detail":
        if "selected_task_id" not in st.session_state or "selected_task_type" not in st.session_state:
            st.error("No task selected.")
            if st.button("Back to Active Jobs"):
                st.session_state.volunteer_page = "Active Jobs"
                st.rerun()
        else:
            task_type = st.session_state.selected_task_type
            task_id = st.session_state.selected_task_id

            if task_type == "Food Hamper Delivery":
                target_hamper = manager.find_food_hamper_by_id(task_id)
                if target_hamper is None:
                    st.error("Food hamper not found.")
                    if st.button("Back to Active Jobs"):
                        st.session_state.volunteer_page = "Active Jobs"
                        st.rerun()
                else:
                    st.title(f"Food Hamper Delivery #{target_hamper.id}")
                    curr_status = target_hamper.status[0] if isinstance(target_hamper.status, list) and target_hamper.status else (target_hamper.status or "created")

                    client_obj = manager.find_client_by_id(target_hamper.client_id)
                    client_name = client_obj.name if client_obj else f"Client #{target_hamper.client_id}"
                    client_email = getattr(client_obj, "email", "N/A") if client_obj else "N/A"
                    client_addr = getattr(client_obj, "address", "N/A") if client_obj else "N/A"

                    # 1. Prominent Allergy Alert
                    client_allergies = getattr(client_obj, "allergy", []) if client_obj else []
                    if isinstance(client_allergies, list) and client_allergies:
                        allergy_str = ", ".join([str(a) for a in client_allergies])
                        st.error(f"⚠️ **ALLERGY ALERT:** {allergy_str} (Please verify that NO matching allergens are present in this food hamper!)")
                    elif isinstance(client_allergies, str) and client_allergies.strip():
                        st.error(f"⚠️ **ALLERGY ALERT:** {client_allergies.strip()} (Please verify that NO matching allergens are present in this food hamper!)")
                    else:
                        st.success("✅ **Allergy Status:** No known allergies recorded for this client.")

                    # 2. Status Banners & Handover instruction
                    if str(curr_status).lower() == "packed":
                        st.info("📦 **Hamper is PACKED & Ready for Delivery!** Please deliver the food hamper to the recipient client at the address below. Once delivered, the client will confirm receipt on their portal.")
                    elif str(curr_status).lower() == "assigned":
                        st.warning("⏳ **Hamper Status: ASSIGNED.** Hamper is awaiting packing by FoodBank warehouse staff before delivery can take place.")
                    elif str(curr_status).lower() == "delivered":
                        st.success("🎉 **Status: DELIVERED.** The client has confirmed receipt of this food hamper.")

                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.metric("Hamper ID", f"#{target_hamper.id}")
                    with c2:
                        st.metric("Status", str(curr_status).upper())
                    with c3:
                        st.metric("Items Breakdown", f"{len(target_hamper.items)} type(s)")

                    st.divider()

                    col_left, col_right = st.columns(2)
                    with col_left:
                        st.subheader("Recipient Client & Address")
                        st.write(f"**Client Name:** {client_name}")
                        st.write(f"**Delivery Address:** {client_addr}")
                        st.write(f"**Client Email:** {client_email}")
                        st.write(f"**Notes / Instructions:** {target_hamper.description or 'None'}")

                    with col_right:
                        st.subheader("Delivery Status & Handover")
                        last_time = target_hamper.status_history[-1]["timestamp"] if getattr(target_hamper, "status_history", None) else "N/A"
                        st.write(f"**Last Status Updated:** {last_time}")
                        st.info("👉 **Handover Protocol:** Deliver this hamper to the client at the destination address. The recipient client will confirm delivery receipt.")

                    st.subheader("Hamper Items Breakdown")
                    if not target_hamper.items:
                        st.info("No items listed in this hamper.")
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

                    # Report / Flag Issue Section
                    if getattr(target_hamper, "flagged_issue", None):
                        st.warning(f"⚠️ **Reported Issue on Record:** {target_hamper.flagged_issue.get('issue')} (Reported at {target_hamper.flagged_issue.get('flagged_at')})")

                    st.subheader("Report an Issue / Obstacle")
                    st.caption("If you encounter any problem (e.g. client not at home, incorrect address, damaged items), report it immediately.")
                    issue_text = st.text_input("Issue Description", placeholder="e.g. Client not at home / Address unreachable", key=f"hamper_issue_{target_hamper.id}")
                    if st.button("Submit Issue Report", key=f"btn_flag_hamper_{target_hamper.id}"):
                        if not issue_text.strip():
                            st.error("Please enter a description of the issue.")
                        else:
                            try:
                                manager.flag_issue("hamper", target_hamper.id, issue_text.strip(), volunteer_id=user.id)
                                st.success("Issue reported successfully to FoodBank staff.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to report issue: {e}")

                    st.write("")
                    if st.button("Back to Active Jobs"):
                        del st.session_state.selected_task_id
                        del st.session_state.selected_task_type
                        st.session_state.volunteer_page = "Active Jobs"
                        st.rerun()

            elif task_type == "Donation Collection":
                target_donation = manager.find_donation_by_id(task_id)
                if target_donation is None:
                    st.error("Donation record not found.")
                    if st.button("Back to Active Jobs"):
                        st.session_state.volunteer_page = "Active Jobs"
                        st.rerun()
                else:
                    st.title(f"Donation Collection #{target_donation.id}")
                    curr_status = target_donation.status[0] if isinstance(target_donation.status, list) and target_donation.status else (target_donation.status or "created")

                    donor_obj = manager.find_donor_by_id(target_donation.donor_id)
                    donor_name = donor_obj.name if donor_obj else f"Donor #{target_donation.donor_id}"
                    donor_email = getattr(donor_obj, "email", "N/A") if donor_obj else "N/A"

                    st_val = getattr(target_donation, "station", None)
                    if st_val is not None:
                        st_obj = manager.find_station_by_id(st_val)
                        station_display = f"ID: {st_val} - {st_obj['name']} ({st_obj.get('address', '')})" if st_obj else f"Station ID: {st_val}"
                    else:
                        station_display = "Pickup directly from Donor"

                    # Status instructions
                    st.info("🚚 **Collection Protocol:** Collect the donated food items from the donor or station, and deliver them to the FoodBank warehouse. Once handed over, FoodBank staff will confirm receipt ('collected').")

                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.metric("Donation ID", f"#{target_donation.id}")
                    with c2:
                        st.metric("Status", str(curr_status).upper())
                    with c3:
                        st.metric("Items Breakdown", f"{len(target_donation.items)} type(s)")

                    st.divider()

                    col_left, col_right = st.columns(2)
                    with col_left:
                        st.subheader("Donor & Dropoff Location")
                        st.write(f"**Donor Name:** {donor_name}")
                        st.write(f"**Donor Email:** {donor_email}")
                        st.write(f"**Dropoff / Pickup Station:** {station_display}")
                        st.write(f"**Donation Notes:** {target_donation.description or 'None'}")

                    with col_right:
                        st.subheader("Handover Status")
                        last_time = target_donation.status_history[-1]["timestamp"] if getattr(target_donation, "status_history", None) else "N/A"
                        st.write(f"**Last Status Updated:** {last_time}")
                        st.info("👉 **Awaiting Staff Confirmation:** Once you bring the items to the FoodBank, staff will verify the inventory and mark the donation as collected.")

                    st.subheader("Donated Items Breakdown")
                    if not target_donation.items:
                        st.info("No items listed in this donation.")
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

                    # Report / Flag Issue Section
                    if getattr(target_donation, "flagged_issue", None):
                        st.warning(f"⚠️ **Reported Issue on Record:** {target_donation.flagged_issue.get('issue')} (Reported at {target_donation.flagged_issue.get('flagged_at')})")

                    st.subheader("Report an Issue / Obstacle")
                    st.caption("If you encounter any problem (e.g. donor absent, damaged items, incorrect station), report it immediately.")
                    issue_text = st.text_input("Issue Description", placeholder="e.g. Donor absent / Station locker locked", key=f"don_issue_{target_donation.id}")
                    if st.button("Submit Issue Report", key=f"btn_flag_don_{target_donation.id}"):
                        if not issue_text.strip():
                            st.error("Please enter a description of the issue.")
                        else:
                            try:
                                manager.flag_issue("donation", target_donation.id, issue_text.strip(), volunteer_id=user.id)
                                st.success("Issue reported successfully to FoodBank staff.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to report issue: {e}")

                    st.write("")
                    if st.button("Back to Active Jobs"):
                        del st.session_state.selected_task_id
                        del st.session_state.selected_task_type
                        st.session_state.volunteer_page = "Active Jobs"
                        st.rerun()

    # =========================================================
    # Claim Jobs (Task Pool)
    # =========================================================

    elif page == "Claim Jobs":
        st.title("Available Tasks to Claim")
        st.info("Browse open tasks looking for volunteers. Select a task and click 'Claim Selected Task' to assign it to yourself.")

        task_type_filter = st.selectbox("Filter Task Type", ["All", "Food Hamper Delivery", "Donation Collection"])

        claimable_tasks = []

        # Claimable Hampers
        if task_type_filter in ("All", "Food Hamper Delivery"):
            open_hampers = manager.get_claimable_hampers()
            for h in open_hampers:
                curr_status = h.status[0] if isinstance(h.status, list) and h.status else (h.status or "created")
                client_obj = manager.find_client_by_id(h.client_id) if h.client_id else None
                client_name = client_obj.name if client_obj else f"Client #{h.client_id}"
                client_addr = getattr(client_obj, "address", "") or "No address provided"

                claimable_tasks.append({
                    "Task Type": "Food Hamper Delivery",
                    "ID": h.id,
                    "Destination / Target": f"{client_name} ({client_addr})",
                    "Status": str(curr_status).upper(),
                    "Items Count": len(getattr(h, "items", [])),
                    "Select": False
                })

        # Claimable Donations
        if task_type_filter in ("All", "Donation Collection"):
            open_donations = manager.get_claimable_donations()
            for d in open_donations:
                curr_status = d.status[0] if isinstance(d.status, list) and d.status else (d.status or "created")
                st_val = getattr(d, "station", None)
                if st_val is not None:
                    st_obj = manager.find_station_by_id(st_val)
                    loc = f"Station: {st_obj['name']}" if st_obj else f"Station ID: {st_val}"
                else:
                    donor_obj = manager.find_donor_by_id(d.donor_id)
                    loc = f"Donor: {donor_obj.name}" if donor_obj else f"Donor #{d.donor_id}"

                claimable_tasks.append({
                    "Task Type": "Donation Collection",
                    "ID": d.id,
                    "Destination / Target": loc,
                    "Status": str(curr_status).upper(),
                    "Items Count": len(getattr(d, "items", [])),
                    "Select": False
                })

        if not claimable_tasks:
            st.info("No open tasks currently available to claim. Please check back later!")
        else:
            claim_df = pd.DataFrame(claimable_tasks)
            edited_claim = st.data_editor(
                claim_df,
                column_config={
                    "Task Type": st.column_config.TextColumn("Task Type", width="medium", disabled=True),
                    "ID": st.column_config.NumberColumn("ID", width="small", disabled=True),
                    "Destination / Target": st.column_config.TextColumn("Destination / Target", width="large", disabled=True),
                    "Status": st.column_config.TextColumn("Status", width="small", disabled=True),
                    "Items Count": st.column_config.NumberColumn("Items Count", width="small", disabled=True),
                    "Select": st.column_config.CheckboxColumn("Select", width="small")
                },
                hide_index=True,
                width="stretch",
                key="claim_jobs_table"
            )

            if st.button("Claim Selected Task", width="stretch"):
                selected_rows = edited_claim[edited_claim["Select"] == True]
                if len(selected_rows) == 0:
                    st.error("Please select a task to claim.")
                elif len(selected_rows) > 1:
                    st.error("Please select only one task at a time.")
                else:
                    chosen_type = str(selected_rows.iloc[0]["Task Type"])
                    chosen_id = int(selected_rows.iloc[0]["ID"])
                    try:
                        if chosen_type == "Food Hamper Delivery":
                            manager.claim_hamper(user.id, chosen_id)
                        else:
                            manager.claim_donation(user.id, chosen_id)

                        st.session_state.volunteer_page = "Active Jobs"
                        st.success(f"{chosen_type} #{chosen_id} claimed successfully! Added to your Active Jobs.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Cannot claim task: {e}")

    # =========================================================
    # Completed Jobs (Read-only historical view)
    # =========================================================

    elif page == "Completed Jobs":
        st.title("My Completed Jobs")
        st.info("History of all tasks you have completed. (Read-only record)")

        user_id_str = str(user.id)
        completed_tasks = []

        # 1. Completed Food Hampers (delivered)
        for h in manager.food_hampers:
            curr_status = h.status[0] if isinstance(h.status, list) and h.status else (h.status or "")
            is_mine = (h.volunteer_id is not None and str(h.volunteer_id) == user_id_str)
            was_completed_work = hasattr(user, "completed_work") and (h.id in user.completed_work or f"deliver_hamper_{h.id}" in user.completed_work)

            if (is_mine or was_completed_work) and str(curr_status).lower() == "delivered":
                client_obj = manager.find_client_by_id(h.client_id) if h.client_id else None
                client_name = client_obj.name if client_obj else f"Client #{h.client_id}"
                completed_time = h.status_history[-1]["timestamp"] if getattr(h, "status_history", None) else "N/A"

                completed_tasks.append({
                    "Task Type": "Food Hamper Delivery",
                    "Task ID": h.id,
                    "Recipient / Station": client_name,
                    "Items Count": len(getattr(h, "items", [])),
                    "Status": "DELIVERED",
                    "Completed At": completed_time
                })

        # 2. Completed Donations (collected or stocked)
        for d in manager.donations:
            curr_status = d.status[0] if isinstance(d.status, list) and d.status else (d.status or "")
            is_mine = (d.volunteer_id is not None and str(d.volunteer_id) == user_id_str)
            was_completed_work = hasattr(user, "completed_work") and (d.id in user.completed_work or f"collect_donation_{d.id}" in user.completed_work)

            if (is_mine or was_completed_work) and str(curr_status).lower() in ("collected", "stocked"):
                st_val = getattr(d, "station", None)
                if st_val is not None:
                    st_obj = manager.find_station_by_id(st_val)
                    loc = f"Station: {st_obj['name']}" if st_obj else f"Station ID: {st_val}"
                else:
                    donor_obj = manager.find_donor_by_id(d.donor_id)
                    loc = f"Donor: {donor_obj.name}" if donor_obj else f"Donor #{d.donor_id}"

                completed_time = d.status_history[-1]["timestamp"] if getattr(d, "status_history", None) else "N/A"

                completed_tasks.append({
                    "Task Type": "Donation Collection",
                    "Task ID": d.id,
                    "Recipient / Station": loc,
                    "Items Count": len(getattr(d, "items", [])),
                    "Status": str(curr_status).upper(),
                    "Completed At": completed_time
                })

        if not completed_tasks:
            st.info("You have not completed any tasks yet. Keep up the good work!")
        else:
            comp_df = pd.DataFrame(completed_tasks)
            st.dataframe(
                comp_df,
                hide_index=True,
                width="stretch"
            )

    # =========================================================
    # Volunteer Profile
    # =========================================================

    elif page == "Profile":
        st.title("My Volunteer Profile")

        col_img, col_info = st.columns([1, 3])
        with col_img:
            st.image(avatar_path if "avatar_path" in locals() else (user.profile_image if getattr(user, "profile_image", None) and os.path.exists(user.profile_image) else "assets/default_avatar.png"), width=150)
        with col_info:
            st.subheader(f"Name: {user.name}")
            st.write(f"**Volunteer ID:** {user.id}")
            st.write(f"**Email:** {user.email}")
            st.write(f"**Role:** Volunteer")
            active_count = len(getattr(user, "work", []))
            completed_count = len(getattr(user, "completed_work", []))
            st.write(f"**Active Jobs Count:** {active_count}")
            st.write(f"**Completed Jobs Count:** {completed_count}")

        st.divider()
        if st.button("Update Profile", width="stretch"):
            st.session_state.volunteer_page = "Update Profile"
            st.rerun()

    # =========================================================
    # Update Volunteer Profile
    # =========================================================

    elif page == "Update Profile":
        st.title("Update My Profile")
        choice = st.selectbox(
            "Update Term",
            ["Name", "Password", "Email", "Profile Image"]
        )

        if choice == "Name":
            new_name = st.text_input("Please enter your NEW NAME.")
            if st.button("Update Name"):
                if not manager.valid_name(new_name):
                    st.error("Invalid name.")
                elif new_name == user.name:
                    st.error("The new name is the same as your current name.")
                else:
                    manager.update_user(user.id, name=new_name.strip())
                    user.name = new_name.strip()
                    st.session_state.volunteer_page = "Profile Update Success"
                    st.rerun()

        elif choice == "Password":
            current_password = st.text_input("Please enter your CURRENT PASSWORD", type="password")
            new_password = st.text_input("Please enter your NEW PASSWORD", type="password")
            confirm_password = st.text_input("Please confirm your NEW PASSWORD", type="password")

            if st.button("Update Password"):
                if not verify_password(current_password, user.password):
                    st.error("Wrong current password.")
                elif not manager.valid_password(new_password):
                    st.error("Invalid password. Password must be at least 6 characters and include letters and numbers.")
                elif new_password != confirm_password:
                    st.error("Confirmation password does not match.")
                elif current_password == new_password:
                    st.error("The new password must be different from the current password.")
                else:
                    manager.update_user(user.id, password=new_password)
                    st.session_state.volunteer_page = "Profile Update Success"
                    st.rerun()

        elif choice == "Email":
            new_email = st.text_input("Please enter your NEW EMAIL.", type="email")
            if st.button("Update Email"):
                clean_email = new_email.strip()
                if "@" not in clean_email or "." not in clean_email.split("@")[-1]:
                    st.error("Please enter a valid email address.")
                elif clean_email.lower() == user.email.lower():
                    st.error("The new email is the same as your current email.")
                elif manager.find_user_by_email(clean_email) is not None:
                    st.error(f"Email '{clean_email}' is already registered.")
                else:
                    manager.update_user(user.id, email=clean_email)
                    user.email = clean_email
                    st.session_state.volunteer_page = "Profile Update Success"
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
                        st.session_state.volunteer_page = "Profile Update Success"
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to save uploaded image: {e}")

        st.divider()
        if st.button("Back to Profile"):
            st.session_state.volunteer_page = "Profile"
            st.rerun()

    elif page == "Profile Update Success":
        success_page(
            "Profile Updated",
            "Your profile has been updated successfully!",
            "Your profile changes have been saved.",
            "Profile"
        )


# Functional alias
volunteer_page = show_volunteer_page
