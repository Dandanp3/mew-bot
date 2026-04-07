from server.models.trainerModel import TrainerModel
from datetime import datetime

class TrainerController:
    def __init__(self, db):
        self.collection = db['trainers']
        self.db = db
    
    async def get_trainer(self, discord_id: int):
        return await self.collection.find_one({"_id": discord_id})
    
    async def create_trainer(self, discord_id: int, username: str, trainer_model=None):
        if trainer_model is None:
            trainer_model = TrainerModel(
                discord_id=str(discord_id),
                username=username
            )
        
        trainer_data = trainer_model.to_dict()
        trainer_data["_id"] = discord_id 
        
        result = await self.collection.insert_one(trainer_data)
        return True, "Trainer created successfully!"
    
    async def update_trainer(self, trainer_model):
        filter_query = {"_id": trainer_model.discord_id}
        update_data = {"$set": trainer_model.to_dict()}
        
        result = await self.collection.update_one(filter_query, update_data, upsert=True)
        return result.modified_count
    
    async def set_starter(self, discord_id: int, caught_pokemon_id: str, species_id: int, region: str, types: list):
        #Define o starter Pokémon do treinador
        
        filter_query = {"_id": discord_id}
        update_data = {
            "$set": {
                "selected_pokemon_id": caught_pokemon_id,  
            },
            "$inc": {}  
        }
        
        # Incrementar regiões
        update_data["$inc"][f"stats.regions.{region}"] = 1
        
        # Incrementar tipos
        for t in types:
            t_cap = t.capitalize()
            update_data["$inc"][f"stats.types.{t_cap}"] = 1
        
        result = await self.collection.update_one(filter_query, update_data, upsert=True)
        return result.modified_count > 0
    
    async def delete_trainer(self, discord_id: int):

        result = await self.collection.delete_one({"_id": discord_id})
        return result.deleted_count
    
    async def get_all_trainers(self):

        return await self.collection.find().to_list(None)