import os
import urllib.parse
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
        hq_addr = getattr(manager, "address", "") or "FoodBank Central Hub"

        for h in manager.food_hampers:
            curr_status = h.status[0] if isinstance(h.status, list) and h.status else (h.status or "created")
            is_assigned_to_me = (h.volunteer_id is not None and str(h.volunteer_id) == user_id_str)
            is_in_work_list = hasattr(user, "work") and (h.id in user.work or f"deliver_hamper_{h.id}" in user.work)

            if (is_assigned_to_me or is_in_work_list) and str(curr_status).lower() != "delivered":
                client_obj = manager.find_client_by_id(h.client_id) if h.client_id else None
                client_name = client_obj.name if client_obj else f"Client #{h.client_id}"
                client_addr = getattr(client_obj, "address", "") or "Address on file"
                pickup_loc = f"FoodBank Central Hub ({hq_addr})"
                dropoff_loc = f"{client_name} ({client_addr})"
                route_flow = f"FoodBank Hub ➔ {client_name}"

                active_tasks.append({
                    "Task Type": "Food Hamper Delivery",
                    "ID": h.id,
                    "Pickup Point": pickup_loc,
                    "Dropoff Point": dropoff_loc,
                    "Route Flow": route_flow,
                    "Status": str(curr_status).upper(),
                    "Items Count": len(getattr(h, "items", [])),
                })

        for d in manager.donations:
            curr_status = d.status[0] if isinstance(d.status, list) and d.status else (d.status or "created")
            is_assigned_to_me = (d.volunteer_id is not None and str(d.volunteer_id) == user_id_str)
            is_in_work_list = hasattr(user, "work") and (d.id in user.work or f"collect_donation_{d.id}" in user.work)

            if (is_assigned_to_me or is_in_work_list) and str(curr_status).lower() not in ("collected", "stocked"):
                st_val = getattr(d, "station", None)
                if st_val is not None:
                    st_obj = manager.find_station_by_id(st_val)
                    st_addr = st_obj.get("address", "") if st_obj else ""
                    st_name = st_obj["name"] if st_obj else f"Station ID: {st_val}"
                    pickup_loc = f"Station: {st_name} ({st_addr})" if st_addr else f"Station: {st_name}"
                    route_flow = f"{st_name} ➔ FoodBank Hub"
                else:
                    donor_obj = manager.find_donor_by_id(d.donor_id)
                    d_name = donor_obj.name if donor_obj else f"Donor #{d.donor_id}"
                    pickup_loc = f"Donor: {d_name}"
                    route_flow = f"{d_name} ➔ FoodBank Hub"

                dropoff_loc = f"FoodBank Central Hub ({hq_addr})"

                active_tasks.append({
                    "Task Type": "Donation Collection",
                    "ID": d.id,
                    "Pickup Point": pickup_loc,
                    "Dropoff Point": dropoff_loc,
                    "Route Flow": route_flow,
                    "Status": str(curr_status).upper(),
                    "Items Count": len(getattr(d, "items", [])),
                })

        if not active_tasks:
            st.info("You currently have no active jobs assigned. Go to 'Claim Jobs' to pick up available tasks!")
        else:
            for t in active_tasks:
                task_type = t["Task Type"]
                task_id = t["ID"]
                icon = "📦" if task_type == "Donation Collection" else "🍲"
                with st.container(border=True):
                    h_col1, h_col2 = st.columns([3, 1])
                    with h_col1:
                        st.markdown(f"#### {icon} {task_type} #{task_id}")
                    with h_col2:
                        st.markdown(f"**Status:** `{t['Status']}`")

                    st.info(f"🧭 **Delivery Direction:** {t['Route Flow']}\n\n*Pickup:* {t['Pickup Point']} ➡️ *Drop-off:* {t['Dropoff Point']}")

                    d_col1, d_col2 = st.columns(2)
                    with d_col1:
                        st.write(f"🚩 **From (Pickup):** {t['Pickup Point']}")
                        st.write(f"🏁 **To (Delivery):** {t['Dropoff Point']}")
                    with d_col2:
                        st.write(f"📦 **Items:** {t['Items Count']} item(s)")
                        st.write(f"🗺️ **Transit Flow:** `{t['Route Flow']}`")

                    if st.button("🔍 View Details & Navigation", key=f"btn_act_task_{task_type}_{task_id}", width="stretch"):
                        st.session_state.selected_task_type = task_type
                        st.session_state.selected_task_id = task_id
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

                    st.subheader("🧭 Delivery Route & Navigation Direction")
                    hq_addr = getattr(manager, "address", "") or "FoodBank Central Warehouse (Main Hub)"
                    with st.container(border=True):
                        r_c1, r_arr, r_c2 = st.columns([5, 1, 5])
                        with r_c1:
                            st.markdown("##### 1️⃣ Pickup Point (Origin)")
                            st.markdown("🏢 **FoodBank Central Hub**")
                            st.caption(f"📍 {hq_addr}")
                            map_hq = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(hq_addr)}"
                            st.markdown(f"[🗺️ Open in Google Maps]({map_hq})")
                        with r_arr:
                            st.markdown("<h2 style='text-align:center;'>➡️</h2>", unsafe_allow_html=True)
                        with r_c2:
                            st.markdown("##### 2️⃣ Drop-off Destination (Recipient)")
                            st.markdown(f"🏠 **Client:** {client_name}")
                            st.caption(f"📍 {client_addr}")
                            map_dest = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(client_addr)}"
                            st.markdown(f"[🗺️ Open in Google Maps]({map_dest})")

                    st.write("")
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
                        with st.container(border=True):
                            for it in target_hamper.items:
                                if isinstance(it, dict):
                                    it_name = it.get("name", "Item")
                                    it_qty = it.get("quantity", 1)
                                else:
                                    it_name = getattr(it, "name", str(it))
                                    it_qty = getattr(it, "quantity", 1)
                                c1, c2 = st.columns([3, 1])
                                with c1:
                                    st.markdown(f"🍲 **{it_name}**")
                                with c2:
                                    st.markdown(f"**Quantity:** `{it_qty}`")

                    if getattr(target_hamper, "status_history", None):
                        st.subheader("Status Timeline History")
                        with st.container(border=True):
                            for h in target_hamper.status_history:
                                st.markdown(f"⏱️ **{str(h.get('status')).upper()}** — *{h.get('timestamp')}*")

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

                    st.subheader("🧭 Collection Route & Navigation Direction")
                    hq_addr = getattr(manager, "address", "") or "FoodBank Central Warehouse (Main Hub)"
                    st_addr = st_obj.get("address", "") if st_val is not None and st_obj else ""
                    with st.container(border=True):
                        r_c1, r_arr, r_c2 = st.columns([5, 1, 5])
                        with r_c1:
                            st.markdown("##### 1️⃣ Pickup Point (Origin)")
                            st.markdown(f"📍 **{station_display}**")
                            pickup_query = st_addr if st_addr else (donor_name if donor_obj else station_display)
                            map_pickup = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(pickup_query)}"
                            st.markdown(f"[🗺️ Open in Google Maps]({map_pickup})")
                        with r_arr:
                            st.markdown("<h2 style='text-align:center;'>➡️</h2>", unsafe_allow_html=True)
                        with r_c2:
                            st.markdown("##### 2️⃣ Drop-off Destination (FoodBank)")
                            st.markdown("🏢 **FoodBank Central Hub**")
                            st.caption(f"📍 {hq_addr}")
                            map_hq = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(hq_addr)}"
                            st.markdown(f"[🗺️ Open in Google Maps]({map_hq})")

                    st.write("")
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
                        with st.container(border=True):
                            for it in target_donation.items:
                                if isinstance(it, dict):
                                    it_name = it.get("name", "Item")
                                    it_qty = it.get("quantity", 1)
                                else:
                                    it_name = getattr(it, "name", str(it))
                                    it_qty = getattr(it, "quantity", 1)
                                c1, c2 = st.columns([3, 1])
                                with c1:
                                    st.markdown(f"📦 **{it_name}**")
                                with c2:
                                    st.markdown(f"**Quantity:** `{it_qty}`")

                    if getattr(target_donation, "status_history", None):
                        st.subheader("Status Timeline History")
                        with st.container(border=True):
                            for h in target_donation.status_history:
                                st.markdown(f"⏱️ **{str(h.get('status')).upper()}** — *{h.get('timestamp')}*")

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
        hq_addr = getattr(manager, "address", "") or "FoodBank Central Hub"

        # Claimable Hampers
        if task_type_filter in ("All", "Food Hamper Delivery"):
            open_hampers = manager.get_claimable_hampers()
            for h in open_hampers:
                curr_status = h.status[0] if isinstance(h.status, list) and h.status else (h.status or "created")
                client_obj = manager.find_client_by_id(h.client_id) if h.client_id else None
                client_name = client_obj.name if client_obj else f"Client #{h.client_id}"
                client_addr = getattr(client_obj, "address", "") or "Address on file"
                pickup_loc = f"FoodBank Central Hub ({hq_addr})"
                dropoff_loc = f"{client_name} ({client_addr})"
                route_flow = f"FoodBank Hub ➔ {client_name}"

                claimable_tasks.append({
                    "Task Type": "Food Hamper Delivery",
                    "ID": h.id,
                    "Pickup Point": pickup_loc,
                    "Dropoff Point": dropoff_loc,
                    "Route Flow": route_flow,
                    "Status": str(curr_status).upper(),
                    "Items Count": len(getattr(h, "items", [])),
                })

        # Claimable Donations
        if task_type_filter in ("All", "Donation Collection"):
            open_donations = manager.get_claimable_donations()
            for d in open_donations:
                curr_status = d.status[0] if isinstance(d.status, list) and d.status else (d.status or "created")
                st_val = getattr(d, "station", None)
                if st_val is not None:
                    st_obj = manager.find_station_by_id(st_val)
                    st_addr = st_obj.get("address", "") if st_obj else ""
                    st_name = st_obj["name"] if st_obj else f"Station ID: {st_val}"
                    pickup_loc = f"Station: {st_name} ({st_addr})" if st_addr else f"Station: {st_name}"
                    route_flow = f"{st_name} ➔ FoodBank Hub"
                else:
                    donor_obj = manager.find_donor_by_id(d.donor_id)
                    d_name = donor_obj.name if donor_obj else f"Donor #{d.donor_id}"
                    pickup_loc = f"Donor: {d_name}"
                    route_flow = f"{d_name} ➔ FoodBank Hub"

                dropoff_loc = f"FoodBank Central Hub ({hq_addr})"

                claimable_tasks.append({
                    "Task Type": "Donation Collection",
                    "ID": d.id,
                    "Pickup Point": pickup_loc,
                    "Dropoff Point": dropoff_loc,
                    "Route Flow": route_flow,
                    "Status": str(curr_status).upper(),
                    "Items Count": len(getattr(d, "items", [])),
                })

        if not claimable_tasks:
            st.info("No open tasks currently available to claim. Please check back later!")
        else:
            for task in claimable_tasks:
                chosen_type = task["Task Type"]
                chosen_id = task["ID"]
                icon = "📦" if chosen_type == "Donation Collection" else "🍲"
                with st.container(border=True):
                    h_col1, h_col2 = st.columns([3, 1])
                    with h_col1:
                        st.markdown(f"#### {icon} {chosen_type} #{chosen_id}")
                    with h_col2:
                        st.markdown(f"**Status:** `{task['Status']}`")

                    st.info(f"🧭 **Route Direction:** {task['Route Flow']}\n\n*Pickup:* {task['Pickup Point']} ➡️ *Drop-off:* {task['Dropoff Point']}")

                    d_col1, d_col2 = st.columns(2)
                    with d_col1:
                        st.write(f"🚩 **From (Pickup):** {task['Pickup Point']}")
                        st.write(f"🏁 **To (Delivery):** {task['Dropoff Point']}")
                    with d_col2:
                        st.write(f"📦 **Items Count:** {task['Items Count']} item(s)")
                        st.write(f"🗺️ **Transit Route:** `{task['Route Flow']}`")

                    if st.button(f"⚡ Claim {chosen_type} #{chosen_id}", key=f"btn_claim_{chosen_type}_{chosen_id}", type="primary", width="stretch"):
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
                    "Route Flow": f"FoodBank Hub ➔ {client_name}",
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
                    st_name = st_obj["name"] if st_obj else f"Station #{st_val}"
                else:
                    donor_obj = manager.find_donor_by_id(d.donor_id)
                    loc = f"Donor: {donor_obj.name}" if donor_obj else f"Donor #{d.donor_id}"
                    st_name = donor_obj.name if donor_obj else f"Donor #{d.donor_id}"

                completed_time = d.status_history[-1]["timestamp"] if getattr(d, "status_history", None) else "N/A"

                completed_tasks.append({
                    "Task Type": "Donation Collection",
                    "Task ID": d.id,
                    "Recipient / Station": loc,
                    "Route Flow": f"{st_name} ➔ FoodBank Hub",
                    "Items Count": len(getattr(d, "items", [])),
                    "Status": str(curr_status).upper(),
                    "Completed At": completed_time
                })

        if not completed_tasks:
            st.info("You have not completed any tasks yet. Keep up the good work!")
        else:
            for task in completed_tasks:
                task_type = task["Task Type"]
                task_id = task["Task ID"]
                icon = "📦" if task_type == "Donation Collection" else "🍲"
                with st.container(border=True):
                    h_col1, h_col2 = st.columns([3, 1])
                    with h_col1:
                        st.markdown(f"#### {icon} {task_type} #{task_id}")
                    with h_col2:
                        st.markdown(f"**Status:** `{task['Status']}`")

                    st.caption(f"🧭 **Completed Route Direction:** `{task.get('Route Flow', 'N/A')}`")

                    d_col1, d_col2, d_col3 = st.columns(3)
                    with d_col1:
                        st.write(f"📍 **Target / Location:** {task['Recipient / Station']}")
                    with d_col2:
                        st.write(f"📦 **Items:** {task['Items Count']} item(s)")
                    with d_col3:
                        st.write(f"🕒 **Completed At:** {task['Completed At']}")

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
