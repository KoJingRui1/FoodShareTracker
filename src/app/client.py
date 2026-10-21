try:
    from src.app.user import User
except ModuleNotFoundError:
    from app.user import User
class ClientUser(User):
    def __init__(self, user_id, name, password, email):
        super().__init__(user_id, name, password, email)
        self.allergy = []
        self.address = []
        self.receive = []