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

def show_donor_page(manager, user):
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

    avatar_path = user.profile_image if getattr(user, "profile_image", None) and os.path.exists(user.profile_image) else "assets/default_avatar.png"
    st.sidebar.image(avatar_path, width="stretch")
    st.sidebar.markdown(f"### {user.name}")
    st.sidebar.caption("Donor")
    st.sidebar.divider()

    if "donor_page" not in st.session_state:
        st.session_state.donor_page = "History"

    if st.sidebar.button("My Donations", width="stretch"):
        st.session_state.donor_page = "History"

    if st.sidebar.button("Make a Donation", width="stretch"):
        st.session_state.donor_page = "Donate"

    if st.sidebar.button("Profile", width="stretch"):
        st.session_state.donor_page = "Profile"

    st.sidebar.divider()
    if st.sidebar.button("Logout", width="stretch"):
        st.session_state.user = None
        st.session_state.current_page = "main"
        st.rerun()

    page = st.session_state.donor_page

    # =========================================================
    # My Donations History
    # =========================================================

    if page == "History":
        st.title("My Donations History")
        st.info("Track the status of your food donations. You may view details or cancel donations while they are still in 'created' status.")

        # Filter donations belonging to this donor
        my_donations = [d for d in manager.donations if str(d.donor_id) == str(user.id)]

        # Search / filter by status
        col_f1, col_f2 = st.columns([1, 3])
        with col_f1:
            status_filter = st.selectbox("Filter by Status", ["All", "created", "assigned", "collected", "stocked"])

        filtered_donations = []
        for d in my_donations:
            curr_status = d.status[0] if isinstance(d.status, list) and d.status else (d.status or "created")
            if status_filter != "All" and str(curr_status).lower() != status_filter.lower():
                continue

            # Station name
            st_val = getattr(d, "station", None)
            if st_val is not None:
                st_obj = manager.find_station_by_id(st_val)
                station_display = f"ID: {st_val} - {st_obj['name']}" if st_obj else f"Station ID: {st_val}"
            else:
                station_display = "Unassigned"

            items_count = len(getattr(d, "items", []))
            last_time = d.status_history[-1]["timestamp"] if getattr(d, "status_history", None) else "N/A"

            filtered_donations.append({
                "ID": d.id,
                "Station": station_display,
                "Status": str(curr_status).upper(),
                "Items Count": items_count,
                "Last Updated": last_time,
                "Select": False
            })

        if not filtered_donations:
            if not my_donations:
                st.info("You have not made any donations yet. Click 'Make a Donation' to support families in need!")
            else:
                st.info(f"No donations found with status '{status_filter}'.")
        else:
            for item in filtered_donations:
                don_id = item["ID"]
                with st.container(border=True):
                    head_col1, head_col2 = st.columns([3, 1])
                    with head_col1:
                        st.markdown(f"#### 🎁 Donation #{don_id}")
                    with head_col2:
                        st.markdown(f"**Status:** `{item['Status']}`")

                    det_c1, det_c2, det_c3 = st.columns(3)
                    with det_c1:
                        st.write(f"📍 **Station:** {item['Station']}")
                    with det_c2:
                        st.write(f"📦 **Items:** {item['Items Count']} item(s)")
                    with det_c3:
                        st.write(f"🕒 **Updated:** {item['Last Updated']}")

                    act_c1, act_c2 = st.columns(2)
                    with act_c1:
                        if st.button("🔍 View Details", key=f"btn_don_det_{don_id}", width="stretch"):
                            st.session_state.selected_donation_id = don_id
                            st.session_state.donor_page = "Donation Detail"
                            st.rerun()
                    with act_c2:
                        if item["Status"].lower() == "created":
                            if st.button("❌ Cancel / Delete", key=f"btn_don_del_{don_id}", width="stretch"):
                                try:
                                    manager.delete_donation(don_id, donor_id=user.id)
                                    st.success(f"Donation #{don_id} has been cancelled and removed.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Failed to cancel donation: {e}")
                        else:
                            st.caption("🔒 Status locked (collected / stocked)")

        st.divider()
        if st.button("Make a New Donation", width="stretch"):
            st.session_state.donor_page = "Donate"
            st.rerun()

    # =========================================================
    # Donation Detail
    # =========================================================

    elif page == "Donation Detail":
        st.title("Donation Detail")

        if "selected_donation_id" not in st.session_state:
            st.error("No donation selected.")
            if st.button("Back to My Donations"):
                st.session_state.donor_page = "History"
                st.rerun()
        else:
            donation_id = st.session_state.selected_donation_id
            target_donation = manager.find_donation_by_id(donation_id)
            if target_donation is None or str(target_donation.donor_id) != str(user.id):
                st.error("Donation record not found or access denied.")
                if st.button("Back to My Donations"):
                    del st.session_state.selected_donation_id
                    st.session_state.donor_page = "History"
                    st.rerun()
            else:
                curr_status = target_donation.status[0] if isinstance(target_donation.status, list) and target_donation.status else (target_donation.status or "created")
                
                # Status overview banner
                if str(curr_status).lower() == "created":
                    st.info("📌 **Status: CREATED** - Your donation is registered and awaiting volunteer assignment or dropoff confirmation.")
                elif str(curr_status).lower() == "assigned":
                    st.warning("🚚 **Status: ASSIGNED** - A volunteer has been assigned to pick up or receive your donation.")
                elif str(curr_status).lower() == "collected":
                    st.success("📦 **Status: COLLECTED** - Your donation has been collected and received by the FoodBank team!")
                elif str(curr_status).lower() == "stocked":
                    st.success("🎉 **Status: STOCKED** - Your donated items have been inspected and stocked into the warehouse inventory to support clients!")

                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("Donation ID", f"#{target_donation.id}")
                with c2:
                    st.metric("Current Status", str(curr_status).upper())
                with c3:
                    st.metric("Items Count", f"{len(target_donation.items)} item type(s)")

                st.divider()

                st_val = getattr(target_donation, "station", None)
                if st_val is not None:
                    st_obj = manager.find_station_by_id(st_val)
                    station_display = f"ID: {st_val} - {st_obj['name']} ({st_obj.get('address', '')})" if st_obj else f"Station ID: {st_val}"
                else:
                    station_display = "Unassigned"

                col_left, col_right = st.columns(2)
                with col_left:
                    st.subheader("Station & Delivery Location")
                    st.write(f"**Dropoff / Collection Station:** {station_display}")
                    st.write(f"**Notes / Instructions:** {target_donation.description or 'None'}")

                with col_right:
                    st.subheader("Tracking Information")
                    last_updated = target_donation.status_history[-1]["timestamp"] if getattr(target_donation, "status_history", None) else "N/A"
                    st.write(f"**Last Updated:** {last_updated}")
                    if getattr(target_donation, "flagged_issue", None):
                        st.warning(f"Note from FoodBank: {target_donation.flagged_issue.get('issue')}")

                st.subheader("Donated Items Breakdown")
                if not target_donation.items:
                    st.info("No items recorded in this donation.")
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

                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    # Can delete only if created
                    if str(curr_status).lower() == "created":
                        if st.button("Cancel & Delete This Donation", width="stretch"):
                            try:
                                manager.delete_donation(target_donation.id, donor_id=user.id)
                                st.session_state.donor_page = "Donation Success"
                                st.session_state.donor_success_msg = f"Donation #{target_donation.id} has been successfully cancelled."
                                del st.session_state.selected_donation_id
                                st.rerun()
                            except Exception as e:
                                st.error(f"Cannot cancel donation: {e}")
                    else:
                        st.caption(f"Donation is in '{curr_status}' status and can no longer be deleted.")

                with col_b2:
                    if st.button("Back to My Donations", width="stretch"):
                        del st.session_state.selected_donation_id
                        st.session_state.donor_page = "History"
                        st.rerun()

    # =========================================================
    # Make a Donation
    # =========================================================

    elif page == "Donate":
        st.title("Make a Food Donation")
        st.info("Thank you for supporting our community! Please select the food items and quantity you would like to donate.")

        stations = manager.get_stations()
        if not stations:
            st.warning("No dropoff stations are registered currently. Please contact the FoodBank administrator.")
            if st.button("Back to My Donations"):
                st.session_state.donor_page = "History"
                st.rerun()
        else:
            station_options = {}
            for s in stations:
                station_options[f"ID: {s.get('id')} - {s.get('name')} ({s.get('address', '')})"] = s.get("id")

            selected_station_label = st.selectbox("Select Dropoff / Pickup Station", list(station_options.keys()))
            selected_station_id = station_options[selected_station_label]

            description = st.text_area("Donation Notes / Pickup Instructions (Optional)", placeholder="e.g. Left at front reception / Best before Dec 2027")

            st.subheader("Select Items to Donate")
            available_items = [item.name for item in manager.get_inventory_items()]
            chosen_items = st.multiselect("Items to Donate", available_items)

            items_list = []
            if chosen_items:
                for it_name in chosen_items:
                    inv_obj = manager.inventory.find_item_by_name(it_name)
                    unit_str = getattr(inv_obj, "unit", "pcs") if inv_obj else "pcs"
                    qty = st.number_input(
                        f"Quantity for {it_name} ({unit_str})",
                        min_value=1.0,
                        step=1.0,
                        value=1.0,
                        key=f"donor_input_{it_name}"
                    )
                    items_list.append({"name": it_name, "quantity": qty})

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Submit Donation", width="stretch"):
                    if not items_list:
                        st.error("Please select at least one item to donate.")
                    else:
                        try:
                            don = manager.add_donation(
                                user.id,
                                description=description.strip(),
                                items=items_list,
                                station=selected_station_id
                            )
                            st.session_state.donor_page = "Donation Success"
                            st.session_state.donor_success_msg = f"Thank you! Your donation #{don.id} has been submitted successfully."
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to submit donation: {e}")

            with col2:
                if st.button("Cancel", width="stretch"):
                    st.session_state.donor_page = "History"
                    st.rerun()

    elif page == "Donation Success":
        success_page(
            "Donation Submitted",
            "Your donation has been processed successfully!",
            st.session_state.get("donor_success_msg", "Thank you for your generous contribution."),
            "History"
        )

    # =========================================================
    # Donor Profile
    # =========================================================

    elif page == "Profile":
        st.title("My Donor Profile")

        col_img, col_info = st.columns([1, 3])
        with col_img:
            st.image(avatar_path if "avatar_path" in locals() else (user.profile_image if getattr(user, "profile_image", None) and os.path.exists(user.profile_image) else "assets/default_avatar.png"), width=150)
        with col_info:
            st.subheader(f"Name: {user.name}")
            st.write(f"**Donor ID:** {user.id}")
            st.write(f"**Email:** {user.email}")
            st.write(f"**Role:** Donor")
            my_don_count = len([d for d in manager.donations if str(d.donor_id) == str(user.id)])
            st.write(f"**Total Donations Made:** {my_don_count}")

        st.divider()
        if st.button("Update Profile", width="stretch"):
            st.session_state.donor_page = "Update Profile"
            st.rerun()

    # =========================================================
    # Update Donor Profile
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
                    st.session_state.donor_page = "Profile Update Success"
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
                    st.session_state.donor_page = "Profile Update Success"
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
                    st.session_state.donor_page = "Profile Update Success"
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
                        st.session_state.donor_page = "Profile Update Success"
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to save uploaded image: {e}")

        st.divider()
        if st.button("Back to Profile"):
            st.session_state.donor_page = "Profile"
            st.rerun()

    elif page == "Profile Update Success":
        success_page(
            "Profile Updated",
            "Your profile has been updated successfully!",
            "Your profile changes have been saved.",
            "Profile"
        )


# Functional alias
donor_page = show_donor_page
