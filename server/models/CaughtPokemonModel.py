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
                 gender: str = None, 
                 initial_moves: List[str] = None,
                 is_shiny: bool = False):
        
        self.owner_id = owner_id
        self.species_id = species_id
        self.name = species_name
        self.nickname = nickname
        self.catch_order = catch_order
    
        if gender:
            self.gender = gender
        else:
            self.gender = random.choice(["Male", "Female"])
        
        # Lvl aleatório de 1-40
        self.level = level if level is not None else random.randint(1, 40)
        self.total_xp = self._calculate_xp_for_level(self.level)
        
        # Lista de moves 
        self.moves = initial_moves if initial_moves else []
        
        self.is_shiny = is_shiny
        
        # Sorteando nature e IVs 
        self.nature = random.choice(list(NATURES_DATA.keys()))
        
        self.ivs = {stat: random.randint(0, 31) for stat in ["hp", "attack", "defense", "sp_atk", "sp_def", "speed"]}
        
        # Cálculo de ivs % 
        self.iv_percentage = round((sum(self.ivs.values()) / 186) * 100, 2)
        
        # EVs começam em 0
        self.evs = {stat: 0 for stat in ["hp", "attack", "defense", "sp_atk", "sp_def", "speed"]}
        
        self.caught_at = datetime.utcnow()

    def _calculate_xp_for_level(self, level: int) -> int:
        return int(math.pow(level, 3))

    def calculate_current_stats(self, base_stats: Dict[str, int]) -> Dict[str, int]:
        stats = {}
        nature_data = NATURES_DATA.get(self.nature, {})
        
        # Mapping dos nomes dos stats da API para internos
        stat_mapping = {
            "hp": "hp",
            "attack": "attack",
            "defense": "defense",
            "sp_atk": "special_attack",
            "sp_def": "special_defense",
            "speed": "speed"
        }
        
        for stat_key, base_stat_key in stat_mapping.items():
            base_stat = base_stats.get(base_stat_key, 0)
            iv = self.ivs.get(stat_key, 0)
            ev = self.evs.get(stat_key, 0)
            
            if stat_key == "hp":
                # Fórmula do HP 
                stat_value = int(((2 * base_stat + iv + (ev / 4)) * self.level / 100) + self.level + 5)
            else:
                # Formula dos outros stats
                stat_value = int(((2 * base_stat + iv + (ev / 4)) * self.level / 100) + 5)
                
                # Aplicar modificador da nature (buff/debuff)
                if nature_data.get("buff") == stat_key:
                    stat_value = int(stat_value * 1.1)  # +10% de boost
                elif nature_data.get("debuff") == stat_key:
                    stat_value = int(stat_value * 0.9)  # -10% de redução
            
            # Mínimo de 1 para garantir que nenhum stat seja 0
            stats[stat_key] = max(1, stat_value)
        
        return stats

    def to_dict(self):
        return {
            "owner_id": self.owner_id,
            "species_id": self.species_id,
            "species_name": self.name,
            "nickname": self.nickname,
            "gender": self.gender, 
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