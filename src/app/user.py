class User:
    """A base class for all users in the system."""
    def __init__(self, user_id, name, password, email, profile_image="assets/default_avatar.png"):
        self.id = user_id
        self.name = name
        self.password = password
        self.email = email
        self.profile_image = profile_image
