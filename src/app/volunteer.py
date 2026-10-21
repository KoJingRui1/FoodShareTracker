from src.app.user import User

class VolunteerUser(User):
    def __init__(self, user_id, name, password, email):
        super().__init__(user_id, name, password, email)
        self.work = []
