try:
    from src.app.user import User
except ModuleNotFoundError:
    from app.user import User
class Donation():
    def __init__(self, id, donor_id, description):
        self.id = id
        self.donor_id = donor_id
        self.status = []
        self.description = description
        self.items = []