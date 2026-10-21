# Store Food Bank data in a JSON file.
import json
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

        # Initialize collections before loading saved data.
        self.admins = []
        self.donors = []
        self.staffs = []
        self.volunteers = []
        self.clients = []
        self.donations = []
        self.food_hampers = []
        self.inventory = Inventory()
        # Shared counters/settings, following ScheduleManager's architecture.
        self.food_bank_data = {
            "next_user_id": 1,
            "next_donation_id": 1,
            "next_food_hamper_id": 1,
        }
        self._load_data()

    def _load_data(self):
        """Load JSON data and recreate each object, following ScheduleManager."""
        try:
            with self.data_path.open("r", encoding="utf-8") as file:
                data = json.load(file)

            # Rebuild each user collection directly in this method.
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
                    admin_data["password"], admin_data["email"]
                )
                self.admins.append(admin)

            for donor_data in data.get("donors", []):
                donor = DonorUser(
                    donor_data["id"], donor_data["name"],
                    donor_data["password"], donor_data["email"]
                )
                donor.donation = donor_data.get("donation", [])
                self.donors.append(donor)

            for staff_data in data.get("staffs", []):
                staff = StaffUser(
                    staff_data["id"], staff_data["name"],
                    staff_data["password"], staff_data["email"]
                )
                self.staffs.append(staff)

            for volunteer_data in data.get("volunteers", []):
                volunteer = VolunteerUser(
                    volunteer_data["id"], volunteer_data["name"],
                    volunteer_data["password"], volunteer_data["email"]
                )
                volunteer.work = volunteer_data.get("work", [])
                self.volunteers.append(volunteer)

            for client_data in data.get("clients", []):
                client = ClientUser(
                    client_data["id"], client_data["name"],
                    client_data["password"], client_data["email"]
                )
                client.allergy = client_data.get("allergy", [])
                client.address = client_data.get("address", [])
                client.receive = client_data.get("receive", [])
                self.clients.append(client)

            for donation_data in data.get("donations", []):
                donation = Donation(
                    donation_data["id"], donation_data["donor_id"],
                    donation_data["description"]
                )
                donation.status = donation_data.get("status", [])
                donation.items = donation_data.get("items", [])
                self.donations.append(donation)

            for hamper_data in data.get("food_hampers", []):
                hamper = FoodHamper(
                    hamper_data["id"], hamper_data["client_id"],
                    hamper_data["description"]
                )
                hamper.status = hamper_data.get("status", [])
                hamper.items = hamper_data.get("items", [])
                self.food_hampers.append(hamper)

            self.food_bank_data = data.get("food_bank_data", {
                "next_user_id": 1,
                "next_donation_id": 1,
                "next_food_hamper_id": 1,
            })

        except FileNotFoundError:
            print("Data file not found. Starting with a clean state.")
        # Load inventory data.
        inventory_data = data.get("inventory", {})

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

        self.inventory.stock_records = inventory_data.get(
            "stock_records", []
        )

        self.inventory.inventory_data = inventory_data.get(
            "inventory_data",
            {
                "next_item_id": 1,
                "next_record_id": 1
            }
        )
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

    def _add_user(self, model, collection, name, password, email):
        user = model(self.food_bank_data["next_user_id"], name, password, email)
        collection.append(user)
        self.food_bank_data["next_user_id"] += 1
        self._save_data()
        return user

    def add_admin(self, name, password, email): 
        return self._add_user(AdminUser, self.admins, name, password, email)
    def add_donor(self, name, password, email): 
        return self._add_user(DonorUser, self.donors, name, password, email)
    def add_staff(self, name, password, email): 
        return self._add_user(StaffUser, self.staffs, name, password, email)
    def add_volunteer(self, name, password, email): 
        return self._add_user(VolunteerUser, self.volunteers, name, password, email)
    def add_client(self, name, password, email): 
        return self._add_user(ClientUser, self.clients, name, password, email)

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
            if isinstance(user, DonorUser):
                self.donations = [d for d in self.donations if str(d.donor_id) != str(user_id)]
            if isinstance(user, ClientUser):
                self.food_hampers = [h for h in self.food_hampers if str(h.client_id) != str(user_id)]
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
            setattr(user, field, value)
        self._save_data()
        return user

    # Donation management.
    def add_donation(self, donor_id, description, items=None):
        if self.find_donor_by_id(donor_id) is None:
            raise ValueError(f"Donor ID {donor_id} does not exist.")
        donation = Donation(self.food_bank_data["next_donation_id"], donor_id, description)
        if items is not None:
            donation.items = list(items)
        self.donations.append(donation)
        self.food_bank_data["next_donation_id"] += 1
        self._save_data()
        return donation

    def update_donation(self, donation_id, **fields):
        donation = self.find_donation_by_id(donation_id)
        if donation is None: return None
        for field, value in fields.items():
            if field.startswith("_") or field == "id":
                raise ValueError(f"Cannot update protected field '{field}'.")
            if not hasattr(donation, field): raise AttributeError(f"Donation has no field '{field}'.")
            if field == "donor_id" and self.find_donor_by_id(value) is None:
                raise ValueError(f"Donor ID {value} does not exist.")
            setattr(donation, field, value)
        self._save_data()
        return donation

    def remove_donation(self, donation_id):
        donation = self.find_donation_by_id(donation_id)
        if donation is None: return False
        self.donations.remove(donation)
        self._save_data()
        return True

    # Food hamper management.
    def add_food_hamper(self, client_id, description, items=None):
        if self.find_client_by_id(client_id) is None:
            raise ValueError(f"Client ID {client_id} does not exist.")
        hamper = FoodHamper(self.food_bank_data["next_food_hamper_id"], client_id, description)
        if items is not None: hamper.items = list(items)
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
            if field == "client_id" and value is not None and self.find_client_by_id(value) is None:
                raise ValueError(f"Client ID {value} does not exist.")
            setattr(hamper, field, value)
        self._save_data()
        return hamper

    def remove_food_hamper(self, hamper_id):
        hamper = self.find_food_hamper_by_id(hamper_id)
        if hamper is None: return False
        self.food_hampers.remove(hamper)
        for client in self.clients:
            if hasattr(client, "receive"):
                client.receive = [item for item in client.receive if str(item) != str(hamper_id)]
        self._save_data()
        return True

    def assign_food_hamper(self, hamper_id, client_id):
        hamper = self.find_food_hamper_by_id(hamper_id)
        client = self.find_client_by_id(client_id)
        if hamper is None: raise ValueError(f"Food hamper ID {hamper_id} does not exist.")
        if client is None: raise ValueError(f"Client ID {client_id} does not exist.")
        if hamper.client_id not in (None, "", 0) and str(hamper.client_id) != str(client_id):
            raise ValueError("This food hamper is already assigned to another client.")
        hamper.client_id = client.id
        if not isinstance(hamper.status, list): hamper.status = []
        if "assigned" not in hamper.status: hamper.status.append("assigned")
        if hasattr(client, "receive") and hamper.id not in client.receive:
            client.receive.append(hamper.id)
        self._save_data()
        return hamper

    def update_hamper_status(self, hamper_id, status):
        hamper = self.find_food_hamper_by_id(hamper_id)
        if hamper is None: return None
        if not isinstance(hamper.status, list): hamper.status = []
        if status not in hamper.status: hamper.status.append(status)
        self._save_data()
        return hamper

    def get_available_hampers(self):
        unavailable = {"assigned", "delivered", "unavailable", "cancelled"}
        return [h for h in self.food_hampers
                if h.client_id in (None, "", 0)
                and not (set(h.status) & unavailable)]

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
        donor_ids = {str(d.id) for d in self.donors}
        for donation in self.donations:
            if str(donation.donor_id) not in donor_ids:
                issues.append(f"Donation {donation.id} references missing donor {donation.donor_id}.")
        client_ids = {str(c.id) for c in self.clients}
        for hamper in self.food_hampers:
            if hamper.client_id not in (None, "", 0) and str(hamper.client_id) not in client_ids:
                issues.append(f"Food hamper {hamper.id} references missing client {hamper.client_id}.")
        return issues
