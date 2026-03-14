class serverModel:
    def __init__(self,
                 id: int,
                 chat: int):
        
        self.chat = chat
        self.id = id
    
    def to_dict(self):
        return {
            "id": self.id,
            "chat": self.chat
        }