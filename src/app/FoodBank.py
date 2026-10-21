# Store Food Bank data in a JSON file.
import json
import datetime
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


class FoodBank:
    """Main controller for Food Bank business logic and JSON persistence."""

    USER_MODELS = {
        "admins": AdminUser,
        "donors": DonorUser,
        "staffs": StaffUser,
        "volunteers": VolunteerUser,
        "clients": ClientUser,
    }

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
        self.food_bank_data = {
            "next_user_id": 1,
            "next_donation_id": 1,
            "next_food_hamper_id": 1,
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
                client = ClientUser(
                    client_data["id"], client_data["name"],
                    client_data["password"], client_data["email"],
                    description=client_data.get("description", ""),
                    profile_image=client_data.get("profile_image", "assets/default_avatar.png")
                )
                client.allergy = client_data.get("allergy", [])
                client.address = client_data.get("address", [])
                client.receive = client_data.get("receive", [])
                client.messages = client_data.get("messages", [])
                self.clients.append(client)

            for donation_data in data.get("donations", []):
                raw_status = donation_data.get("status", "created")
                status = raw_status[0] if isinstance(raw_status, list) and raw_status else (raw_status or "created")
                donation = Donation(
                    donation_data["id"], donation_data.get("donor_id"),
                    donation_data["description"], status=status,
                    volunteer_id=donation_data.get("volunteer_id")
                )
                donation.items = donation_data.get("items", [])
                self.donations.append(donation)

            for hamper_data in data.get("food_hampers", []):
                raw_status = hamper_data.get("status", "created")
                status = raw_status[0] if isinstance(raw_status, list) and raw_status else (raw_status or "created")
                hamper = FoodHamper(
                    hamper_data["id"], hamper_data.get("client_id"),
                    hamper_data["description"], status=status,
                    volunteer_id=hamper_data.get("volunteer_id")
                )
                hamper.items = hamper_data.get("items", [])
                self.food_hampers.append(hamper)

            self.food_bank_data = data.get("food_bank_data", {
                "next_user_id": 1,
                "next_donation_id": 1,
                "next_food_hamper_id": 1,
            })

            # Load inventory data safely inside try block.
            inventory_data = data.get("inventory", {})
            self.inventory = Inventory()
            self.inventory.items = []

            for item_data in inventory_data.get("items", []):
                item = Item(
                    item_data["id"],
                    item_data["name"],
                    item_data["category"],
                    item_data.get("quantity", 0),
                    item_data.get("unit", "pcs"),
                    item_data.get("min_quantity", 0)
                )
                self.inventory.items.append(item)

            self.inventory.stock_records = inventory_data.get("stock_records", [])
            self.inventory.inventory_data = inventory_data.get(
                "inventory_data",
                {
                    "next_item_id": 1,
                    "next_record_id": 1
                }
            )

        except (FileNotFoundError, json.JSONDecodeError):
            print("Data file not found or corrupted. Starting with a clean state.")
            self._init_empty_state()

    def _save_data(self):
        """Save the collections and system counters as JSON, like ScheduleManager."""
        data_to_save = {
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
        """Authenticates user credentials and returns (user, role_name) or None."""
        user = self.find_user_by_email(email)
        if user is not None and user.password == password:
            for role_name, model in self.USER_MODELS.items():
                if isinstance(user, model):
                    return user, role_name
        return None

    def _add_user(self, model, collection, name, password, email, profile_image="assets/default_avatar.png"):
        if self.find_user_by_email(email) is not None:
            raise ValueError(f"Email '{email}' is already registered.")
        user = model(self.food_bank_data["next_user_id"], name, password, email, profile_image=profile_image)
        collection.append(user)
        self.food_bank_data["next_user_id"] += 1
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
    def add_client(self, name, password, email, description="", profile_image="assets/default_avatar.png"): 
        if self.find_user_by_email(email) is not None:
            raise ValueError(f"Email '{email}' is already registered.")
        user = ClientUser(
            self.food_bank_data["next_user_id"],
            name,
            password,
            email,
            description=description,
            profile_image=profile_image
        )
        self.clients.append(user)
        self.food_bank_data["next_user_id"] += 1
        self._save_data()
        return user

    def get_user_profile_image(self, user_id):
        """Returns the profile image path for the specified user, or default avatar if unset."""
        user = self.find_user_by_id(user_id)
        if user is None:
            return None
        return getattr(user, "profile_image", None) or "assets/default_avatar.png"

    def set_user_profile_image(self, user_id, profile_image):
        """Updates the profile image path for the specified user and saves to disk."""
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
        collection.append(user)
        try:
            self.food_bank_data["next_user_id"] = max(self.food_bank_data["next_user_id"], int(user.id) + 1)
        except (TypeError, ValueError):
            pass
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
                            # Assigned hamper cannot be deleted; unbind client and reset status to created
                            hamper.client_id = None
                            hamper.status = "created"
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
            setattr(user, field, value)
        self._save_data()
        return user

    # Donation management.
    def add_donation(self, donor_id, description="", items=None):
        donor = self.find_donor_by_id(donor_id)
        if donor is None:
            raise ValueError(f"Donor ID {donor_id} does not exist.")
        donation = Donation(
            self.food_bank_data["next_donation_id"],
            donor_id,
            description=description,
            status="created",
            volunteer_id=None
        )
        if items is not None:
            donation.items = list(items)
        self.donations.append(donation)
        if hasattr(donor, "donation") and donation.id not in donor.donation:
            donor.donation.append(donation.id)
        self.food_bank_data["next_donation_id"] += 1
        self._save_data()
        return donation

    def collect_donation(self, donation_id, volunteer_id):
        """Marks donation as collected by a volunteer, recording volunteer ID."""
        donation = self.find_donation_by_id(donation_id)
        if donation is None:
            raise ValueError(f"Donation ID {donation_id} does not exist.")
        volunteer = self.find_volunteer_by_id(volunteer_id)
        if volunteer is None:
            raise ValueError(f"Volunteer ID {volunteer_id} does not exist.")
        
        donation.status = "collected"
        donation.volunteer_id = volunteer.id
        if hasattr(volunteer, "work") and donation.id not in volunteer.work:
            volunteer.work.append(donation.id)
        self._save_data()
        return donation

    def stock_donation(self, donation_id):
        """Transfers items from a donation into inventory, marking the donation as 'stocked'."""
        donation = self.find_donation_by_id(donation_id)
        if donation is None:
            raise ValueError(f"Donation ID {donation_id} does not exist.")
        
        curr_status = donation.status[0] if isinstance(donation.status, list) and donation.status else (donation.status or "")
        if str(curr_status).lower() not in ("collected", "created"):
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

        donation.status = "stocked"
        self._save_data()
        return stocked_items

    def update_donation(self, donation_id, **fields):
        donation = self.find_donation_by_id(donation_id)
        if donation is None: return None
        for field, value in fields.items():
            if field.startswith("_") or field == "id":
                raise ValueError(f"Cannot update protected field '{field}'.")
            if not hasattr(donation, field): raise AttributeError(f"Donation has no field '{field}'.")
            if field == "donor_id" and value not in (None, "", 0) and self.find_donor_by_id(value) is None:
                raise ValueError(f"Donor ID {value} does not exist.")
            if field == "volunteer_id" and value not in (None, "", 0) and self.find_volunteer_by_id(value) is None:
                raise ValueError(f"Volunteer ID {value} does not exist.")
            setattr(donation, field, value)
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
            status = "assigned"
        else:
            client_id = None
            status = "created"
        
        if volunteer_id not in (None, "", 0) and self.find_volunteer_by_id(volunteer_id) is None:
            raise ValueError(f"Volunteer ID {volunteer_id} does not exist.")

        hamper = FoodHamper(
            self.food_bank_data["next_food_hamper_id"],
            client_id,
            description,
            status=status,
            volunteer_id=volunteer_id
        )
        if items is not None:
            hamper.items = list(items)
        if client_id:
            client = self.find_client_by_id(client_id)
            if hasattr(client, "receive") and hamper.id not in client.receive:
                client.receive.append(hamper.id)
        if volunteer_id:
            vol = self.find_volunteer_by_id(volunteer_id)
            if hasattr(vol, "work") and hamper.id not in vol.work:
                vol.work.append(hamper.id)

        self.food_hampers.append(hamper)
        self.food_bank_data["next_food_hamper_id"] += 1
        self._save_data()
        return hamper

    def update_food_hamper(self, hamper_id, **fields):
        hamper = self.find_food_hamper_by_id(hamper_id)
        if hamper is None: return None
        for field, value in fields.items():
            if field.startswith("_") or field == "id":
                raise ValueError(f"Cannot update protected field '{field}'.")
            if not hasattr(hamper, field): raise AttributeError(f"FoodHamper has no field '{field}'.")
            if field == "client_id" and value not in (None, "", 0) and self.find_client_by_id(value) is None:
                raise ValueError(f"Client ID {value} does not exist.")
            if field == "volunteer_id" and value not in (None, "", 0) and self.find_volunteer_by_id(value) is None:
                raise ValueError(f"Volunteer ID {value} does not exist.")
            setattr(hamper, field, value)
        self._save_data()
        return hamper

    def remove_food_hamper(self, hamper_id):
        """Deletes food hamper only if status is 'created'; raises ValueError if 'assigned'."""
        hamper = self.find_food_hamper_by_id(hamper_id)
        if hamper is None:
            return False
        
        curr_status = hamper.status[0] if isinstance(hamper.status, list) and hamper.status else (hamper.status or "")
        if str(curr_status).lower() == "assigned":
            raise ValueError(f"Cannot delete food hamper {hamper_id} with status 'assigned'. Only 'created' food hampers can be deleted.")
        
        self.food_hampers.remove(hamper)
        for client in self.clients:
            if hasattr(client, "receive"):
                client.receive = [item for item in client.receive if str(item) != str(hamper_id)]
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
        
        if volunteer_id is not None:
            volunteer = self.find_volunteer_by_id(volunteer_id)
            if volunteer is None:
                raise ValueError(f"Volunteer ID {volunteer_id} does not exist.")
            hamper.volunteer_id = volunteer.id
            if hasattr(volunteer, "work") and hamper.id not in volunteer.work:
                volunteer.work.append(hamper.id)

        hamper.client_id = client.id
        hamper.status = "assigned"
        if hasattr(client, "receive") and hamper.id not in client.receive:
            client.receive.append(hamper.id)
        self._save_data()
        return hamper

    def deliver_food_hamper(self, hamper_id, volunteer_id=None):
        """Marks food hamper as successfully delivered to the client and invokes complete_job."""
        hamper = self.find_food_hamper_by_id(hamper_id)
        if hamper is None:
            raise ValueError(f"Food hamper ID {hamper_id} does not exist.")
        
        curr_status = hamper.status[0] if isinstance(hamper.status, list) and hamper.status else (hamper.status or "")
        if str(curr_status).lower() != "assigned":
            raise ValueError(f"Cannot deliver hamper {hamper_id} with status '{curr_status}'. Hamper must be 'assigned' before delivery.")

        if volunteer_id is not None and hamper.volunteer_id is not None:
            if str(hamper.volunteer_id) != str(volunteer_id):
                raise PermissionError(f"Volunteer {volunteer_id} is not the assigned volunteer for hamper {hamper_id}.")

        hamper.status = "delivered"

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

        # 1. Pre-check: verify all items exist and have sufficient stock before deducting anything
        prepared_deductions = []
        for it in items_to_pack:
            if isinstance(it, dict):
                item_id = it.get("item_id") or it.get("id")
                item_name = it.get("name")
                qty = float(it.get("quantity", 1))
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
        if str(curr_status).lower() == "created":
            hamper.status = "packed"
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
        for it in hamper.items:
            if isinstance(it, dict):
                item_id = it.get("item_id") or it.get("id")
                item_name = it.get("name")
                qty = float(it.get("quantity", 1))
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

        hamper.status = "created"
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
        donation.status = "collected"
        if hasattr(new_vol, "work") and donation.id not in new_vol.work:
            new_vol.work.append(donation.id)

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

        self._save_data()
        return True

    def update_hamper_status(self, hamper_id, status):
        hamper = self.find_food_hamper_by_id(hamper_id)
        if hamper is None: return None
        hamper.status = status
        self._save_data()
        return hamper

    def get_available_hampers(self):
        """Returns food hampers that are created and not yet assigned to any client."""
        unavailable = {"assigned", "delivered", "unavailable", "cancelled"}
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

        # 1. Check if FoodHamper: if currently assigned/in hand, cannot delete!
        hamper = self.find_food_hamper_by_id(check_hamper_id)
        if hamper is not None and hamper.volunteer_id is not None and str(hamper.volunteer_id) == str(volunteer.id):
            curr_status = hamper.status[0] if isinstance(hamper.status, list) and hamper.status else (hamper.status or "")
            if str(curr_status).lower() == "assigned":
                raise ValueError(
                    f"Cannot remove job: Food hamper {check_hamper_id} is already in hand (assigned). "
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

        # If it is an assigned food hamper, mark as delivered
        hamper = self.find_food_hamper_by_id(job)
        if hamper is not None and str(hamper.status).lower() == "assigned":
            hamper.status = "delivered"

        volunteer.work.remove(job)
        if job not in volunteer.completed_work:
            volunteer.completed_work.append(job)

        self._save_data()
        return True

    def get_volunteer_completed_jobs(self, volunteer_id):
        """Returns list of completed jobs for the volunteer."""
        volunteer = self.find_volunteer_by_id(volunteer_id)
        if volunteer is None:
            raise ValueError(f"Volunteer ID {volunteer_id} does not exist.")
        return getattr(volunteer, "completed_work", [])

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
            self._save_data()
            return True
        return False

    # Inventory proxy management (with auto-persistence).
    def add_inventory_item(self, name, category, quantity=0, unit="pcs", min_quantity=0):
        """Adds a new item or updates an existing item in inventory, with auto-save."""
        item = self.inventory.add_item(name, category, quantity=quantity, unit=unit, min_quantity=min_quantity)
        self._save_data()
        return item

    def add_stock(self, item_id, quantity, reason="Stock In"):
        """Adds stock quantity to an inventory item, with auto-save."""
        result = self.inventory.add_stock(item_id, quantity, reason=reason)
        if result:
            self._save_data()
        return result

    def remove_stock(self, item_id, quantity, reason="Stock Out"):
        """Deducts stock quantity from an inventory item, with auto-save."""
        result = self.inventory.remove_stock(item_id, quantity, reason=reason)
        if result:
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
