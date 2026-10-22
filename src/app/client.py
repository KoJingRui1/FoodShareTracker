try:
    from src.app.user import User
except ModuleNotFoundError:
    from app.user import User


class ClientUser(User):
    """Represents a client user who receives food assistance."""
    def __init__(self, user_id, name, password, email, description="", address="", profile_image="assets/default_avatar.png"):
        super().__init__(user_id, name, password, email, profile_image=profile_image)
        self.description = description
        self.address = address
        self.allergy = []
        self.receive = []
        self.messages = []
