try:
    from src.app.user import User
except ModuleNotFoundError:
    from app.user import User
class Item:
    def __init__(self, item_id, name, category, quantity=0, unit="pcs", min_quantity=0):
        self.id = item_id
        self.name = name
        self.category = category
        self.quantity = quantity
        self.unit = unit
        self.min_quantity = min_quantity
