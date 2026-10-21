import datetime

try:
    from src.app.item import Item
except ModuleNotFoundError:
    from app.item import Item

class Inventory:
    def __init__(self):
        self.items = []
        self.stock_records = []

        self.inventory_data = {
            "next_item_id": 1,
            "next_record_id": 1
        }

    def _record_transaction(self, item_id, change_type, quantity, previous_qty, new_qty, reason=""):
        """Records an inventory stock change transaction."""
        record_id = self.inventory_data.get("next_record_id", 1)
        record = {
            "id": record_id,
            "item_id": item_id,
            "change_type": change_type,
            "quantity": quantity,
            "previous_quantity": previous_qty,
            "new_quantity": new_qty,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "reason": reason
        }
        self.stock_records.append(record)
        self.inventory_data["next_record_id"] = record_id + 1
        return record

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

            prev_qty = existing_item.quantity
            existing_item.quantity += quantity
            existing_item.min_quantity = min_quantity
            if quantity > 0:
                self._record_transaction(
                    existing_item.id, "RESTOCK", quantity, prev_qty, existing_item.quantity, "Add existing item"
                )
            return existing_item

        # Create a new item.
        new_item = Item(
            self.inventory_data["next_item_id"],
            name.strip(),
            category.strip(),
            quantity,
            unit.strip(),
            min_quantity
        )

        self.items.append(new_item)
        self.inventory_data["next_item_id"] += 1

        if quantity > 0:
            self._record_transaction(
                new_item.id, "INITIAL", quantity, 0, quantity, "New item created"
            )

        return new_item

    def add_stock(self, item_id, quantity, reason="Stock In"):
        item = self.find_item_by_id(item_id)
        if item is None or quantity <= 0:
            return False

        prev_qty = item.quantity
        item.quantity += quantity
        self._record_transaction(item.id, "ADD_STOCK", quantity, prev_qty, item.quantity, reason)
        return True

    def remove_stock(self, item_id, quantity, reason="Stock Out"):
        item = self.find_item_by_id(item_id)
        if item is None or quantity <= 0:
            return False

        if item.quantity < quantity:
            return False

        prev_qty = item.quantity
        item.quantity -= quantity
        self._record_transaction(item.id, "REMOVE_STOCK", quantity, prev_qty, item.quantity, reason)
        return True

    def get_low_stock_items(self):
        return [
            item for item in self.items
            if item.quantity <= item.min_quantity
        ]

    def get_all_items(self):
        return self.items

    def get_stock_records(self, item_id=None):
        if item_id is None:
            return self.stock_records
        return [r for r in self.stock_records if str(r.get("item_id")) == str(item_id)]
