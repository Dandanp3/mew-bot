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
        self.ivs = {stat: random.randint(0, 31) for stat in ["hp", "attack", "defense", "special_attack", "special_defense", "speed"]}
        
        # calculo de ivs %
        self.iv_percentage = round((sum(self.ivs.values()) / 186) * 100, 2)
        
        # EVs começam em 0
        self.evs = {stat: 0 for stat in ["hp", "attack", "defense", "special_attack", "special_defense", "speed"]}
        
        self.caught_at = datetime.utcnow()
    
    def _calculate_xp_for_level(self, level: int) -> int:
        # Fórmula de n^3
        return int(level ** 3)
    
    def calculate_current_stats(self, base_stats: Dict[str, int]) -> Dict[str, int]:
        # Calcula os status reais aplicando IVs, EVs, lvl e nature
        final_stats = {}
        nature_mod = NATURES_DATA.get(self.nature)
        
        for stat, base in base_stats.items():
            iv = self.ivs.get(stat, 0)
            ev = self.evs.get(stat, 0)
            
            if stat == "hp":
                value = math.floor(((2 * base + iv + (ev // 4)) * self.level) / 100) + self.level + 10
                final_stats[stat] = value
            else:
                modifier = 1.0
                if nature_mod["buff"] == stat: modifier = 1.1
                if nature_mod["debuff"] == stat: modifier = 0.9
                
                core_calc = math.floor(((2 * base + iv + (ev // 4)) * self.level) / 100) + 5
                final_stats[stat] = math.floor(core_calc * modifier)      
        return final_stats     

    def to_dict(self):
        return {
            "owner_id": self.owner_id,
            "species_id": self.species_id,
            "name": self.name,
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