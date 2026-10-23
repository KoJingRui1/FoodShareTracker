import os
import streamlit as st
import pandas as pd
import datetime
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
        st.session_state.client_page = return_page
        if "selected_hamper_id" in st.session_state:
            del st.session_state.selected_hamper_id
        st.rerun()


# =========================================================
# Client Portal Main Page
# =========================================================

def show_client_page(manager, user):
    """Render the client assistance portal with hampers tracking, requesting, messaging, and profile."""
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
    st.sidebar.caption("Client (Beneficiary)")
    st.sidebar.divider()

    if "client_page" not in st.session_state:
        st.session_state.client_page = "My Hampers"

    if st.sidebar.button("My Hampers", width="stretch"):
        st.session_state.client_page = "My Hampers"

    if st.sidebar.button("Request Food Assistance", width="stretch"):
        st.session_state.client_page = "Request Hamper"

    if st.sidebar.button("Messages & Support", width="stretch"):
        st.session_state.client_page = "Messages"

    if st.sidebar.button("Profile & Allergies", width="stretch"):
        st.session_state.client_page = "Profile"

    st.sidebar.divider()
    if st.sidebar.button("Logout", width="stretch"):
        st.session_state.user = None
        st.session_state.current_page = "main"
        st.rerun()

    page = st.session_state.client_page

    # =========================================================
    # My Hampers (Tracking & Confirm Delivery)
    # =========================================================

    if page == "My Hampers":
        st.title("My Food Assistance Hampers")
        st.info("Track the status of your food assistance packages. When a hamper is delivered to your door by a volunteer, please confirm receipt below.")

        user_id_str = str(user.id)
        my_hampers = [h for h in manager.food_hampers if str(h.client_id) == user_id_str]

        # Top summary metrics
        total_hampers = len(my_hampers)
        received_hampers = sum(1 for h in my_hampers if str(h.status[0] if isinstance(h.status, list) and h.status else (h.status or "")).lower() == "delivered")
        active_hampers = total_hampers - received_hampers

        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Total Requested", total_hampers)
        with m2:
            st.metric("Active / In Transit", active_hampers)
        with m3:
            st.metric("Successfully Received", received_hampers)

        st.divider()

        # Status filter
        col_f1, col_f2 = st.columns([1, 3])
        with col_f1:
            status_filter = st.selectbox("Filter by Status", ["All", "created", "assigned", "packed", "delivered", "flagged"])

        filtered_hampers = []
        for h in my_hampers:
            curr_status = h.status[0] if isinstance(h.status, list) and h.status else (h.status or "created")
            if status_filter != "All" and str(curr_status).lower() != status_filter.lower():
                continue

            vol_obj = manager.find_volunteer_by_id(h.volunteer_id) if h.volunteer_id else None
            vol_name = vol_obj.name if vol_obj else "Pending assignment"

            items_count = len(getattr(h, "items", []))
            last_time = h.status_history[-1]["timestamp"] if getattr(h, "status_history", None) else "N/A"

            filtered_hampers.append({
                "ID": h.id,
                "Status": str(curr_status).upper(),
                "Assigned Volunteer": vol_name,
                "Items Count": items_count,
                "Delivery Address": getattr(user, "address", "On file"),
                "Last Updated": last_time,
                "Select": False
            })

        if not filtered_hampers:
            if not my_hampers:
                st.info("You do not have any active or past food hampers. Click 'Request Food Assistance' if you need food support!")
            else:
                st.info(f"No food hampers found with status '{status_filter}'.")
        else:
            for item in filtered_hampers:
                target_id = item["ID"]
                with st.container(border=True):
                    h_col1, h_col2 = st.columns([3, 1])
                    with h_col1:
                        st.markdown(f"#### 🍲 Food Hamper #{target_id}")
                    with h_col2:
                        st.markdown(f"**Status:** `{item['Status']}`")

                    d_col1, d_col2 = st.columns(2)
                    with d_col1:
                        st.write(f"🚚 **Volunteer:** {item['Assigned Volunteer']}")
                        st.write(f"📍 **Address:** {item['Delivery Address']}")
                    with d_col2:
                        st.write(f"📦 **Items:** {item['Items Count']} item(s)")
                        st.write(f"🕒 **Last Updated:** {item['Last Updated']}")

                    act_c1, act_c2 = st.columns(2)
                    with act_c1:
                        if st.button("🔍 View Details & Confirm Receipt", key=f"btn_hmp_det_{target_id}", width="stretch"):
                            st.session_state.selected_hamper_id = target_id
                            st.session_state.client_page = "Hamper Detail"
                            st.rerun()
                    with act_c2:
                        if item["Status"].lower() == "created":
                            if st.button("❌ Cancel Request", key=f"btn_hmp_del_{target_id}", width="stretch"):
                                try:
                                    manager.delete_food_hamper(target_id)
                                    st.success(f"Food hamper request #{target_id} has been cancelled.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Cannot cancel request: {e}")
                        else:
                            st.caption("🔒 Status locked (assigned / packed / delivered)")

        st.divider()
        if st.button("Submit New Assistance Request", width="stretch"):
            st.session_state.client_page = "Request Hamper"
            st.rerun()

    # =========================================================
    # Hamper Detail & Delivery Confirmation
    # =========================================================

    elif page == "Hamper Detail":
        if "selected_hamper_id" not in st.session_state:
            st.error("No hamper selected.")
            if st.button("Back to My Hampers"):
                st.session_state.client_page = "My Hampers"
                st.rerun()
        else:
            hamper_id = st.session_state.selected_hamper_id
            target_hamper = manager.find_food_hamper_by_id(hamper_id)

            if target_hamper is None or str(target_hamper.client_id) != str(user.id):
                st.error("Hamper record not found or access denied.")
                if st.button("Back to My Hampers"):
                    del st.session_state.selected_hamper_id
                    st.session_state.client_page = "My Hampers"
                    st.rerun()
            else:
                st.title(f"Food Hamper Package #{target_hamper.id}")
                curr_status = target_hamper.status[0] if isinstance(target_hamper.status, list) and target_hamper.status else (target_hamper.status or "created")

                # Status Progression Banners
                if str(curr_status).lower() == "created":
                    st.info("📌 **Status: CREATED.** Your request has been registered and is awaiting preparation by the FoodBank warehouse.")
                elif str(curr_status).lower() == "assigned":
                    st.info("🚚 **Status: ASSIGNED.** A volunteer has been assigned to your delivery. Warehouse staff is preparing and packing your package.")
                elif str(curr_status).lower() == "packed":
                    st.success("📦 **Status: PACKED & OUT FOR DELIVERY!** Your hamper has been packed and is with the volunteer for delivery.")
                elif str(curr_status).lower() == "delivered":
                    st.success("🎉 **Status: DELIVERED.** You have confirmed receipt of this food hamper package. Enjoy your meals!")

                # Confirmation Box ONLY when packed
                if str(curr_status).lower() == "packed":
                    st.markdown("---")
                    st.subheader("📬 Confirm Delivery Handover")
                    st.info("Has the volunteer arrived and handed you this food hamper package?")
                    if st.button("✅ Confirm Food Hamper Received", width="stretch"):
                        try:
                            manager.deliver_food_hamper(target_hamper.id)
                            if not hasattr(user, "receive") or not isinstance(user.receive, list):
                                user.receive = []
                            if target_hamper.id not in user.receive:
                                user.receive.append(target_hamper.id)
                            manager._save_data()
                            st.success(f"Delivery confirmed! Food Hamper #{target_hamper.id} marked as DELIVERED.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Cannot confirm delivery: {e}")
                    st.markdown("---")

                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("Hamper ID", f"#{target_hamper.id}")
                with c2:
                    st.metric("Current Status", str(curr_status).upper())
                with c3:
                    st.metric("Items Count", f"{len(target_hamper.items)} item type(s)")

                st.divider()

                # Assigned Volunteer Contact
                vol_obj = manager.find_volunteer_by_id(target_hamper.volunteer_id) if target_hamper.volunteer_id else None
                vol_name = vol_obj.name if vol_obj else "Not assigned yet"
                vol_email = getattr(vol_obj, "email", "N/A") if vol_obj else "N/A"

                col_left, col_right = st.columns(2)
                with col_left:
                    st.subheader("Delivery Address & Notes")
                    st.write(f"**Delivery Address:** {getattr(user, 'address', '') or 'Address on file'}")
                    st.write(f"**Special Instructions:** {target_hamper.description or 'None'}")

                with col_right:
                    st.subheader("Delivery Volunteer Contact")
                    st.write(f"**Assigned Volunteer:** {vol_name}")
                    st.write(f"**Volunteer Contact Email:** {vol_email}")
                    last_time = target_hamper.status_history[-1]["timestamp"] if getattr(target_hamper, "status_history", None) else "N/A"
                    st.write(f"**Last Status Updated:** {last_time}")

                st.subheader("Food Items in Package")
                if not target_hamper.items:
                    st.info("No items listed in this package.")
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

                # Report Issue with package
                st.subheader("Report an Issue with this Package")
                st.caption("If any item was missing, damaged, or contained unexpected allergens, report it to our team immediately.")
                issue_text = st.text_input("Describe the issue", placeholder="e.g. Box arrived open / Allergen item detected", key=f"cl_issue_{target_hamper.id}")
                if st.button("Submit Issue Report", key=f"btn_flag_cl_{target_hamper.id}"):
                    if not issue_text.strip():
                        st.error("Please enter a description of the issue.")
                    else:
                        try:
                            manager.flag_issue("hamper", target_hamper.id, issue_text.strip())
                            st.success("Issue submitted successfully. Our team will review it.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to submit issue: {e}")

                st.write("")
                if st.button("Back to My Hampers"):
                    del st.session_state.selected_hamper_id
                    st.session_state.client_page = "My Hampers"
                    st.rerun()

    # =========================================================
    # Request Food Assistance (Submit Hamper Request)
    # =========================================================

    elif page == "Request Hamper":
        st.title("Request Food Assistance")
        st.info("FoodBank is committed to providing nutritious meals for you and your family. Select the food items and quantity you need.")

        # Show recorded allergies for dietary safety
        client_allergies = getattr(user, "allergy", [])
        if isinstance(client_allergies, list) and client_allergies:
            allergy_str = ", ".join([str(a) for a in client_allergies])
            st.warning(f"🛡️ **Dietary Safety Note:** Your profile lists allergies to: **{allergy_str}**. Our packing team will strictly avoid these allergens.")
        elif isinstance(client_allergies, str) and client_allergies.strip():
            st.warning(f"🛡️ **Dietary Safety Note:** Your profile lists allergies to: **{client_allergies.strip()}**.")

        # Delivery Address confirmation
        current_addr = getattr(user, "address", "") or ""
        delivery_address = st.text_input("Confirm Your Delivery Address", value=current_addr, placeholder="e.g. 123 Hope St, Apartment 4B")

        description = st.text_area("Family Size / Dietary Notes / Special Requests", placeholder="e.g. Family of 4, two young children. Prefer canned beans and rice.")

        st.subheader("Select Desired Food Items")
        available_items = [item.name for item in manager.get_inventory_items()]
        chosen_items = st.multiselect("Requested Items", available_items)

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
                    key=f"client_req_{it_name}"
                )
                items_list.append({"name": it_name, "quantity": qty})

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Submit Assistance Request", width="stretch"):
                if not delivery_address.strip():
                    st.error("Please provide a valid delivery address so our volunteer can reach you.")
                elif not items_list:
                    st.error("Please select at least one food item.")
                else:
                    try:
                        # Update address on client user if changed
                        if delivery_address.strip() != current_addr:
                            manager.update_user(user.id, address=delivery_address.strip())
                            user.address = delivery_address.strip()

                        hamper = manager.add_food_hamper(
                            client_id=user.id,
                            description=description.strip(),
                            items=items_list
                        )
                        st.session_state.client_page = "Request Success"
                        st.session_state.client_success_msg = f"Your food assistance request #{hamper.id} has been received. Our team will prepare your hamper promptly."
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to submit request: {e}")

        with col2:
            if st.button("Cancel", width="stretch"):
                st.session_state.client_page = "My Hampers"
                st.rerun()

    elif page == "Request Success":
        success_page(
            "Request Submitted",
            "Your assistance request has been received!",
            st.session_state.get("client_success_msg", "FoodBank is processing your request."),
            "My Hampers"
        )

    # =========================================================
    # Client Messages & Support
    # =========================================================

    elif page == "Messages":
        st.title("FoodBank Support Messages")
        st.info("Communicate directly with FoodBank staff regarding your assistance, delivery schedule, or inquiries.")

        # Send new message
        st.subheader("Send a Message to FoodBank")
        msg_input = st.text_area("Message Content", placeholder="Write your question, scheduling update, or feedback here...")
        if st.button("Send Message", width="stretch"):
            if not msg_input.strip():
                st.error("Message content cannot be empty.")
            else:
                try:
                    manager.send_client_message(user.id, msg_input.strip())
                    st.success("Message sent successfully to FoodBank staff.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to send message: {e}")

        st.divider()

        # Display Message History
        st.subheader("My Message History")
        client_msgs = manager.get_client_messages(user.id)
        if not client_msgs:
            st.info("No messages sent yet.")
        else:
            # Display reverse chronological
            for msg in reversed(client_msgs):
                msg_id = msg.get("id")
                timestamp = msg.get("timestamp")
                content = msg.get("content")
                is_edited = msg.get("is_edited", False)
                tag = " *(edited)*" if is_edited else ""

                with st.expander(f"✉️ Message #{msg_id} - {timestamp}{tag}", expanded=False):
                    st.write(content)

                    # Edit form inside expander
                    new_edit_text = st.text_input("Edit message content", value=content, key=f"edit_msg_{msg_id}")
                    col_e1, col_e2 = st.columns(2)
                    with col_e1:
                        if st.button("Save Changes", key=f"btn_save_msg_{msg_id}", width="stretch"):
                            if not new_edit_text.strip():
                                st.error("Content cannot be empty.")
                            else:
                                try:
                                    manager.edit_client_message(user.id, msg_id, new_edit_text.strip())
                                    st.success("Message updated.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Cannot edit message: {e}")
                    with col_e2:
                        if st.button("Delete Message", key=f"btn_del_msg_{msg_id}", width="stretch"):
                            try:
                                manager.delete_client_message(user.id, msg_id)
                                st.success("Message deleted.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Cannot delete message: {e}")

    # =========================================================
    # Client Profile & Allergies
    # =========================================================

    elif page == "Profile":
        st.title("My Client Profile & Dietary Information")

        col_img, col_info = st.columns([1, 3])
        with col_img:
            st.image(avatar_path if "avatar_path" in locals() else (user.profile_image if getattr(user, "profile_image", None) and os.path.exists(user.profile_image) else "assets/default_avatar.png"), width=150)
        with col_info:
            st.subheader(f"Name: {user.name}")
            st.write(f"**Client ID:** {user.id}")
            st.write(f"**Email:** {user.email}")
            st.write(f"**Delivery Address:** {getattr(user, 'address', '') or 'Not set'}")
            
            client_allg = getattr(user, "allergy", [])
            allg_str = ", ".join(client_allg) if isinstance(client_allg, list) and client_allg else (str(client_allg) if client_allg else "None recorded")
            st.write(f"**Recorded Allergies:** {allg_str}")
            st.write(f"**Personal / Family Notes:** {getattr(user, 'description', '') or 'None'}")
            received_count = len(getattr(user, "receive", []))
            st.write(f"**Total Hampers Received:** {received_count}")

        st.divider()
        if st.button("Update Profile & Allergies", width="stretch"):
            st.session_state.client_page = "Update Profile"
            st.rerun()

    # =========================================================
    # Update Client Profile
    # =========================================================

    elif page == "Update Profile":
        st.title("Update My Profile & Allergies")
        choice = st.selectbox(
            "Update Term",
            ["Name", "Password", "Email", "Delivery Address", "Allergies & Dietary Restrictions", "Personal Description", "Profile Image"]
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
                    st.session_state.client_page = "Profile Update Success"
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
                    st.session_state.client_page = "Profile Update Success"
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
                    st.session_state.client_page = "Profile Update Success"
                    st.rerun()

        elif choice == "Delivery Address":
            curr_addr = getattr(user, "address", "") or ""
            new_addr = st.text_input("Delivery Address", value=curr_addr, placeholder="e.g. 123 Hope St, Apartment 4B")
            if st.button("Update Delivery Address"):
                if not new_addr.strip():
                    st.error("Address cannot be empty.")
                else:
                    manager.update_user(user.id, address=new_addr.strip())
                    user.address = new_addr.strip()
                    st.session_state.client_page = "Profile Update Success"
                    st.rerun()

        elif choice == "Allergies & Dietary Restrictions":
            curr_allg = getattr(user, "allergy", [])
            curr_allg_str = ", ".join(curr_allg) if isinstance(curr_allg, list) else str(curr_allg)
            st.info("Specify any food allergies (e.g. Peanuts, Gluten, Dairy, Seafood) so hampers never include items you cannot safely consume.")
            new_allg_str = st.text_input("Allergies (comma-separated)", value=curr_allg_str, placeholder="e.g. Peanuts, Seafood, Gluten")
            if st.button("Update Allergies"):
                parsed = [a.strip() for a in new_allg_str.split(",") if a.strip()]
                manager.update_user(user.id, allergy=parsed)
                user.allergy = parsed
                st.session_state.client_page = "Profile Update Success"
                st.rerun()

        elif choice == "Personal Description":
            curr_desc = getattr(user, "description", "") or ""
            new_desc = st.text_area("Personal / Family Description", value=curr_desc, placeholder="e.g. Family of 4, two children. Special dietary preferences.")
            if st.button("Update Description"):
                manager.update_user(user.id, description=new_desc.strip())
                user.description = new_desc.strip()
                st.session_state.client_page = "Profile Update Success"
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
                        st.session_state.client_page = "Profile Update Success"
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to save uploaded image: {e}")

        st.divider()
        if st.button("Back to Profile"):
            st.session_state.client_page = "Profile"
            st.rerun()

    elif page == "Profile Update Success":
        success_page(
            "Profile Updated",
            "Your profile and dietary preferences have been updated!",
            "Your updated information has been saved.",
            "Profile"
        )
