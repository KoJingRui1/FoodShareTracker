try:
    from src.app.user import User
except ModuleNotFoundError:
    from app.user import User

class Donation:
    def __init__(self, id, donor_id, description="", status="created", volunteer_id=None):
        self.id = id
        self.donor_id = donor_id
        self.description = description
        self.status = status
        self.volunteer_id = volunteer_id
        self.items = []
        self.flagged_issue = None
        self.previous_status = None
        self.issue_history = []
