import math
import random
from datetime import datetime
from typing import Dict, Optional
from server.config.natures import NATURES_DATA

class CaughtPokemonModel:
    def __init__(self,
                 owner_id: int,
                 species_id: int,
                 species_name: str,
                 catch_order: int,
                 level: Optional[int] = None,
                 nickname: str = None):
        
        self.owner_id = owner_id
        self.species_id = species_id
        self.name = species_name
        self.nickname = nickname
        self.catch_order = catch_order
        
        # Lvl aleatorio de 1-40
        self.level = level if level is not None else random.randint(1, 40)
        # Xp total acumulado
        #self.total_xp = self._calculate_xp_for_level(self.level)
        
        # Sorteando nature e IVS
        self.nature = random.choice(list(NATURES_DATA.keys()))
        self.ivs = {stat: random.randint(0, 31) for stat in ["hp", "attack", "defense", "special_attack", "special_defense", "speed",]}
        # mostrando porcentagem dos IVs
        self.iv_percentage = round((sum(self.ivs.values()) / 186) * 100, 2)
        
        # Evs começa em 0
        self.evs = {stat: 0 for stat in ["hp", "attack", "defense", "special_attack", "special_defense", "speed",]}
        self.caught_at = datetime.utcnow
    
    def _calculate_xp_for_level(self, level: int) -> int:
        # Fórmuma n^3
        return int(level ** 3)
    
    def calculate_current_stats(self, base_stats: Dict[str, int]) -> Dict[str, int]:
        
        final_stats = {}
        nature_mod = NATURES_DATA.get(self.nature)
        
        for stat, base in base_stats.items():
            iv = self.ivs.get(stat, 0)
            ev = self.evs.get(stat, 0)
            
        if stat == "hp":
            value = math.floor(((2 * base + iv + (ev // 4)) * self.level) / 100) + self.level + 10
            final_stats[stat] = value