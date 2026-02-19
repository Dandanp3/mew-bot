import random
from server.models.caughtPokemonModel import CaughtPokemonModel

class CatchController:
    def __init__(self, db):
        self.pokemon_collection = db['pokemons'] 
        self.caught_collection = db['caught_pokemons'] 

    async def create_specific_pokemon(self, owner_id: int, species_id: int, level: int = 5): 
        base_data = await self.pokemon_collection.find_one({"_id": species_id})
        if not base_data:
            return None, "Pokémon não encontrado na base de dados."

        # Calcula os moves baseados no Nível
        all_moves = base_data.get('moves', {}).get('level_up', [])
        allowed_moves = [m['name'] for m in all_moves if m['level'] <= level]
        initial_moves = allowed_moves[-4:] # Pega os 4 últimos

        new_pokemon = CaughtPokemonModel(
            owner_id=owner_id,
            species_id=species_id,
            species_name=base_data['name'],
            catch_order=await self.caught_collection.count_documents({"owner_id": owner_id}) + 1,
            level=level,
            initial_moves=initial_moves
        )

        # Calcula os Status Finais
        current_stats = new_pokemon.calculate_current_stats(base_data['stats'])
        pokemon_dict = new_pokemon.to_dict()
        pokemon_dict['stats'] = current_stats 

        result = await self.caught_collection.insert_one(pokemon_dict)     
        return result.inserted_id, new_pokemon