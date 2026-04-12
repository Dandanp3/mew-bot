import math
from typing import Optional
from server.models.caughtPokemonModel import CaughtPokemonModel

class XPController:
    def __init__(self, bot):
        self.bot = bot

    def _calculate_xp_for_level(self, level: int) -> int:
        return int(math.pow(level, 3))

    async def add_xp(self, user_id: int, amount: int = 100):
        # 1. Busca o treinador para saber qual o pokemon selecionado
        trainer = await self.bot.db.trainers.find_one({"_id": user_id})
        if not trainer or not trainer.get("selected_pokemon_id"):
            return

        pokemon_id = trainer["selected_pokemon_id"]
        
        # Busca os dados do Pokémon e os Base Stats da espécie
        pokemon_data = await self.bot.db.caught_pokemons.find_one({"_id": pokemon_id})
        if not pokemon_data:
            return

        # Trava no level 100
        current_level = pokemon_data.get("level", 1)
        if current_level >= 100:
            return

        base_stats_data = await self.bot.db.pokemons.find_one({"_id": pokemon_data["species_id"]})
        if not base_stats_data:
            return

        # Atualiza XP e verifica Level Up
        new_xp = pokemon_data.get("total_xp", 0) + amount
        new_level = current_level
        leveled_up = False

        # Verifica se o novo XP é suficiente para o próximo nível
        while new_level < 100:
            xp_needed_for_next = self._calculate_xp_for_level(new_level + 1)
            if new_xp >= xp_needed_for_next:
                new_level += 1
                leveled_up = True
            else:
                break

        # Se passou de 100, trava no 100
        if new_level > 100:
            new_level = 100
            new_xp = self._calculate_xp_for_level(100)

        # Se upou de level, recalcula os Stats
        update_dict = {
            "total_xp": new_xp,
            "level": new_level
        }

        pokemon_obj = CaughtPokemonModel.from_dict(pokemon_data)
        pokemon_obj.level = new_level 
        
        # Recalcula stats
        new_stats = pokemon_obj.calculate_current_stats(base_stats_data["base_stats"])
        update_dict["stats"] = new_stats

        # Salva no Banco de Dados
        await self.bot.db.caught_pokemons.update_one(
            {"_id": pokemon_id},
            {"$set": update_dict}
        )

        return {
            "leveled_up": leveled_up,
            "new_level": new_level,
            "pokemon_name": pokemon_data["species_name"]
        }