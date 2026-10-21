try:
    from src.app.user import User
except ModuleNotFoundError:
    from app.user import User

class AdminUser(User):
    def __init__(self, user_id, name, password, email, profile_image="assets/default_avatar.png"):
        super().__init__(user_id, name, password, email, profile_image=profile_image)
