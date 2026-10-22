# Store Food Bank data in a JSON file.
import json
import datetime
import logging
import csv
from pathlib import Path

try:
    from src.app.admin import AdminUser
    from src.app.client import ClientUser
    from src.app.donations import Donation
    from src.app.donor import DonorUser
    from src.app.FoodHamper import FoodHamper
    from src.app.staff import StaffUser
    from src.app.volunteer import VolunteerUser
    from src.app.inventory import Inventory
    from src.app.item import Item
    from src.app.utils import (
        valid_name, valid_password, validate_name, validate_password,
        hash_password, verify_password, is_bcrypt_hash
    )
except ModuleNotFoundError:
    from app.admin import AdminUser
    from app.client import ClientUser
    from app.donations import Donation
    from app.donor import DonorUser
    from app.FoodHamper import FoodHamper
    from app.staff import StaffUser
    from app.volunteer import VolunteerUser
    from app.inventory import Inventory
    from app.item import Item
    from app.utils import (
        valid_name, valid_password, validate_name, validate_password,
        hash_password, verify_password, is_bcrypt_hash
    )


class FoodBank:
    """Main controller for Food Bank business logic and JSON persistence."""

    USER_MODELS = {
        "admins": AdminUser,
        "donors": DonorUser,
        "staffs": StaffUser,
        "volunteers": VolunteerUser,
        "clients": ClientUser,
    }

    @staticmethod
    def valid_name(name, **kwargs):
        """Helper to validate a user or entity name."""
        return valid_name(name, **kwargs)

    @staticmethod
    def valid_password(password, **kwargs):
        """Helper to validate a user password."""
        return valid_password(password, **kwargs)

    @staticmethod
    def validate_name(name, **kwargs):
        """Helper to validate name returning (is_valid, reason)."""
        return validate_name(name, **kwargs)

    @staticmethod
    def validate_password(password, **kwargs):
        """Helper to validate password returning (is_valid, reason)."""
        return validate_password(password, **kwargs)

    @staticmethod
    def hash_password(password):
        """Helper to hash password with bcrypt."""
        return hash_password(password)

    @staticmethod
    def verify_password(password, hashed_password):
        """Helper to verify password against bcrypt hash."""
        return verify_password(password, hashed_password)

    @staticmethod
    def is_bcrypt_hash(stored_hash):
        """Helper to check if string is bcrypt hash."""
        return is_bcrypt_hash(stored_hash)

    @staticmethod
    def _update_status(entity, new_status):
        """Updates entity status and records entry in status_history."""
        entity.status = new_status
        if not hasattr(entity, "status_history") or not isinstance(entity.status_history, list):
            entity.status_history = []
        entity.status_history.append({
            "status": new_status,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    def __init__(self, data_path=None):
        # Default path: <project root>/src/data/data.json.
        project_root = Path(__file__).resolve().parent
        if project_root.name == "app" and project_root.parent.name == "src":
            project_root = project_root.parent.parent
        elif project_root.name == "src":
            project_root = project_root.parent
        self.data_path = Path(data_path) if data_path is not None else project_root / "src" / "data" / "data.json"

        # Initialize collections and counters to a clean empty state.
        self._init_empty_state()

        # Load saved data from disk if present.
        self._load_data()

    def _init_empty_state(self):
        """Initializes empty in-memory collections and system counters."""
        self.admins = []
        self.donors = []
        self.staffs = []
        self.volunteers = []
        self.clients = []
        self.donations = []
        self.food_hampers = []
        self.inventory = Inventory()
        self.address = ""
        self.description = ""
        self.collection_centers = []
        self.applications = []
        self.food_bank_data = {
            "next_user_id": 1,
            "next_donation_id": 1,
            "next_food_hamper_id": 1,
            "next_application_id": 1,
            "address": "",
            "description": "",
            "collection_centers": [],
        }

    def _load_data(self):
        """Load JSON data and recreate each object, handling missing or corrupted files safely."""
        try:
            with self.data_path.open("r", encoding="utf-8") as file:
                data = json.load(file)

            if not isinstance(data, dict):
                print("Invalid data format in JSON file. Starting with a clean state.")
                self._init_empty_state()
                return

            # Rebuild collections from loaded JSON.
            self.admins = []
            self.donors = []
            self.staffs = []
            self.volunteers = []
            self.clients = []
            self.donations = []
            self.food_hampers = []

            for admin_data in data.get("admins", []):
                admin = AdminUser(
                    admin_data["id"], admin_data["name"],
                    admin_data["password"], admin_data["email"],
                    profile_image=admin_data.get("profile_image", "assets/default_avatar.png")
                )
                self.admins.append(admin)

            for donor_data in data.get("donors", []):
                donor = DonorUser(
                    donor_data["id"], donor_data["name"],
                    donor_data["password"], donor_data["email"],
                    profile_image=donor_data.get("profile_image", "assets/default_avatar.png")
                )
                donor.donation = donor_data.get("donation", [])
                self.donors.append(donor)

            for staff_data in data.get("staffs", []):
                staff = StaffUser(
                    staff_data["id"], staff_data["name"],
                    staff_data["password"], staff_data["email"],
                    profile_image=staff_data.get("profile_image", "assets/default_avatar.png")
                )
                self.staffs.append(staff)

            for volunteer_data in data.get("volunteers", []):
                volunteer = VolunteerUser(
                    volunteer_data["id"], volunteer_data["name"],
                    volunteer_data["password"], volunteer_data["email"],
                    profile_image=volunteer_data.get("profile_image", "assets/default_avatar.png")
                )
                volunteer.work = volunteer_data.get("work", [])
                volunteer.completed_work = volunteer_data.get("completed_work", [])
                self.volunteers.append(volunteer)

            for client_data in data.get("clients", []):
                raw_address = client_data.get("address", "")
                if isinstance(raw_address, list):
                    client_address = str(raw_address[0]).strip() if raw_address and str(raw_address[0]).strip() else ""
                elif raw_address is None:
                    client_address = ""
                else:
                    client_address = str(raw_address).strip()

                client = ClientUser(
                    client_data["id"], client_data["name"],
                    client_data["password"], client_data["email"],
                    description=client_data.get("description", ""),
                    address=client_address,
                    profile_image=client_data.get("profile_image", "assets/default_avatar.png")
                )
                client.allergy = client_data.get("allergy", [])
                client.address = client_address
                client.receive = client_data.get("receive", [])
                client.messages = client_data.get("messages", [])
                self.clients.append(client)

            for donation_data in data.get("donations", []):
                raw_status = donation_data.get("status", "created")
                status = raw_status[0] if isinstance(raw_status, list) and raw_status else (raw_status or "created")
                donation = Donation(
                    donation_data["id"], donation_data.get("donor_id"),
                    donation_data["description"], status=status,
                    volunteer_id=donation_data.get("volunteer_id"),
                    station=donation_data.get("station")
                )
                donation.items = donation_data.get("items", [])
                donation.flagged_issue = donation_data.get("flagged_issue", None)
                donation.previous_status = donation_data.get("previous_status", None)
                donation.issue_history = donation_data.get("issue_history", [])
                donation.status_history = donation_data.get("status_history", [])
                self.donations.append(donation)

            for hamper_data in data.get("food_hampers", []):
                raw_status = hamper_data.get("status", "created")
                status = raw_status[0] if isinstance(raw_status, list) and hamper_data else (raw_status or "created")
                hamper = FoodHamper(
                    hamper_data["id"], hamper_data.get("client_id"),
                    hamper_data["description"], status=status,
                    volunteer_id=hamper_data.get("volunteer_id")
                )
                hamper.items = hamper_data.get("items", [])
                hamper.flagged_issue = hamper_data.get("flagged_issue", None)
                hamper.previous_status = hamper_data.get("previous_status", None)
                hamper.issue_history = hamper_data.get("issue_history", [])
                hamper.status_history = hamper_data.get("status_history", [])
                self.food_hampers.append(hamper)

            self.food_bank_data = data.get("food_bank_data", {
                "next_user_id": 1,
                "next_donation_id": 1,
                "next_food_hamper_id": 1,
            })
            self.address = data.get("address") or self.food_bank_data.get("address", "")
            self.description = data.get("description") or self.food_bank_data.get("description", "")
            raw_centers = data.get("collection_centers") or self.food_bank_data.get("collection_centers", [])
            self.collection_centers = []
            max_station_id = 0
            if isinstance(raw_centers, list):
                for idx, c in enumerate(raw_centers, start=1):
                    if isinstance(c, dict):
                        sid = c.get("id") or idx
                        max_station_id = max(max_station_id, int(sid))
                        self.collection_centers.append({
                            "id": int(sid),
                            "name": str(c.get("name", "")),
                            "address": str(c.get("address", ""))
                        })
                    elif isinstance(c, str):
                        max_station_id = max(max_station_id, idx)
                        self.collection_centers.append({"id": idx, "name": c, "address": ""})
            if "next_station_id" not in self.food_bank_data:
                self.food_bank_data["next_station_id"] = max_station_id + 1
            self.food_bank_data["address"] = self.address
            self.food_bank_data["description"] = self.description
            self.food_bank_data["collection_centers"] = self.collection_centers

            # Load volunteer applications
            raw_apps = data.get("applications", [])
            self.applications = raw_apps if isinstance(raw_apps, list) else []

            # Load inventory data safely inside try block (handles both list and dict formats).
            raw_inventory = data.get("inventory", {})
            self.inventory = Inventory()
            self.inventory.items = []

            if isinstance(raw_inventory, list):
                items_list = raw_inventory
                records_list = data.get("inventory_transactions", [])
                inv_metadata = {"next_item_id": 1, "next_record_id": 1}
            elif isinstance(raw_inventory, dict):
                items_list = raw_inventory.get("items", [])
                records_list = raw_inventory.get("stock_records", [])
                inv_metadata = raw_inventory.get("inventory_data", {"next_item_id": 1, "next_record_id": 1})
            else:
                items_list = []
                records_list = []
                inv_metadata = {"next_item_id": 1, "next_record_id": 1}

            for item_data in items_list:
                item = Item(
                    item_data["id"],
                    item_data["name"],
                    item_data["category"],
                    item_data.get("quantity", 0),
                    item_data.get("unit", "pcs"),
                    item_data.get("min_quantity", 0)
                )
                self.inventory.items.append(item)

            self.inventory.stock_records = records_list
            self.inventory.inventory_data = inv_metadata

        except (FileNotFoundError, json.JSONDecodeError):
            print("Data file not found or corrupted. Starting with a clean state.")
            self._init_empty_state()

    def _save_data(self):
        """Save the collections and system counters as JSON, like ScheduleManager."""
        self.food_bank_data["address"] = self.address
        self.food_bank_data["description"] = self.description
        self.food_bank_data["collection_centers"] = self.collection_centers
        data_to_save = {
            "address": self.address,
            "description": self.description,
            "collection_centers": self.collection_centers,
            "applications": self.applications,
            "admins": [admin.__dict__ for admin in self.admins],
            "donors": [donor.__dict__ for donor in self.donors],
            "staffs": [staff.__dict__ for staff in self.staffs],
            "volunteers": [volunteer.__dict__ for volunteer in self.volunteers],
            "clients": [client.__dict__ for client in self.clients],
            "donations": [donation.__dict__ for donation in self.donations],
            "food_hampers": [hamper.__dict__ for hamper in self.food_hampers],
            "food_bank_data": self.food_bank_data,
            "inventory": {
            "items": [
                item.__dict__ for item in self.inventory.items
            ],
            "stock_records": self.inventory.stock_records,
            "inventory_data": self.inventory.inventory_data
            },
        }
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        with self.data_path.open("w", encoding="utf-8") as file:
            json.dump(data_to_save, file, indent=4, ensure_ascii=False)
        logging.info(f"Saved system data to JSON file: {self.data_path}")

    def save_data(self):
        self._save_data()

    def load_data(self):
        self._load_data()

    # Find objects by ID, following ScheduleManager's explicit lookup style.
    @staticmethod
    def _find_by_id(collection, object_id):
        for obj in collection:
            if str(obj.id) == str(object_id):
                return obj
        return None

    def find_admin_by_id(self, user_id): 
        return self._find_by_id(self.admins, user_id)
    def find_donor_by_id(self, user_id): 
        return self._find_by_id(self.donors, user_id)
    def find_staff_by_id(self, user_id): 
        return self._find_by_id(self.staffs, user_id)
    def find_volunteer_by_id(self, user_id): 
        return self._find_by_id(self.volunteers, user_id)
    def find_client_by_id(self, user_id): 
        return self._find_by_id(self.clients, user_id)
    def find_donation_by_id(self, donation_id): 
        return self._find_by_id(self.donations, donation_id)
    def find_food_hamper_by_id(self, hamper_id): 
        return self._find_by_id(self.food_hampers, hamper_id)

    def find_user_by_id(self, user_id):
        for collection_name in self.USER_MODELS:
            result = self._find_by_id(getattr(self, collection_name), user_id)
            if result is not None:
                return result
        return None

    def find_user_by_email(self, email):
        """Finds any user across all user collections matching the email address (case-insensitive)."""
        if not email:
            return None
        target_email = email.strip().lower()
        for collection_name in self.USER_MODELS:
            collection = getattr(self, collection_name)
            for user in collection:
                if hasattr(user, "email") and user.email and user.email.strip().lower() == target_email:
                    return user
        return None

    def authenticate(self, email, password):
        """Authenticates user credentials using bcrypt and returns (user, role_name) or None."""
        user = self.find_user_by_email(email)
        if user is None or not password or not hasattr(user, "password"):
            return None
        if verify_password(password, user.password):
            # Auto-upgrade plain-text password to bcrypt hash upon successful login
            if not is_bcrypt_hash(user.password):
                user.password = hash_password(password)
                self._save_data()
            for role_name, model in self.USER_MODELS.items():
                if isinstance(user, model):
                    return user, role_name
        return None

    def _add_user(self, model, collection, name, password, email, profile_image="assets/default_avatar.png"):
        if self.find_user_by_email(email) is not None:
            raise ValueError(f"Email '{email}' is already registered.")
        hashed_password = hash_password(password) if not is_bcrypt_hash(password) else password
        user = model(self.food_bank_data["next_user_id"], name, hashed_password, email, profile_image=profile_image)
        collection.append(user)
        self.food_bank_data["next_user_id"] += 1
        logging.info(f"Added user: {user.name} (Role: {model.__name__}, ID: {user.id}, Email: {user.email})")
        self._save_data()
        return user

    def add_admin(self, name, password, email, profile_image="assets/default_avatar.png"): 
        return self._add_user(AdminUser, self.admins, name, password, email, profile_image=profile_image)
    def add_donor(self, name, password, email, profile_image="assets/default_avatar.png"): 
        return self._add_user(DonorUser, self.donors, name, password, email, profile_image=profile_image)
    def add_staff(self, name, password, email, profile_image="assets/default_avatar.png"): 
        return self._add_user(StaffUser, self.staffs, name, password, email, profile_image=profile_image)
    def add_volunteer(self, name, password, email, profile_image="assets/default_avatar.png"): 
        return self._add_user(VolunteerUser, self.volunteers, name, password, email, profile_image=profile_image)
    def add_client(self, name, password, email, description="", address="", profile_image="assets/default_avatar.png"): 
        if self.find_user_by_email(email) is not None:
            raise ValueError(f"Email '{email}' is already registered.")
        hashed_password = hash_password(password) if not is_bcrypt_hash(password) else password
        user = ClientUser(
            self.food_bank_data["next_user_id"],
            name,
            hashed_password,
            email,
            description=description,
            address=address,
            profile_image=profile_image
        )
        self.clients.append(user)
        self.food_bank_data["next_user_id"] += 1
        logging.info(f"Added client: {user.name} (ID: {user.id}, Email: {user.email})")
        self._save_data()
        return user

    # Volunteer Application management.
    @property
    def application(self):
        """Property alias for applications list."""
        return self.applications

    @application.setter
    def application(self, value):
        self.applications = value

    def find_application_by_id(self, application_id):
        """Finds an application by its ID."""
        for app in self.applications:
            if str(app.get("id")) == str(application_id):
                return app
        return None

    def apply_volunteer(self, name, password, email, description="", profile_image="assets/default_avatar.png"):
        """Submits an application to become a volunteer with a personal description and no initial jobs."""
        if not name or not str(name).strip():
            raise ValueError("Applicant name cannot be empty.")
        if not email or not str(email).strip():
            raise ValueError("Applicant email cannot be empty.")
        if self.find_user_by_email(email) is not None:
            raise ValueError(f"Email '{email}' is already registered.")

        for app in self.applications:
            if app.get("email", "").lower() == email.strip().lower() and app.get("status") == "pending":
                raise ValueError(f"An application for email '{email}' is already pending review.")

        hashed_password = hash_password(password) if not is_bcrypt_hash(password) else password
        app_id = self.food_bank_data.get("next_application_id", 1)
        application = {
            "id": app_id,
            "name": str(name).strip(),
            "password": hashed_password,
            "email": str(email).strip(),
            "description": str(description or "").strip(),
            "profile_image": profile_image,
            "status": "pending",
            "submitted_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.applications.append(application)
        self.food_bank_data["next_application_id"] = app_id + 1
        logging.info(f"Submitted volunteer application ID {app_id} for {name} ({email})")
        self._save_data()
        return application

    # Functional aliases for applying
    submit_volunteer_application = apply_volunteer
    add_volunteer_application = apply_volunteer
    add_application = apply_volunteer

    def approve_volunteer_application(self, application_id):
        """Approves a volunteer application and registers the applicant as a VolunteerUser with no initial jobs."""
        app = self.find_application_by_id(application_id)
        if app is None:
            raise ValueError(f"Application ID {application_id} does not exist.")

        if app.get("status") == "approved":
            raise ValueError(f"Application ID {application_id} has already been approved.")

        if self.find_user_by_email(app["email"]) is not None:
            raise ValueError(f"Email '{app['email']}' is already registered.")

        # Create new VolunteerUser without initial jobs
        volunteer = self.add_volunteer(
            name=app["name"],
            password=app["password"],
            email=app["email"],
            profile_image=app.get("profile_image", "assets/default_avatar.png")
        )

        app["status"] = "approved"
        app["approved_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        app["user_id"] = volunteer.id

        logging.info(f"Approved application ID {application_id}: Created volunteer {volunteer.name} (ID: {volunteer.id})")
        self._save_data()
        return volunteer

    # Functional alias for approving
    approve_application = approve_volunteer_application

    def delete_volunteer_application(self, application_id):
        """Deletes/removes a volunteer application from the system."""
        app = self.find_application_by_id(application_id)
        if app is None:
            return False
        self.applications.remove(app)
        logging.info(f"Deleted volunteer application ID {application_id}")
        self._save_data()
        return True

    # Functional aliases for deleting
    delete_application = delete_volunteer_application
    remove_application = delete_volunteer_application

    def get_applications(self, status=None):
        """Returns list of applications, optionally filtered by status ('pending', 'approved', etc.)."""
        if status is None:
            return self.applications
        clean_status = str(status).strip().lower()
        return [app for app in self.applications if app.get("status", "").lower() == clean_status]

    def get_pending_applications(self):
        """Returns list of all pending volunteer applications."""
        return self.get_applications(status="pending")

    def get_all_users(self):
        """Returns a combined list of all users across all role collections."""
        all_users = []
        for collection_name in self.USER_MODELS:
            all_users.extend(getattr(self, collection_name, []))
        return all_users

    def get_user_profile_image(self, user_id):
        """Returns the profile image path for the specified user, or default avatar if unset."""
        user = self.find_user_by_id(user_id)
        if user is None:
            return None
        return getattr(user, "profile_image", None) or "assets/default_avatar.png"

    def set_user_profile_image(self, user_id, profile_image):
        """Updates the profile image path for the specified user and saves to disk."""
        logging.info(f"Updated profile image for user ID {user_id} to '{profile_image}'")
        return self.update_user(user_id, profile_image=profile_image)

    def update_user_profile_image(self, user_id, profile_image):
        """Alias for set_user_profile_image."""
        return self.set_user_profile_image(user_id, profile_image)

    def add_user(self, user):
        collection = None
        for name, model in self.USER_MODELS.items():
            if isinstance(user, model):
                collection = getattr(self, name)
                break
        if collection is None:
            raise TypeError("Unsupported user type.")
        if self.find_user_by_id(user.id) is not None:
            raise ValueError(f"User ID {user.id} already exists.")
        existing_by_email = self.find_user_by_email(user.email)
        if existing_by_email is not None and str(existing_by_email.id) != str(user.id):
            raise ValueError(f"Email '{user.email}' is already registered.")
        if hasattr(user, "password") and user.password and not is_bcrypt_hash(user.password):
            user.password = hash_password(user.password)
        collection.append(user)
        try:
            self.food_bank_data["next_user_id"] = max(self.food_bank_data["next_user_id"], int(user.id) + 1)
        except (TypeError, ValueError):
            pass
        logging.info(f"Added user instance: {user.name} (ID: {user.id})")
        self._save_data()
        return user

    def remove_user(self, user_id):
        for collection_name in self.USER_MODELS:
            collection = getattr(self, collection_name)
            user = self._find_by_id(collection, user_id)
            if user is None:
                continue

            # Cascade deletion logic based on entity status:
            # 1. If Client is removed:
            #    - If hamper is in 'created' status: delete together with client;
            #    - If hamper is already 'assigned': cannot delete hamper; unbind client and reset to 'created' to return to available pool.
            if isinstance(user, ClientUser):
                retained_hampers = []
                for hamper in self.food_hampers:
                    if str(hamper.client_id) == str(user_id):
                        curr_status = hamper.status[0] if isinstance(hamper.status, list) and hamper.status else (hamper.status or "")
                        if str(curr_status).lower() == "created":
                            continue  # Delete created hamper together with client
                        else:
                            # Assigned or packed hamper cannot be deleted; unbind client
                            hamper.client_id = None
                            if str(curr_status).lower() == "assigned":
                                self._update_status(hamper, "created")
                            retained_hampers.append(hamper)
                    else:
                        retained_hampers.append(hamper)
                self.food_hampers = retained_hampers

            # 2. If Donor is removed:
            #    - 'created' status: delete donation together with donor;
            #    - 'collected' status: cannot delete donation; unbind donor to anonymous (None) to preserve records.
            if isinstance(user, DonorUser):
                retained_donations = []
                for donation in self.donations:
                    if str(donation.donor_id) == str(user_id):
                        curr_status = donation.status[0] if isinstance(donation.status, list) and donation.status else (donation.status or "")
                        if str(curr_status).lower() == "created":
                            continue  # Delete created donation together with donor
                        else:
                            # Collected donation cannot be deleted; retain anonymously
                            donation.donor_id = None
                            retained_donations.append(donation)
                    else:
                        retained_donations.append(donation)
                self.donations = retained_donations

            # 3. If Volunteer is removed: clear work records and unbind active uncompleted tasks
            if isinstance(user, VolunteerUser):
                user.work = []
                user.completed_work = []
                for hamper in self.food_hampers:
                    if str(hamper.volunteer_id) == str(user_id) and str(hamper.status).lower() != "delivered":
                        hamper.volunteer_id = None
                for donation in self.donations:
                    if str(donation.volunteer_id) == str(user_id):
                        donation.volunteer_id = None

            collection.remove(user)
            logging.info(f"Removed user ID {user_id} ({user.name}, Role: {type(user).__name__})")
            self._save_data()
            return user
        return None

    def update_user(self, user_id, **fields):
        user = self.find_user_by_id(user_id)
        if user is None:
            return None
        for field, value in fields.items():
            if field.startswith("_") or field == "id":
                raise ValueError(f"Cannot update protected field '{field}'.")
            if not hasattr(user, field):
                raise AttributeError(f"{type(user).__name__} has no field '{field}'.")
            if field == "email" and value:
                existing = self.find_user_by_email(value)
                if existing is not None and str(existing.id) != str(user_id):
                    raise ValueError(f"Email '{value}' is already in use by another user.")
            if field == "password" and value and not is_bcrypt_hash(value):
                value = hash_password(value)
            if isinstance(user, ClientUser) and field == "address":
                if isinstance(value, list):
                    value = str(value[0]).strip() if value and str(value[0]).strip() else ""
                elif value is None:
                    value = ""
                else:
                    value = str(value).strip()
            setattr(user, field, value)
        logging.info(f"Updated user ID {user_id}: {fields}")
        self._save_data()
        return user

    # Donation management.
    def add_donation(self, donor_id, description="", items=None, station=None):
        donor = self.find_donor_by_id(donor_id)
        if donor is None:
            raise ValueError(f"Donor ID {donor_id} does not exist.")
        donation = Donation(
            self.food_bank_data["next_donation_id"],
            donor_id,
            description=description,
            status="created",
            volunteer_id=None,
            station=station
        )
        if items is not None:
            if isinstance(items, dict):
                donation.items = [{"name": k, "quantity": v} for k, v in items.items()]
            else:
                donation.items = list(items)
        self._update_status(donation, "created")
        self.donations.append(donation)
        if hasattr(donor, "donation") and donation.id not in donor.donation:
            donor.donation.append(donation.id)
        self.food_bank_data["next_donation_id"] += 1
        logging.info(f"Added donation ID {donation.id} for donor ID {donor_id}")
        self._save_data()
        return donation

    def collect_donation(self, donation_id, volunteer_id=None):
        """Marks donation as collected by a volunteer or directly by staff/admin."""
        donation = self.find_donation_by_id(donation_id)
        if donation is None:
            raise ValueError(f"Donation ID {donation_id} does not exist.")
        
        target_vol_id = volunteer_id if volunteer_id is not None else donation.volunteer_id
        if target_vol_id is not None:
            volunteer = self.find_volunteer_by_id(target_vol_id)
            if volunteer is None:
                raise ValueError(f"Volunteer ID {target_vol_id} does not exist.")
            donation.volunteer_id = volunteer.id
            if hasattr(volunteer, "work") and hasattr(volunteer, "completed_work"):
                for job_item in [donation.id, str(donation.id), f"collect_donation_{donation.id}", f"donation_{donation.id}"]:
                    if job_item in volunteer.work:
                        volunteer.work.remove(job_item)
                        if job_item not in volunteer.completed_work:
                            volunteer.completed_work.append(job_item)

        self._update_status(donation, "collected")
        logging.info(f"Donation ID {donation_id} collected (volunteer: {donation.volunteer_id})")
        self._save_data()
        return donation

    def stock_donation(self, donation_id):
        """Transfers items from a donation into inventory, marking the donation as 'stocked'."""
        donation = self.find_donation_by_id(donation_id)
        if donation is None:
            raise ValueError(f"Donation ID {donation_id} does not exist.")
        
        curr_status = donation.status[0] if isinstance(donation.status, list) and donation.status else (donation.status or "")
        if str(curr_status).lower() not in ("collected", "created", "assigned"):
            raise ValueError(f"Cannot stock donation {donation_id} with status '{curr_status}'.")

        stocked_items = []
        for it in donation.items:
            if isinstance(it, dict):
                name = it.get("name", "").strip()
                category = it.get("category", "General").strip()
                quantity = float(it.get("quantity", 0))
                unit = it.get("unit", "pcs").strip()
            else:
                name = getattr(it, "name", "").strip()
                category = getattr(it, "category", "General").strip()
                quantity = float(getattr(it, "quantity", 0))
                unit = getattr(it, "unit", "pcs").strip()

            if not name or quantity <= 0:
                continue

            existing = self.inventory.find_item_by_name(name)
            if existing:
                self.add_stock(existing.id, quantity, reason=f"Stocked from Donation #{donation_id}")
                stocked_items.append({"item_id": existing.id, "name": name, "quantity": quantity})
            else:
                new_item = self.add_inventory_item(name, category, quantity, unit=unit)
                stocked_items.append({"item_id": new_item.id, "name": name, "quantity": quantity})

        self._update_status(donation, "stocked")
        logging.info(f"Stocked donation ID {donation_id} into inventory ({len(stocked_items)} items)")
        self._save_data()
        return stocked_items

    def update_donation(self, donation_id, **fields):
        donation = self.find_donation_by_id(donation_id)
        if donation is None: return None

        # Auto unbind from previous volunteer's work list if volunteer_id changed or unassigned
        prev_vol_id = getattr(donation, "volunteer_id", None)
        new_vol_id = fields.get("volunteer_id", prev_vol_id) if "volunteer_id" in fields else prev_vol_id

        if "volunteer_id" in fields and str(new_vol_id) != str(prev_vol_id):
            if prev_vol_id:
                prev_vol = self.find_volunteer_by_id(prev_vol_id)
                if prev_vol and hasattr(prev_vol, "work") and donation.id in prev_vol.work:
                    prev_vol.work.remove(donation.id)
            if new_vol_id:
                new_vol = self.find_volunteer_by_id(new_vol_id)
                if new_vol and hasattr(new_vol, "work") and donation.id not in new_vol.work:
                    new_vol.work.append(donation.id)

        # Automatic fallback: If volunteer becomes None/Unassigned and status was collected, return to 'created'
        curr_status = donation.status[0] if isinstance(donation.status, list) and donation.status else (donation.status or "")
        if "volunteer_id" in fields and fields["volunteer_id"] in (None, "", 0):
            target_status = fields.get("status", curr_status)
            if str(target_status).lower() == "collected":
                fields["status"] = "created"

        for field, value in fields.items():
            if field.startswith("_") or field == "id":
                raise ValueError(f"Cannot update protected field '{field}'.")
            if not hasattr(donation, field): raise AttributeError(f"Donation has no field '{field}'.")
            if field == "donor_id" and value not in (None, "", 0) and self.find_donor_by_id(value) is None:
                raise ValueError(f"Donor ID {value} does not exist.")
            if field == "volunteer_id" and value not in (None, "", 0) and self.find_volunteer_by_id(value) is None:
                raise ValueError(f"Volunteer ID {value} does not exist.")
            if field == "status":
                self._update_status(donation, value)
            else:
                setattr(donation, field, value)
        logging.info(f"Updated donation ID {donation_id}: {fields}")
        self._save_data()
        return donation

    def remove_donation(self, donation_id, donor_id=None):
        """Deletes donation only if status is 'created'; verifies donor ownership if donor_id provided; raises ValueError if 'collected'."""
        donation = self.find_donation_by_id(donation_id)
        if donation is None: return False

        if donor_id is not None and str(donation.donor_id) != str(donor_id):
            raise PermissionError(f"Donor {donor_id} is not authorized to delete donation {donation_id}.")
        
        curr_status = donation.status[0] if isinstance(donation.status, list) and donation.status else (donation.status or "")
        if str(curr_status).lower() != "created":
            raise ValueError(f"Cannot delete donation {donation_id} with status '{curr_status}'. Only 'created' donations can be deleted.")
        
        self.donations.remove(donation)
        for donor in self.donors:
            if hasattr(donor, "donation"):
                donor.donation = [item for item in donor.donation if str(item) != str(donation_id)]
        logging.info(f"Removed donation ID {donation_id}")
        self._save_data()
        return True

    def delete_donation(self, donation_id, donor_id=None):
        """Alias for remove_donation."""
        return self.remove_donation(donation_id, donor_id=donor_id)

    # Food hamper management.
    def add_food_hamper(self, client_id=None, description="", items=None, volunteer_id=None):
        if client_id not in (None, "", 0):
            if self.find_client_by_id(client_id) is None:
                raise ValueError(f"Client ID {client_id} does not exist.")
        else:
            client_id = None

        if volunteer_id not in (None, "", 0):
            if self.find_volunteer_by_id(volunteer_id) is None:
                raise ValueError(f"Volunteer ID {volunteer_id} does not exist.")
            status = "assigned"
        else:
            status = "created"

        hamper = FoodHamper(
            self.food_bank_data["next_food_hamper_id"],
            client_id,
            description,
            status=status,
            volunteer_id=volunteer_id
        )
        if items is not None:
            if isinstance(items, dict):
                hamper.items = [{"name": k, "quantity": v} for k, v in items.items()]
            else:
                hamper.items = list(items)
        if client_id:
            client = self.find_client_by_id(client_id)
            if hasattr(client, "receive") and hamper.id not in client.receive:
                client.receive.append(hamper.id)
        if volunteer_id:
            vol = self.find_volunteer_by_id(volunteer_id)
            if hasattr(vol, "work") and hamper.id not in vol.work:
                vol.work.append(hamper.id)

        self._update_status(hamper, status)
        self.food_hampers.append(hamper)
        self.food_bank_data["next_food_hamper_id"] += 1
        logging.info(f"Added food hamper ID {hamper.id} (Status: '{hamper.status}')")
        self._save_data()
        return hamper

    def update_food_hamper(self, hamper_id, **fields):
        hamper = self.find_food_hamper_by_id(hamper_id)
        if hamper is None: return None

        # Auto unbind from previous volunteer's work list if volunteer_id changed or unassigned
        prev_vol_id = getattr(hamper, "volunteer_id", None)
        new_vol_id = fields.get("volunteer_id", prev_vol_id) if "volunteer_id" in fields else prev_vol_id

        if "volunteer_id" in fields and str(new_vol_id) != str(prev_vol_id):
            if prev_vol_id:
                prev_vol = self.find_volunteer_by_id(prev_vol_id)
                if prev_vol and hasattr(prev_vol, "work") and hamper.id in prev_vol.work:
                    prev_vol.work.remove(hamper.id)
            if new_vol_id:
                new_vol = self.find_volunteer_by_id(new_vol_id)
                if new_vol and hasattr(new_vol, "work") and hamper.id not in new_vol.work:
                    new_vol.work.append(hamper.id)

        # Automatic fallback: If volunteer becomes None/Unassigned and status was assigned, return to 'created'
        curr_status = hamper.status[0] if isinstance(hamper.status, list) and hamper.status else (hamper.status or "")
        if "volunteer_id" in fields and fields["volunteer_id"] in (None, "", 0):
            target_status = fields.get("status", curr_status)
            if str(target_status).lower() == "assigned":
                fields["status"] = "created"

        for field, value in fields.items():
            if field.startswith("_") or field == "id":
                raise ValueError(f"Cannot update protected field '{field}'.")
            if not hasattr(hamper, field): raise AttributeError(f"FoodHamper has no field '{field}'.")
            if field == "client_id" and value not in (None, "", 0) and self.find_client_by_id(value) is None:
                raise ValueError(f"Client ID {value} does not exist.")
            if field == "volunteer_id" and value not in (None, "", 0) and self.find_volunteer_by_id(value) is None:
                raise ValueError(f"Volunteer ID {value} does not exist.")
            if field == "status":
                self._update_status(hamper, value)
            else:
                setattr(hamper, field, value)
        logging.info(f"Updated food hamper ID {hamper_id}: {fields}")
        self._save_data()
        return hamper

    def remove_food_hamper(self, hamper_id):
        """Deletes food hamper only if status is 'created'; raises ValueError if not 'created'."""
        hamper = self.find_food_hamper_by_id(hamper_id)
        if hamper is None:
            return False
        
        curr_status = hamper.status[0] if isinstance(hamper.status, list) and hamper.status else (hamper.status or "")
        if str(curr_status).lower() != "created":
            raise ValueError(f"Cannot delete food hamper {hamper_id} with status '{curr_status}'. Only 'created' food hampers can be deleted.")
        
        self.food_hampers.remove(hamper)
        for client in self.clients:
            if hasattr(client, "receive"):
                client.receive = [item for item in client.receive if str(item) != str(hamper_id)]
        logging.info(f"Removed food hamper ID {hamper_id}")
        self._save_data()
        return True

    def delete_food_hamper(self, hamper_id):
        """Alias for remove_food_hamper."""
        return self.remove_food_hamper(hamper_id)

    def assign_food_hamper(self, hamper_id, client_id, volunteer_id=None):
        """Assigns food hamper to a client, setting status to 'assigned' and recording volunteer."""
        hamper = self.find_food_hamper_by_id(hamper_id)
        client = self.find_client_by_id(client_id)
        if hamper is None: raise ValueError(f"Food hamper ID {hamper_id} does not exist.")
        if client is None: raise ValueError(f"Client ID {client_id} does not exist.")
        if hamper.client_id not in (None, "", 0) and str(hamper.client_id) != str(client_id):
            raise ValueError("This food hamper is already assigned to another client.")
        
        curr_status = hamper.status[0] if isinstance(hamper.status, list) and hamper.status else (hamper.status or "")
        if str(curr_status).lower() in ("delivered", "cancelled"):
            raise ValueError(f"Cannot assign food hamper {hamper_id} with status '{curr_status}'.")

        if volunteer_id is not None:
            volunteer = self.find_volunteer_by_id(volunteer_id)
            if volunteer is None:
                raise ValueError(f"Volunteer ID {volunteer_id} does not exist.")
            hamper.volunteer_id = volunteer.id
            if hasattr(volunteer, "work") and hamper.id not in volunteer.work:
                volunteer.work.append(hamper.id)

        hamper.client_id = client.id
        if str(curr_status).lower() != "packed":
            self._update_status(hamper, "assigned")
        if hasattr(client, "receive") and hamper.id not in client.receive:
            client.receive.append(hamper.id)
        logging.info(f"Assigned food hamper ID {hamper_id} to client ID {client_id} (Volunteer: {volunteer_id})")
        self._save_data()
        return hamper

    def deliver_food_hamper(self, hamper_id, volunteer_id=None):
        """Marks food hamper as successfully delivered to the client and invokes complete_job."""
        hamper = self.find_food_hamper_by_id(hamper_id)
        if hamper is None:
            raise ValueError(f"Food hamper ID {hamper_id} does not exist.")
        
        curr_status = hamper.status[0] if isinstance(hamper.status, list) and hamper.status else (hamper.status or "")
        if str(curr_status).lower() not in ("assigned", "packed"):
            raise ValueError(
                f"Cannot deliver hamper {hamper_id} with status '{curr_status}'. Hamper must be 'packed' or 'assigned' before delivery."
            )

        if volunteer_id is not None and hamper.volunteer_id is not None:
            if str(hamper.volunteer_id) != str(volunteer_id):
                raise PermissionError(f"Volunteer {volunteer_id} is not the assigned volunteer for hamper {hamper_id}.")

        self._update_status(hamper, "delivered")
        logging.info(f"Delivered food hamper ID {hamper_id} to client")

        # Complete work in the assigned volunteer's list (moves to completed_work)
        target_vol_id = volunteer_id or hamper.volunteer_id
        if target_vol_id:
            vol = self.find_volunteer_by_id(target_vol_id)
            if vol and hasattr(vol, "work"):
                if hamper.id in vol.work:
                    self.complete_job(target_vol_id, hamper.id)
                elif f"deliver_hamper_{hamper.id}" in vol.work:
                    self.complete_job(target_vol_id, f"deliver_hamper_{hamper.id}")

        self._save_data()
        return hamper

    def pack_food_hamper(self, hamper_id, items=None):
        """Packs a food hamper by verifying stock and deducting required quantities from inventory."""
        hamper = self.find_food_hamper_by_id(hamper_id)
        if hamper is None:
            raise ValueError(f"Food hamper ID {hamper_id} does not exist.")
        
        curr_status = hamper.status[0] if isinstance(hamper.status, list) and hamper.status else (hamper.status or "")
        if str(curr_status).lower() in ("delivered", "cancelled"):
            raise ValueError(f"Cannot pack hamper {hamper_id} with status '{curr_status}'.")

        items_to_pack = items if items is not None else hamper.items
        if not items_to_pack:
            raise ValueError(f"Cannot pack hamper {hamper_id} with an empty item list.")

        if isinstance(items_to_pack, dict):
            items_to_pack = [{"name": k, "quantity": v} for k, v in items_to_pack.items()]

        # 1. Pre-check: verify all items exist and have sufficient stock before deducting anything
        prepared_deductions = []
        for it in items_to_pack:
            if isinstance(it, dict):
                item_id = it.get("item_id") or it.get("id")
                item_name = it.get("name")
                qty = float(it.get("quantity", 1))
            elif isinstance(it, str):
                item_id = None
                item_name = it
                qty = 1.0
            else:
                item_id = getattr(it, "id", None)
                item_name = getattr(it, "name", None)
                qty = float(getattr(it, "quantity", 1))

            inv_item = None
            if item_id is not None:
                inv_item = self.inventory.find_item_by_id(item_id)
            elif item_name:
                inv_item = self.inventory.find_item_by_name(item_name)

            if inv_item is None:
                raise ValueError(f"Item '{item_name or item_id}' not found in inventory.")
            if inv_item.quantity < qty:
                raise ValueError(
                    f"Insufficient stock for '{inv_item.name}': requested {qty}, available {inv_item.quantity}."
                )
            prepared_deductions.append((inv_item, qty))

        # 2. Deduct quantities from inventory
        for inv_item, qty in prepared_deductions:
            self.remove_stock(inv_item.id, qty, reason=f"Packed for Hamper #{hamper_id}")

        hamper.items = list(items_to_pack)
        self._update_status(hamper, "packed")
        logging.info(f"Packed food hamper ID {hamper_id} with {len(items_to_pack)} items")
        self._save_data()
        return hamper

    def unpack_food_hamper(self, hamper_id):
        """Unpacks/cancels a packed food hamper, returning its items back into inventory."""
        hamper = self.find_food_hamper_by_id(hamper_id)
        if hamper is None:
            raise ValueError(f"Food hamper ID {hamper_id} does not exist.")
        
        curr_status = hamper.status[0] if isinstance(hamper.status, list) and hamper.status else (hamper.status or "")
        if str(curr_status).lower() == "delivered":
            raise ValueError(f"Cannot unpack hamper {hamper_id} that has already been delivered.")

        # Return items to inventory
        items_to_return = hamper.items
        if isinstance(items_to_return, dict):
            items_to_return = [{"name": k, "quantity": v} for k, v in items_to_return.items()]

        for it in (items_to_return or []):
            if isinstance(it, dict):
                item_id = it.get("item_id") or it.get("id")
                item_name = it.get("name")
                qty = float(it.get("quantity", 1))
            elif isinstance(it, str):
                item_id = None
                item_name = it
                qty = 1.0
            else:
                item_id = getattr(it, "id", None)
                item_name = getattr(it, "name", None)
                qty = float(getattr(it, "quantity", 1))

            inv_item = None
            if item_id is not None:
                inv_item = self.inventory.find_item_by_id(item_id)
            elif item_name:
                inv_item = self.inventory.find_item_by_name(item_name)

            if inv_item:
                self.add_stock(inv_item.id, qty, reason=f"Unpacked from Hamper #{hamper_id}")

        self._update_status(hamper, "created")
        logging.info(f"Unpacked food hamper ID {hamper_id}, returned items to inventory")
        self._save_data()
        return hamper

    def take_over_hamper(self, hamper_id, new_volunteer_id):
        """Transfers / takes over delivery of a food hamper to a new volunteer."""
        hamper = self.find_food_hamper_by_id(hamper_id)
        if hamper is None:
            raise ValueError(f"Food hamper ID {hamper_id} does not exist.")
        
        curr_status = hamper.status[0] if isinstance(hamper.status, list) and hamper.status else (hamper.status or "")
        if str(curr_status).lower() == "delivered":
            raise ValueError(f"Cannot take over food hamper {hamper_id} that has already been delivered.")

        new_vol = self.find_volunteer_by_id(new_volunteer_id)
        if new_vol is None:
            raise ValueError(f"New Volunteer ID {new_volunteer_id} does not exist.")

        # Clean up from previous volunteer's work list if assigned
        old_vol_id = hamper.volunteer_id
        if old_vol_id and str(old_vol_id) != str(new_volunteer_id):
            old_vol = self.find_volunteer_by_id(old_vol_id)
            if old_vol and hasattr(old_vol, "work"):
                old_vol.work = [item for item in old_vol.work if str(item) != str(hamper.id)]

        # Transfer to new volunteer
        hamper.volunteer_id = new_vol.id
        if hasattr(new_vol, "work") and hamper.id not in new_vol.work:
            new_vol.work.append(hamper.id)

        logging.info(f"Volunteer ID {new_volunteer_id} took over delivery of food hamper ID {hamper_id}")
        self._save_data()
        return hamper

    def take_over_donation(self, donation_id, new_volunteer_id):
        """Transfers / takes over collection of a donation to a new volunteer."""
        donation = self.find_donation_by_id(donation_id)
        if donation is None:
            raise ValueError(f"Donation ID {donation_id} does not exist.")
        new_vol = self.find_volunteer_by_id(new_volunteer_id)
        if new_vol is None:
            raise ValueError(f"New Volunteer ID {new_volunteer_id} does not exist.")

        # Clean up from previous volunteer if assigned
        old_vol_id = donation.volunteer_id
        if old_vol_id and str(old_vol_id) != str(new_volunteer_id):
            old_vol = self.find_volunteer_by_id(old_vol_id)
            if old_vol and hasattr(old_vol, "work"):
                old_vol.work = [item for item in old_vol.work if str(item) != str(donation.id)]

        # Transfer to new volunteer and set status
        donation.volunteer_id = new_vol.id
        self._update_status(donation, "collected")
        if hasattr(new_vol, "work") and donation.id not in new_vol.work:
            new_vol.work.append(donation.id)

        logging.info(f"Volunteer ID {new_volunteer_id} took over collection of donation ID {donation_id}")
        self._save_data()
        return donation

    def take_over_job(self, old_volunteer_id, new_volunteer_id, job):
        """Transfers a generic job from one volunteer to another."""
        old_vol = self.find_volunteer_by_id(old_volunteer_id)
        if old_vol is None:
            raise ValueError(f"Old Volunteer ID {old_volunteer_id} does not exist.")
        new_vol = self.find_volunteer_by_id(new_volunteer_id)
        if new_vol is None:
            raise ValueError(f"New Volunteer ID {new_volunteer_id} does not exist.")

        if hasattr(old_vol, "work") and job in old_vol.work:
            old_vol.work.remove(job)
        if not hasattr(new_vol, "work") or not isinstance(new_vol.work, list):
            new_vol.work = []
        if job not in new_vol.work:
            new_vol.work.append(job)

        logging.info(f"Transferred job '{job}' from volunteer ID {old_volunteer_id} to volunteer ID {new_volunteer_id}")
        self._save_data()
        return True

    def update_hamper_status(self, hamper_id, status):
        hamper = self.find_food_hamper_by_id(hamper_id)
        if hamper is None: return None
        self._update_status(hamper, status)
        logging.info(f"Updated food hamper ID {hamper_id} status to '{status}'")
        self._save_data()
        return hamper

    def get_available_hampers(self):
        """Returns food hampers that are created and not yet assigned to any client."""
        unavailable = {"assigned", "delivered", "unavailable", "cancelled", "flagged", "issue"}
        result = []
        for h in self.food_hampers:
            curr_status = h.status[0] if isinstance(h.status, list) and h.status else (h.status or "")
            if h.client_id in (None, "", 0) and str(curr_status).lower() not in unavailable:
                result.append(h)
        return result

    # Volunteer Job management.
    def assign_job(self, volunteer_id, job):
        """Assigns a job/task to a volunteer and persists changes."""
        volunteer = self.find_volunteer_by_id(volunteer_id)
        if volunteer is None:
            raise ValueError(f"Volunteer ID {volunteer_id} does not exist.")
        if not hasattr(volunteer, "work") or not isinstance(volunteer.work, list):
            volunteer.work = []
        volunteer.work.append(job)
        logging.info(f"Assigned job '{job}' to volunteer ID {volunteer_id}")
        self._save_data()
        return volunteer

    def get_volunteer_jobs(self, volunteer_id):
        """Returns list of jobs assigned to the volunteer."""
        volunteer = self.find_volunteer_by_id(volunteer_id)
        if volunteer is None:
            raise ValueError(f"Volunteer ID {volunteer_id} does not exist.")
        return getattr(volunteer, "work", [])

    def remove_job(self, volunteer_id, job):
        """Removes a job from the volunteer's assigned jobs.
        If the item/task is already 'in hand' (e.g. food hamper is assigned, or donation is collected),
        it CANNOT be deleted without first completing/delivering or transferring to another volunteer."""
        volunteer = self.find_volunteer_by_id(volunteer_id)
        if volunteer is None:
            raise ValueError(f"Volunteer ID {volunteer_id} does not exist.")
        if not hasattr(volunteer, "work") or job not in volunteer.work:
            return False

        # Extract potential ID (supports integer, 'hamper_1', 'donation_1', etc.)
        job_str = str(job)
        check_hamper_id = job_str.replace("deliver_hamper_", "").replace("hamper_", "") if "hamper" in job_str else job
        check_donation_id = job_str.replace("collect_donation_", "").replace("donation_", "") if "donation" in job_str else job

        # 1. Check if FoodHamper: if currently assigned/packed (in hand), cannot delete!
        hamper = self.find_food_hamper_by_id(check_hamper_id)
        if hamper is not None and hamper.volunteer_id is not None and str(hamper.volunteer_id) == str(volunteer.id):
            curr_status = hamper.status[0] if isinstance(hamper.status, list) and hamper.status else (hamper.status or "")
            if str(curr_status).lower() in ("assigned", "packed"):
                raise ValueError(
                    f"Cannot remove job: Food hamper {check_hamper_id} is already in progress ({curr_status}). "
                    "It must be delivered via deliver_food_hamper() or transferred via take_over_hamper()."
                )

        # 2. Check if Donation: if currently collected/in hand, cannot delete!
        donation = self.find_donation_by_id(check_donation_id)
        if donation is not None and donation.volunteer_id is not None and str(donation.volunteer_id) == str(volunteer.id):
            curr_status = donation.status[0] if isinstance(donation.status, list) and donation.status else (donation.status or "")
            if str(curr_status).lower() == "collected":
                raise ValueError(
                    f"Cannot remove job: Donation {check_donation_id} is already in hand (collected). "
                    "It must be processed or transferred via take_over_donation()."
                )

        # Check dictionary-based tasks
        if isinstance(job, dict) and job.get("status") in ("in_progress", "in_hand", "collected", "assigned"):
            raise ValueError("Cannot remove job: item/task is already in progress/in hand.")

        volunteer.work.remove(job)
        logging.info(f"Removed job '{job}' from volunteer ID {volunteer_id}")
        self._save_data()
        return True

    def complete_job(self, volunteer_id, job):
        """Marks a job as complete: moves it from active work to completed_work.
        If the job corresponds to an assigned food hamper, automatically marks it as delivered."""
        volunteer = self.find_volunteer_by_id(volunteer_id)
        if volunteer is None:
            raise ValueError(f"Volunteer ID {volunteer_id} does not exist.")
        if not hasattr(volunteer, "work") or not isinstance(volunteer.work, list):
            volunteer.work = []
        if not hasattr(volunteer, "completed_work") or not isinstance(volunteer.completed_work, list):
            volunteer.completed_work = []

        if job not in volunteer.work:
            return False

        # If it is an assigned/packed food hamper, mark as delivered
        hamper = self.find_food_hamper_by_id(job)
        if hamper is not None and str(hamper.status).lower() in ("assigned", "packed"):
            self._update_status(hamper, "delivered")

        volunteer.work.remove(job)
        if job not in volunteer.completed_work:
            volunteer.completed_work.append(job)

        logging.info(f"Completed job '{job}' for volunteer ID {volunteer_id}")
        self._save_data()
        return True

    def get_volunteer_completed_jobs(self, volunteer_id):
        """Returns list of completed jobs for the volunteer."""
        volunteer = self.find_volunteer_by_id(volunteer_id)
        if volunteer is None:
            raise ValueError(f"Volunteer ID {volunteer_id} does not exist.")
        return getattr(volunteer, "completed_work", [])

    # Volunteer self-service claiming and task pool management.
    def get_claimable_hampers(self):
        """Returns food hampers that are ready for delivery and have not been claimed by any volunteer."""
        claimable = []
        for h in self.food_hampers:
            curr_status = h.status[0] if isinstance(h.status, list) and h.status else (h.status or "")
            has_no_volunteer = h.volunteer_id in (None, "", 0)
            has_client = h.client_id not in (None, "", 0)
            valid_status = str(curr_status).lower() in ("assigned", "packed", "created")
            is_not_flagged = getattr(h, "flagged_issue", None) is None
            if has_no_volunteer and has_client and valid_status and is_not_flagged:
                claimable.append(h)
        return claimable

    def get_claimable_donations(self):
        """Returns donations that need collection and have not been claimed by any volunteer."""
        claimable = []
        for d in self.donations:
            curr_status = d.status[0] if isinstance(d.status, list) and d.status else (d.status or "")
            has_no_volunteer = d.volunteer_id in (None, "", 0)
            valid_status = str(curr_status).lower() in ("created", "pending")
            is_not_flagged = getattr(d, "flagged_issue", None) is None
            if has_no_volunteer and valid_status and is_not_flagged:
                claimable.append(d)
        return claimable

    def get_all_claimable_jobs(self):
        """Returns all open, claimable delivery and collection tasks."""
        return {
            "hampers": self.get_claimable_hampers(),
            "donations": self.get_claimable_donations(),
        }

    def claim_hamper(self, volunteer_id, hamper_id):
        """Allows a volunteer to claim/accept a food hamper delivery job."""
        volunteer = self.find_volunteer_by_id(volunteer_id)
        if volunteer is None:
            raise ValueError(f"Volunteer ID {volunteer_id} does not exist.")

        hamper = self.find_food_hamper_by_id(hamper_id)
        if hamper is None:
            raise ValueError(f"Food hamper ID {hamper_id} does not exist.")

        if hamper.volunteer_id not in (None, "", 0) and str(hamper.volunteer_id) != str(volunteer_id):
            raise ValueError(f"Food hamper {hamper_id} has already been claimed by volunteer ID {hamper.volunteer_id}.")

        curr_status = hamper.status[0] if isinstance(hamper.status, list) and hamper.status else (hamper.status or "")
        if str(curr_status).lower() == "delivered":
            raise ValueError(f"Cannot claim food hamper {hamper_id} because it has already been delivered.")

        if getattr(hamper, "flagged_issue", None) is not None:
            raise ValueError(f"Cannot claim food hamper {hamper_id} because it has an unresolved flagged issue.")

        hamper.volunteer_id = volunteer.id
        if str(curr_status).lower() == "created":
            self._update_status(hamper, "assigned")

        if not hasattr(volunteer, "work") or not isinstance(volunteer.work, list):
            volunteer.work = []
        if hamper.id not in volunteer.work:
            volunteer.work.append(hamper.id)

        logging.info(f"Volunteer ID {volunteer_id} successfully claimed food hamper ID {hamper_id}")
        self._save_data()
        return hamper

    def claim_donation(self, volunteer_id, donation_id):
        """Allows a volunteer to claim/accept a donation collection job."""
        volunteer = self.find_volunteer_by_id(volunteer_id)
        if volunteer is None:
            raise ValueError(f"Volunteer ID {volunteer_id} does not exist.")

        donation = self.find_donation_by_id(donation_id)
        if donation is None:
            raise ValueError(f"Donation ID {donation_id} does not exist.")

        if donation.volunteer_id not in (None, "", 0) and str(donation.volunteer_id) != str(volunteer_id):
            raise ValueError(f"Donation {donation_id} has already been claimed by volunteer ID {donation.volunteer_id}.")

        curr_status = donation.status[0] if isinstance(donation.status, list) and donation.status else (donation.status or "")
        if str(curr_status).lower() in ("collected", "stocked"):
            raise ValueError(f"Cannot claim donation {donation_id} with status '{curr_status}'.")

        if getattr(donation, "flagged_issue", None) is not None:
            raise ValueError(f"Cannot claim donation {donation_id} because it has an unresolved flagged issue.")

        donation.volunteer_id = volunteer.id
        self._update_status(donation, "assigned")

        if not hasattr(volunteer, "work") or not isinstance(volunteer.work, list):
            volunteer.work = []
        if donation.id not in volunteer.work:
            volunteer.work.append(donation.id)

        logging.info(f"Volunteer ID {volunteer_id} successfully claimed donation ID {donation_id}")
        self._save_data()
        return donation

    def release_hamper(self, volunteer_id, hamper_id):
        """Allows a volunteer to release / drop a previously claimed food hamper back to the open pool."""
        volunteer = self.find_volunteer_by_id(volunteer_id)
        if volunteer is None:
            raise ValueError(f"Volunteer ID {volunteer_id} does not exist.")

        hamper = self.find_food_hamper_by_id(hamper_id)
        if hamper is None:
            raise ValueError(f"Food hamper ID {hamper_id} does not exist.")

        if str(hamper.volunteer_id) != str(volunteer_id):
            raise ValueError(f"Volunteer ID {volunteer_id} is not assigned to food hamper {hamper_id}.")

        curr_status = hamper.status[0] if isinstance(hamper.status, list) and hamper.status else (hamper.status or "")
        if str(curr_status).lower() == "delivered":
            raise ValueError(f"Cannot release food hamper {hamper_id} because it has already been delivered.")

        hamper.volunteer_id = None
        if str(curr_status).lower() == "assigned":
            self._update_status(hamper, "created")

        if hasattr(volunteer, "work") and hamper.id in volunteer.work:
            volunteer.work.remove(hamper.id)

        logging.info(f"Volunteer ID {volunteer_id} released food hamper ID {hamper_id} back to open pool")
        self._save_data()
        return hamper

    def release_donation(self, volunteer_id, donation_id):
        """Allows a volunteer to release / drop a previously claimed donation back to the open pool."""
        volunteer = self.find_volunteer_by_id(volunteer_id)
        if volunteer is None:
            raise ValueError(f"Volunteer ID {volunteer_id} does not exist.")

        donation = self.find_donation_by_id(donation_id)
        if donation is None:
            raise ValueError(f"Donation ID {donation_id} does not exist.")

        if str(donation.volunteer_id) != str(volunteer_id):
            raise ValueError(f"Volunteer ID {volunteer_id} is not assigned to donation {donation_id}.")

        curr_status = donation.status[0] if isinstance(donation.status, list) and donation.status else (donation.status or "")
        if str(curr_status).lower() in ("collected", "stocked"):
            raise ValueError(f"Cannot release donation {donation_id} with status '{curr_status}'.")

        donation.volunteer_id = None
        self._update_status(donation, "created")

        if hasattr(volunteer, "work") and donation.id in volunteer.work:
            volunteer.work.remove(donation.id)

        logging.info(f"Volunteer ID {volunteer_id} released donation ID {donation_id} back to open pool")
        self._save_data()
        return donation

    # Issue tracking and resolution (Food Hampers & Donations).
    def flag_hamper_issue(self, hamper_id, issue_description, volunteer_id=None, new_status="flagged"):
        """Flags an issue on a food hamper, saving previous status and updating status to 'flagged'."""
        hamper = self.find_food_hamper_by_id(hamper_id)
        if hamper is None:
            raise ValueError(f"Food hamper ID {hamper_id} does not exist.")
        if not isinstance(issue_description, str) or not issue_description.strip():
            raise ValueError("Issue description cannot be empty.")
        if volunteer_id is not None and self.find_volunteer_by_id(volunteer_id) is None:
            raise ValueError(f"Volunteer ID {volunteer_id} does not exist.")

        curr_status = hamper.status[0] if isinstance(hamper.status, list) and hamper.status else (hamper.status or "created")
        hamper.previous_status = curr_status
        self._update_status(hamper, new_status)
        issue_record = {
            "entity_type": "hamper",
            "entity_id": hamper.id,
            "issue": issue_description.strip(),
            "volunteer_id": volunteer_id,
            "reported_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "previous_status": curr_status,
            "status": "open"
        }
        hamper.flagged_issue = issue_record
        if not hasattr(hamper, "issue_history") or not isinstance(hamper.issue_history, list):
            hamper.issue_history = []
        hamper.issue_history.append(issue_record)

        logging.info(f"Flagged issue on FoodHamper #{hamper_id} by volunteer {volunteer_id}: '{issue_description}' (Previous status: '{curr_status}', New status: '{new_status}')")
        self._save_data()
        return issue_record

    def flag_donation_issue(self, donation_id, issue_description, volunteer_id=None, new_status="flagged"):
        """Flags an issue on a donation, saving previous status and updating status to 'flagged'."""
        donation = self.find_donation_by_id(donation_id)
        if donation is None:
            raise ValueError(f"Donation ID {donation_id} does not exist.")
        if not isinstance(issue_description, str) or not issue_description.strip():
            raise ValueError("Issue description cannot be empty.")
        if volunteer_id is not None and self.find_volunteer_by_id(volunteer_id) is None:
            raise ValueError(f"Volunteer ID {volunteer_id} does not exist.")

        curr_status = donation.status[0] if isinstance(donation.status, list) and donation.status else (donation.status or "created")
        donation.previous_status = curr_status
        self._update_status(donation, new_status)
        issue_record = {
            "entity_type": "donation",
            "entity_id": donation.id,
            "issue": issue_description.strip(),
            "volunteer_id": volunteer_id,
            "reported_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "previous_status": curr_status,
            "status": "open"
        }
        donation.flagged_issue = issue_record
        if not hasattr(donation, "issue_history") or not isinstance(donation.issue_history, list):
            donation.issue_history = []
        donation.issue_history.append(issue_record)

        logging.info(f"Flagged issue on Donation #{donation_id} by volunteer {volunteer_id}: '{issue_description}' (Previous status: '{curr_status}', New status: '{new_status}')")
        self._save_data()
        return issue_record

    def flag_issue(self, entity_type, entity_id, issue_description, volunteer_id=None, new_status="flagged"):
        """Flags an issue on either a food hamper or donation, modifying its status."""
        clean_type = str(entity_type).strip().lower()
        if clean_type in ("hamper", "food_hamper", "foodhamper"):
            return self.flag_hamper_issue(entity_id, issue_description, volunteer_id=volunteer_id, new_status=new_status)
        elif clean_type in ("donation", "donations"):
            return self.flag_donation_issue(entity_id, issue_description, volunteer_id=volunteer_id, new_status=new_status)
        else:
            raise ValueError(f"Unsupported entity type '{entity_type}'. Must be 'hamper' or 'donation'.")

    def resolve_hamper_issue(self, hamper_id, resolution_notes="", resolved_by=None, restore_status=None):
        """Resolves a flagged issue on a food hamper and restores its status to previous or specified status."""
        hamper = self.find_food_hamper_by_id(hamper_id)
        if hamper is None:
            raise ValueError(f"Food hamper ID {hamper_id} does not exist.")

        target_status = restore_status or getattr(hamper, "previous_status", None) or "created"
        self._update_status(hamper, target_status)
        if getattr(hamper, "flagged_issue", None):
            hamper.flagged_issue["status"] = "resolved"
            hamper.flagged_issue["resolved_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            hamper.flagged_issue["resolution_notes"] = resolution_notes
            hamper.flagged_issue["resolved_by"] = resolved_by
        hamper.flagged_issue = None

        logging.info(f"Resolved issue on FoodHamper #{hamper_id}, restored status to '{target_status}'")
        self._save_data()
        return hamper

    def resolve_donation_issue(self, donation_id, resolution_notes="", resolved_by=None, restore_status=None):
        """Resolves a flagged issue on a donation and restores its status to previous or specified status."""
        donation = self.find_donation_by_id(donation_id)
        if donation is None:
            raise ValueError(f"Donation ID {donation_id} does not exist.")

        target_status = restore_status or getattr(donation, "previous_status", None) or "created"
        self._update_status(donation, target_status)
        if getattr(donation, "flagged_issue", None):
            donation.flagged_issue["status"] = "resolved"
            donation.flagged_issue["resolved_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            donation.flagged_issue["resolution_notes"] = resolution_notes
            donation.flagged_issue["resolved_by"] = resolved_by
        donation.flagged_issue = None

        logging.info(f"Resolved issue on Donation #{donation_id}, restored status to '{target_status}'")
        self._save_data()
        return donation

    def resolve_issue(self, entity_type, entity_id, resolution_notes="", resolved_by=None, restore_status=None):
        """Resolves a flagged issue on either a food hamper or donation, restoring original status."""
        clean_type = str(entity_type).strip().lower()
        if clean_type in ("hamper", "food_hamper", "foodhamper"):
            return self.resolve_hamper_issue(entity_id, resolution_notes=resolution_notes, resolved_by=resolved_by, restore_status=restore_status)
        elif clean_type in ("donation", "donations"):
            return self.resolve_donation_issue(entity_id, resolution_notes=resolution_notes, resolved_by=resolved_by, restore_status=restore_status)
        else:
            raise ValueError(f"Unsupported entity type '{entity_type}'. Must be 'hamper' or 'donation'.")

    def get_flagged_issues(self, entity_type=None):
        """Returns all open flagged issues across food hampers and donations."""
        issues = []
        clean_type = str(entity_type).strip().lower() if entity_type else None

        if clean_type in (None, "hamper", "food_hamper", "foodhamper"):
            for h in self.food_hampers:
                if getattr(h, "flagged_issue", None) and h.flagged_issue.get("status") == "open":
                    issues.append(h.flagged_issue)
                elif str(getattr(h, "status", "")).lower() == "flagged":
                    issues.append({
                        "entity_type": "hamper",
                        "entity_id": h.id,
                        "status": "open",
                        "issue": getattr(h, "description", "")
                    })

        if clean_type in (None, "donation", "donations"):
            for d in self.donations:
                if getattr(d, "flagged_issue", None) and d.flagged_issue.get("status") == "open":
                    issues.append(d.flagged_issue)
                elif str(getattr(d, "status", "")).lower() == "flagged":
                    issues.append({
                        "entity_type": "donation",
                        "entity_id": d.id,
                        "status": "open",
                        "issue": getattr(d, "description", "")
                    })

        return issues

    # Client Messaging management.
    def send_client_message(self, client_id, content):
        """Sends a message from a client, storing content and timestamp in a dictionary."""
        client = self.find_client_by_id(client_id)
        if client is None:
            raise ValueError(f"Client ID {client_id} does not exist.")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Message content cannot be empty.")

        if not hasattr(client, "messages") or not isinstance(client.messages, list):
            client.messages = []

        next_msg_id = max([int(m.get("id", 0)) for m in client.messages], default=0) + 1
        message = {
            "id": next_msg_id,
            "content": content.strip(),
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "is_edited": False
        }
        client.messages.append(message)
        logging.info(f"Client ID {client_id} sent message ID {message['id']}")
        self._save_data()
        return message

    def edit_client_message(self, client_id, message_id, new_content):
        """Edits an existing client message, updating content and displaying the edited timestamp."""
        client = self.find_client_by_id(client_id)
        if client is None:
            raise ValueError(f"Client ID {client_id} does not exist.")
        if not isinstance(new_content, str) or not new_content.strip():
            raise ValueError("New message content cannot be empty.")

        if not hasattr(client, "messages") or not isinstance(client.messages, list):
            client.messages = []

        target_msg = None
        for msg in client.messages:
            if str(msg.get("id")) == str(message_id):
                target_msg = msg
                break

        if target_msg is None:
            raise ValueError(f"Message ID {message_id} not found for client {client_id}.")

        target_msg["content"] = new_content.strip()
        target_msg["timestamp"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        target_msg["is_edited"] = True

        logging.info(f"Client ID {client_id} edited message ID {message_id} at {target_msg['timestamp']}")
        self._save_data()
        return target_msg

    def get_client_messages(self, client_id):
        """Returns the list of message dictionaries sent by the client."""
        client = self.find_client_by_id(client_id)
        if client is None:
            raise ValueError(f"Client ID {client_id} does not exist.")
        return getattr(client, "messages", [])

    def output_client_messages(self, client_id, print_to_console=True):
        """Formats and outputs all messages sent by the client, displaying edited timestamp if updated."""
        client = self.find_client_by_id(client_id)
        if client is None:
            raise ValueError(f"Client ID {client_id} does not exist.")

        messages = getattr(client, "messages", [])
        formatted_lines = []
        for msg in messages:
            tag = " (edited)" if msg.get("is_edited") else ""
            line = f"[{msg['timestamp']}]{tag} Message #{msg['id']} from {client.name} (ID {client.id}): {msg['content']}"
            formatted_lines.append(line)

        if print_to_console:
            for line in formatted_lines:
                print(line)

        return formatted_lines

    def delete_client_message(self, client_id, message_id):
        """Deletes a message from the client's message history."""
        client = self.find_client_by_id(client_id)
        if client is None:
            raise ValueError(f"Client ID {client_id} does not exist.")
        if hasattr(client, "messages"):
            client.messages = [m for m in client.messages if str(m.get("id")) != str(message_id)]
            logging.info(f"Deleted message ID {message_id} for client ID {client_id}")
            self._save_data()
            return True
        return False

    # FoodBank Organization & Collection Centers
    def set_foodbank_info(self, address=None, description=None):
        """Updates the FoodBank organization address and description."""
        if address is not None:
            self.address = str(address).strip()
            self.food_bank_data["address"] = self.address
        if description is not None:
            self.description = str(description).strip()
            self.food_bank_data["description"] = self.description
        logging.info(f"Updated FoodBank info (Address: '{self.address}')")
        self._save_data()
        return {"address": self.address, "description": self.description}

    def get_foodbank_info(self):
        """Returns the FoodBank organization address, description, and collection centers."""
        return {
            "address": self.address,
            "description": self.description,
            "collection_centers": self.collection_centers,
        }

    def add_collection_center(self, name, address):
        """Adds a new collection center with an id, name, and address."""
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Collection center name cannot be empty.")
        station_id = self.food_bank_data.get("next_station_id", 1)
        # Ensure station_id is unique
        existing_ids = [c.get("id", 0) for c in self.collection_centers]
        while station_id in existing_ids:
            station_id += 1
        center = {
            "id": int(station_id),
            "name": name.strip(),
            "address": str(address or "").strip()
        }
        self.collection_centers.append(center)
        self.food_bank_data["next_station_id"] = station_id + 1
        self.food_bank_data["collection_centers"] = self.collection_centers
        logging.info(f"Added collection center ID {center['id']}: '{center['name']}' at '{center['address']}'")
        self._save_data()
        return center

    def remove_collection_center(self, identifier):
        """Removes a collection center matching the given id or name."""
        initial_count = len(self.collection_centers)
        id_str = str(identifier).strip().lower()
        self.collection_centers = [
            c for c in self.collection_centers
            if str(c.get("id")) != id_str and c.get("name", "").strip().lower() != id_str
        ]
        self.food_bank_data["collection_centers"] = self.collection_centers
        if len(self.collection_centers) < initial_count:
            logging.info(f"Removed collection center: '{identifier}'")
            self._save_data()
            return True
        return False

    def update_collection_center(self, identifier, new_name=None, new_address=None):
        """Updates the name and/or address of an existing collection center or station by id, name, or index."""
        target_center = None
        id_str = str(identifier).strip().lower()
        for c in self.collection_centers:
            if str(c.get("id")) == id_str or c.get("name", "").strip().lower() == id_str:
                target_center = c
                break
        if target_center is None and isinstance(identifier, int) and 0 <= identifier < len(self.collection_centers):
            target_center = self.collection_centers[identifier]

        if target_center is None:
            raise ValueError(f"Collection center or station '{identifier}' not found.")

        if new_name is not None and str(new_name).strip():
            target_center["name"] = str(new_name).strip()
        if new_address is not None:
            target_center["address"] = str(new_address).strip()

        self.food_bank_data["collection_centers"] = self.collection_centers
        logging.info(f"Updated collection center/station '{target_center['name']}' at '{target_center['address']}'")
        self._save_data()
        return target_center

    def modify_collection_center(self, identifier, new_name=None, new_address=None):
        """Alias for update_collection_center."""
        return self.update_collection_center(identifier, new_name=new_name, new_address=new_address)

    def find_station_by_id(self, station_id):
        """Finds a collection center / station by its ID."""
        id_str = str(station_id).strip()
        for c in self.collection_centers:
            if str(c.get("id")) == id_str:
                return c
        return None

    find_collection_center_by_id = find_station_by_id

    def get_collection_centers(self):
        """Returns the list of collection centers."""
        return self.collection_centers

    # Station aliases (collection center / station support)
    def add_station(self, name, address):
        """Alias for add_collection_center."""
        return self.add_collection_center(name, address)

    def update_station(self, identifier, new_name=None, new_address=None):
        """Alias for update_collection_center."""
        return self.update_collection_center(identifier, new_name=new_name, new_address=new_address)

    def modify_station(self, identifier, new_name=None, new_address=None):
        """Alias for update_collection_center."""
        return self.update_collection_center(identifier, new_name=new_name, new_address=new_address)

    def remove_station(self, name):
        """Alias for remove_collection_center."""
        return self.remove_collection_center(name)

    def get_stations(self):
        """Alias for get_collection_centers."""
        return self.get_collection_centers()

    @property
    def stations(self):
        """Property alias for collection_centers."""
        return self.collection_centers

    @stations.setter
    def stations(self, value):
        self.collection_centers = value
        self.food_bank_data["collection_centers"] = value

    # Inventory proxy management (with auto-persistence).
    def add_inventory_item(self, name, category, quantity=0, unit="pcs", min_quantity=None):
        """Adds a new item or updates an existing item in inventory, with auto-save."""
        item = self.inventory.add_item(name, category, quantity=quantity, unit=unit, min_quantity=min_quantity)
        logging.info(f"Added/updated inventory item '{item.name}' (ID: {item.id}, Quantity: {item.quantity}) via FoodBank")
        self._save_data()
        return item

    def add_stock(self, item_id, quantity, reason="Stock In"):
        """Adds stock quantity to an inventory item, with auto-save."""
        result = self.inventory.add_stock(item_id, quantity, reason=reason)
        if result:
            logging.info(f"Added {quantity} stock to item ID {item_id} (Reason: '{reason}') via FoodBank")
            self._save_data()
        return result

    def remove_stock(self, item_id, quantity, reason="Stock Out"):
        """Deducts stock quantity from an inventory item, with auto-save."""
        result = self.inventory.remove_stock(item_id, quantity, reason=reason)
        if result:
            logging.info(f"Removed {quantity} stock from item ID {item_id} (Reason: '{reason}') via FoodBank")
            self._save_data()
        return result

    def get_inventory_items(self):
        """Returns all items in inventory."""
        return self.inventory.get_all_items()

    def get_low_stock_items(self):
        """Returns items in inventory whose quantity is at or below minimum threshold."""
        return self.inventory.get_low_stock_items()

    def get_stock_records(self, item_id=None):
        """Returns inventory transaction audit logs."""
        return self.inventory.get_stock_records(item_id=item_id)

    # CSV Export and Reporting Management.
    def _format_item_summary(self, items):
        """Formats an item list or dictionary into a human-readable summary string for CSV export."""
        if not items:
            return "None"
        if isinstance(items, dict):
            return "; ".join([f"{k}: {v}" for k, v in items.items()])
        formatted = []
        for it in items:
            if isinstance(it, dict):
                name = it.get("name") or it.get("item_name") or f"Item #{it.get('item_id', '')}"
                qty = it.get("quantity", 1)
                unit = it.get("unit", "")
                formatted.append(f"{name}: {qty} {unit}".strip())
            elif isinstance(it, str):
                formatted.append(it)
            else:
                name = getattr(it, "name", f"Item #{getattr(it, 'id', '')}")
                qty = getattr(it, "quantity", 1)
                unit = getattr(it, "unit", "")
                formatted.append(f"{name}: {qty} {unit}".strip())
        return "; ".join(formatted) if formatted else "None"

    def export_inventory_csv(self, filepath=None):
        """Exports current inventory items and stock alert status to a CSV file."""
        if filepath is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = Path("reports") / f"inventory_report_{timestamp}.csv"
        else:
            filepath = Path(filepath)

        filepath.parent.mkdir(parents=True, exist_ok=True)
        headers = ["Item ID", "Name", "Category", "Quantity", "Unit", "Min Quantity", "Stock Status"]

        with filepath.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for item in self.inventory.items:
                if item.quantity <= 0:
                    status = "Out of Stock"
                elif item.quantity <= item.min_quantity:
                    status = "Low Stock"
                else:
                    status = "Normal"
                writer.writerow([
                    item.id, item.name, item.category, item.quantity, item.unit, item.min_quantity, status
                ])

        logging.info(f"Exported inventory report to {filepath} ({len(self.inventory.items)} items)")
        return str(filepath)

    def export_transactions_csv(self, filepath=None):
        """Exports inventory stock change transaction history to a CSV file."""
        if filepath is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = Path("reports") / f"stock_transactions_{timestamp}.csv"
        else:
            filepath = Path(filepath)

        filepath.parent.mkdir(parents=True, exist_ok=True)
        headers = [
            "Record ID", "Timestamp", "Item ID", "Item Name",
            "Change Type", "Quantity Changed", "Previous Quantity", "New Quantity", "Reason"
        ]

        with filepath.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for r in self.inventory.stock_records:
                item = self.inventory.find_item_by_id(r.get("item_id"))
                item_name = item.name if item else "Unknown"
                writer.writerow([
                    r.get("id"), r.get("timestamp"), r.get("item_id"), item_name,
                    r.get("change_type"), r.get("quantity"), r.get("previous_quantity"),
                    r.get("new_quantity"), r.get("reason", "")
                ])

        logging.info(f"Exported stock transactions to {filepath} ({len(self.inventory.stock_records)} records)")
        return str(filepath)

    def export_hampers_csv(self, filepath=None):
        """Exports food hamper distribution records and status to a CSV file."""
        if filepath is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = Path("reports") / f"food_hampers_report_{timestamp}.csv"
        else:
            filepath = Path(filepath)

        filepath.parent.mkdir(parents=True, exist_ok=True)
        headers = [
            "Hamper ID", "Description", "Client ID", "Client Name",
            "Volunteer ID", "Volunteer Name", "Status", "Status Updated At", "Items", "Flagged Issue"
        ]

        with filepath.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for h in self.food_hampers:
                client = self.find_client_by_id(h.client_id) if h.client_id else None
                client_name = client.name if client else "Unassigned"
                vol = self.find_volunteer_by_id(h.volunteer_id) if h.volunteer_id else None
                vol_name = vol.name if vol else "Unassigned"
                status_str = h.status[0] if isinstance(h.status, list) and h.status else (h.status or "created")
                status_time = h.status_history[-1]["timestamp"] if getattr(h, "status_history", None) else ""
                items_str = self._format_item_summary(h.items)
                issue_str = h.flagged_issue.get("issue", "") if getattr(h, "flagged_issue", None) else "None"

                writer.writerow([
                    h.id, h.description, h.client_id or "", client_name,
                    h.volunteer_id or "", vol_name, status_str, status_time, items_str, issue_str
                ])

        logging.info(f"Exported food hampers report to {filepath} ({len(self.food_hampers)} hampers)")
        return str(filepath)

    def export_donations_csv(self, filepath=None):
        """Exports donations records and status to a CSV file."""
        if filepath is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = Path("reports") / f"donations_report_{timestamp}.csv"
        else:
            filepath = Path(filepath)

        filepath.parent.mkdir(parents=True, exist_ok=True)
        headers = [
            "Donation ID", "Description", "Donor ID", "Donor Name", "Station",
            "Volunteer ID", "Volunteer Name", "Status", "Status Updated At", "Items", "Flagged Issue"
        ]

        with filepath.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for d in self.donations:
                donor = self.find_donor_by_id(d.donor_id) if d.donor_id else None
                donor_name = donor.name if donor else "Anonymous"
                vol = self.find_volunteer_by_id(d.volunteer_id) if d.volunteer_id else None
                vol_name = vol.name if vol else "Unassigned"
                status_str = d.status[0] if isinstance(d.status, list) and d.status else (d.status or "created")
                status_time = d.status_history[-1]["timestamp"] if getattr(d, "status_history", None) else ""
                items_str = self._format_item_summary(d.items)
                issue_str = d.flagged_issue.get("issue", "") if getattr(d, "flagged_issue", None) else "None"
                station_str = getattr(d, "station", "") or "Unspecified"

                writer.writerow([
                    d.id, d.description, d.donor_id or "", donor_name, station_str,
                    d.volunteer_id or "", vol_name, status_str, status_time, items_str, issue_str
                ])

        logging.info(f"Exported donations report to {filepath} ({len(self.donations)} donations)")
        return str(filepath)

    def export_volunteers_csv(self, filepath=None):
        """Exports volunteer activity and task completion statistics to a CSV file."""
        if filepath is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = Path("reports") / f"volunteers_report_{timestamp}.csv"
        else:
            filepath = Path(filepath)

        filepath.parent.mkdir(parents=True, exist_ok=True)
        headers = [
            "Volunteer ID", "Name", "Email",
            "Active Jobs Count", "Active Job IDs",
            "Completed Jobs Count", "Completed Job IDs"
        ]

        with filepath.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for v in self.volunteers:
                active_jobs = getattr(v, "work", []) or []
                completed_jobs = getattr(v, "completed_work", []) or []
                writer.writerow([
                    v.id, v.name, getattr(v, "email", ""),
                    len(active_jobs), "; ".join(map(str, active_jobs)) if active_jobs else "None",
                    len(completed_jobs), "; ".join(map(str, completed_jobs)) if completed_jobs else "None"
                ])

        logging.info(f"Exported volunteers report to {filepath} ({len(self.volunteers)} volunteers)")
        return str(filepath)

    def export_all_reports(self, output_dir="reports"):
        """Generates and exports all 5 core CSV reports into the specified directory."""
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        generated = {
            "inventory": self.export_inventory_csv(out_path / f"inventory_report_{timestamp}.csv"),
            "transactions": self.export_transactions_csv(out_path / f"stock_transactions_{timestamp}.csv"),
            "food_hampers": self.export_hampers_csv(out_path / f"food_hampers_report_{timestamp}.csv"),
            "donations": self.export_donations_csv(out_path / f"donations_report_{timestamp}.csv"),
            "volunteers": self.export_volunteers_csv(out_path / f"volunteers_report_{timestamp}.csv"),
        }

        logging.info(f"Exported all 5 master reports to directory '{out_path}' (Timestamp: {timestamp})")
        return generated

    def get_system_summary(self):
        return {
            "admins": len(self.admins), "donors": len(self.donors),
            "staffs": len(self.staffs), "volunteers": len(self.volunteers),
            "clients": len(self.clients), "donations": len(self.donations),
            "food_hampers": len(self.food_hampers),
            "available_hampers": len(self.get_available_hampers()),
        }

    def validate_data(self):
        """Return data-integrity issues; an empty list means no issues were found."""
        issues = []
        users = sum((getattr(self, name) for name in self.USER_MODELS), [])
        for label, objects in (
            ("user", users), ("donation", self.donations), ("food hamper", self.food_hampers)
        ):
            ids = [str(obj.id) for obj in objects]
            if len(ids) != len(set(ids)):
                issues.append(f"Duplicate {label} IDs found.")

        # Check for duplicate user emails
        emails = [u.email.strip().lower() for u in users if hasattr(u, "email") and u.email]
        if len(emails) != len(set(emails)):
            issues.append("Duplicate user email addresses found.")

        # Check donor references in donations
        donor_ids = {str(d.id) for d in self.donors}
        for donation in self.donations:
            if donation.donor_id not in (None, "", 0) and str(donation.donor_id) not in donor_ids:
                issues.append(f"Donation {donation.id} references missing donor {donation.donor_id}.")

        # Check client references in food hampers
        client_ids = {str(c.id) for c in self.clients}
        for hamper in self.food_hampers:
            if hamper.client_id not in (None, "", 0) and str(hamper.client_id) not in client_ids:
                issues.append(f"Food hamper {hamper.id} references missing client {hamper.client_id}.")

        # Check volunteer references in food hampers and donations
        vol_ids = {str(v.id) for v in self.volunteers}
        for hamper in self.food_hampers:
            if hamper.volunteer_id not in (None, "", 0) and str(hamper.volunteer_id) not in vol_ids:
                issues.append(f"Food hamper {hamper.id} references missing volunteer {hamper.volunteer_id}.")
        for donation in self.donations:
            if donation.volunteer_id not in (None, "", 0) and str(donation.volunteer_id) not in vol_ids:
                issues.append(f"Donation {donation.id} references missing volunteer {donation.volunteer_id}.")

        return issues


# Functional class aliases
FoodBankManager = FoodBank
