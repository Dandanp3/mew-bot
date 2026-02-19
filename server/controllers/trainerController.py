from server.models.trainerModel import TrainerModel
from datetime import datetime

class TrainerController:
    def __init__(self, db):
        self.collection = db['trainers']

    async def get_trainer(self, discord_id: str):
        return await self.collection.find_one({"_id": str(discord_id)})

    async def create_trainer(self, discord_id: str, username: str):
        existing = await self.get_trainer(discord_id)
        if existing:
            return False, "Você já possui um registro!"

        new_trainer = TrainerModel(str(discord_id), username)
        await self.collection.insert_one(new_trainer.to_dict())
        return True, "Treinador registrado!"

    async def set_starter(self, discord_id: str, caught_pokemon_id, species_id: int, region: str, types: list):
        await self.collection.update_one(
            {"_id": str(discord_id)},
            {
                "$set": {
                    "selected_pokemon_id": caught_pokemon_id, 
                    "total_caught": 1,
                },
                "$addToSet": {"pokedex_ids": species_id}, 
                "$inc": {
                    f"stats.regions.{region}": 1 # 
                }
            }
        )
        
        # Incrementa os tipos 
        for t in types:
            await self.collection.update_one(
                {"_id": str(discord_id)},
                {"$inc": {f"stats.types.{t}": 1}}
            )