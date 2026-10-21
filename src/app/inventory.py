import datetime
import logging

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
        logging.info(f"Inventory transaction #{record_id}: Item {item_id} {change_type} {quantity} ({reason}). New quantity: {new_qty}")
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
                unit="pcs", min_quantity=None):
        # Validate the input values.
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Item name cannot be empty.")

        if not isinstance(category, str) or not category.strip():
            raise ValueError("Item category cannot be empty.")

        if not isinstance(unit, str) or not unit.strip():
            raise ValueError("Item unit cannot be empty.")

        if isinstance(quantity, bool) or not isinstance(quantity, (int, float)):
            raise ValueError("Quantity must be a number.")

        if min_quantity is not None:
            if isinstance(min_quantity, bool) or not isinstance(min_quantity, (int, float)):
                raise ValueError("Minimum quantity must be a number.")
            if min_quantity < 0:
                raise ValueError("Minimum quantity cannot be negative.")

        if quantity < 0:
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
            # Preserve existing min_quantity threshold unless a positive value is explicitly provided
            if min_quantity is not None and min_quantity > 0:
                existing_item.min_quantity = min_quantity
            if quantity > 0:
                self._record_transaction(
                    existing_item.id, "RESTOCK", quantity, prev_qty, existing_item.quantity, "Add existing item"
                )
            logging.info(f"Restocked existing item '{existing_item.name}' (ID: {existing_item.id}) by {quantity}. Total: {existing_item.quantity}")
            return existing_item

        # Create a new item.
        effective_min_qty = 0 if min_quantity is None else min_quantity
        new_item = Item(
            self.inventory_data["next_item_id"],
            name.strip(),
            category.strip(),
            quantity,
            unit.strip(),
            effective_min_qty
        )

        self.items.append(new_item)
        self.inventory_data["next_item_id"] += 1

        if quantity > 0:
            self._record_transaction(
                new_item.id, "INITIAL", quantity, 0, quantity, "New item created"
            )

        logging.info(f"Created new inventory item '{new_item.name}' (ID: {new_item.id}, Quantity: {new_item.quantity} {new_item.unit})")
        return new_item

    def add_stock(self, item_id, quantity, reason="Stock In"):
        item = self.find_item_by_id(item_id)
        if item is None or quantity <= 0:
            return False

        prev_qty = item.quantity
        item.quantity += quantity
        self._record_transaction(item.id, "ADD_STOCK", quantity, prev_qty, item.quantity, reason)
        logging.info(f"Added {quantity} stock to Item {item.id} ('{item.name}'). Total: {item.quantity}")
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
        logging.info(f"Removed {quantity} stock from Item {item.id} ('{item.name}'). Remaining: {item.quantity}")
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
