class FoodHamper:
    def __init__(self, id, client_id=None, description="", status="created", volunteer_id=None):
        self.id = id
        self.client_id = client_id
        self.description = description
        self.status = status
        self.volunteer_id = volunteer_id
        self.items = []
        self.flagged_issue = None
        self.previous_status = None
        self.issue_history = []
