class FoodHamper():
    def __init__(self, id, client_id, description):
        self.id = id
        self.client_id = client_id
        self.status = []
        self.description = description
        self.items = []