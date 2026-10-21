try:
    from src.app.user import User
except ModuleNotFoundError:
    from app.user import User

class Inventory:
    def __init__(self):
        self.items = []
        self.stock_records = []

        self.inventory_data = {
            "next_item_id": 1,
            "next_record_id": 1
        }

    def find_item_by_id(self, item_id):
        for item in self.items:
            if item.id == item_id:
                return item
        return None

    def find_item_by_name(self, name):
        for item in self.items:
            if item.name.lower() == name.lower():
                return item
        return None


    def add_item(self, name, category, quantity=0,
                unit="pcs", min_quantity=0):

        # Validate the input values.
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Item name cannot be empty.")

        if not isinstance(category, str) or not category.strip():
            raise ValueError("Item category cannot be empty.")

        if not isinstance(unit, str) or not unit.strip():
            raise ValueError("Item unit cannot be empty.")

        if isinstance(quantity, bool) or not isinstance(quantity, (int, float)):
            raise ValueError("Quantity must be a number.")

        if isinstance(min_quantity, bool) or not isinstance(min_quantity, (int, float)):
            raise ValueError("Minimum quantity must be a number.")

        if quantity < 0 or min_quantity < 0:
            raise ValueError("Quantity cannot be negative.")

        # Check whether this item already exists.
        existing_item = self.find_item_by_name(name.strip())

        if existing_item:
            if existing_item.unit.lower() != unit.strip().lower():
                raise ValueError("The item already exists with a different unit.")

            if existing_item.category.lower() != category.strip().lower():
                raise ValueError("The item already exists in a different category.")

            existing_item.quantity += quantity
            existing_item.min_quantity = min_quantity
            return existing_item

        # Create a new item.
        item = Item(
            self.inventory_data["next_item_id"],
            name.strip(),
            category.strip(),
            quantity,
            unit.strip(),
            min_quantity
        )

        self.items.append(item)
        self.inventory_data["next_item_id"] += 1

        return item


    def add_stock(self, item_id, quantity):
        item = self.find_item_by_id(item_id)

        if item is None or quantity <= 0:
            return False

        item.quantity += quantity
        return True

    def remove_stock(self, item_id, quantity):
        item = self.find_item_by_id(item_id)

        if item is None or quantity <= 0:
            return False

        if item.quantity < quantity:
            return False

        item.quantity -= quantity
        return True

    def get_low_stock_items(self):
        return [
            item for item in self.items
            if item.quantity <= item.min_quantity
        ]

    def get_all_items(self):
        return self.items
