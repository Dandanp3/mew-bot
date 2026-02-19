import math
import random
from datetime import datetime
from typing import Dict, Optional, List
from server.config.natures import NATURES_DATA

class CaughtPokemonModel:
    def __init__(self,
                 owner_id: int,
                 species_id: int,
                 species_name: str,
                 catch_order: int,
                 level: Optional[int] = None,
                 nickname: str = None,
                 initial_moves: List[str] = None):
        
        self.owner_id = owner_id
        self.species_id = species_id
        self.name = species_name
        self.nickname = nickname
        self.catch_order = catch_order
        
        # Lvl aleatório de 1-40 ou definido (ex: inicial)
        self.level = level if level is not None else random.randint(1, 40)
        self.total_xp = self._calculate_xp_for_level(self.level)
        
        # Lista de moves 
        self.moves = initial_moves if initial_moves else []
        
        # Lógica shiny (0.2% de chance)
        self.is_shiny = random.randint(1, 500) == 1
        
        # Sorteando nature e IVs 
        self.nature = random.choice(list(NATURES_DATA.keys()))
        
        self.ivs = {stat: random.randint(0, 31) for stat in ["hp", "attack", "defense", "sp_atk", "sp_def", "speed"]}
        
        # calculo de ivs %
        self.iv_percentage = round((sum(self.ivs.values()) / 186) * 100, 2)
        
        # EVs começam em 0
        self.evs = {stat: 0 for stat in ["hp", "attack", "defense", "sp_atk", "sp_def", "speed"]}
        
        self.caught_at = datetime.utcnow()
    
    def _calculate_xp_for_level(self, level: int) -> int:
        # Fórmula de n^3
        return int(level ** 3)
    
    def calculate_current_stats(self, base_stats: Dict[str, int]) -> Dict[str, int]:
        final_stats = {}
        nature_mod = NATURES_DATA.get(self.nature)
        
        # Mapeamento para garantir que o resultado final use nomes curtos
        stat_map = {
            "hp": "hp",
            "attack": "attack",
            "defense": "defense",
            "special-attack": "sp_atk",
            "special_attack": "sp_atk", # Caso venha com underscore
            "special-defense": "sp_def",
            "special_defense": "sp_def", # Caso venha com underscore
            "speed": "speed"
        }
        
        for api_name, base in base_stats.items():
            # Traduz o nome da API para o seu padrão (sp_atk, etc)
            my_stat_name = stat_map.get(api_name, api_name)
            
            iv = self.ivs.get(my_stat_name, 0)
            ev = self.evs.get(my_stat_name, 0)
            
            if my_stat_name == "hp":
                value = math.floor(((2 * base + iv + (ev // 4)) * self.level) / 100) + self.level + 10
                final_stats[my_stat_name] = value
            else:
                modifier = 1.0
                if nature_mod["buff"] == my_stat_name: modifier = 1.1
                if nature_mod["debuff"] == my_stat_name: modifier = 0.9
                
                core_calc = math.floor(((2 * base + iv + (ev // 4)) * self.level) / 100) + 5
                final_stats[my_stat_name] = math.floor(core_calc * modifier)      
                
        return final_stats   

    def to_dict(self):
        return {
            "owner_id": self.owner_id,
            "species_id": self.species_id,
            "species_name": self.name,
            "nickname": self.nickname,
            "catch_order": self.catch_order,
            "level": self.level,
            "is_shiny": self.is_shiny,
            "total_xp": self.total_xp,
            "nature": self.nature,
            "ivs": self.ivs,
            "iv_percentage": self.iv_percentage,
            "evs": self.evs,
            "moves": self.moves, 
            "caught_at": self.caught_at
        }