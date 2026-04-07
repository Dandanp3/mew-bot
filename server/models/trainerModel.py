from datetime import datetime
from typing import Dict, List, Optional

class TrainerModel:
    def __init__(self,
                 discord_id: str,
                 username: str):
        
        self.discord_id = discord_id # "Chave primaria" no mongo
        self.username = username
        
        # | Economia/progressao
        self.pokedollars = 0
        self.joined_at = datetime.utcnow()
        
        # Level
        self.level = 1
        self.xp = 0
        self.xp_to_next_level = self._calculate_xp_required(self.level)
        
        # | gestão de party
        self.selected_pokemon_id: Optional[str] = None
        
        # coleçao
        self.total_caught = 0
        self.pokedex_ids = []
        
        # | inventario
        self.inventory: Dict[str, int] = {}
        
        # | Contador para futuras tasks
        self.region_counts = {
            "Kanto": 0, "Johto": 0, "Hoenn": 0,
            "Sinnoh": 0, "Unova": 0
        }
        self.type_counts = {
            "Normal": 0, "Fire": 0, "Water": 0, "Grass": 0, "Electric": 0, 
            "Ice": 0, "Fighting": 0, "Poison": 0, "Ground": 0, "Flying": 0, 
            "Psychic": 0, "Bug": 0, "Rock": 0, "Ghost": 0, "Dragon": 0, 
            "Steel": 0, "Dark": 0, "Fairy": 0
        }
        
    def _calculate_xp_required(self, level: int) -> int:
        # Soma 500xp base + 250xp a cada lvl
        return 500 + (level * 250)
    
    @property
    def pokedex_completion(self):
        # retornar pokemons UNICOS do treinador
        return len(self.pokedex_ids)
    
    def add_xp(self, amount: int) -> bool:
        self.xp += amount
        leveled_up = False
        
        while self.xp >= self.xp_to_next_level:
            self.xp -= self.xp_to_next_level
            self.level += 1
            self.xp_to_next_level = self._calculate_xp_required(self.level)
            leveled_up = True
        return leveled_up
    
    def register_catch(self, pokemon_species_id: int, region: str, types: list[str]):
        self.total_caught += 1
        
        #Atualizando pokedex
        if pokemon_species_id not in self.pokedex_ids:
            self.pokedex_ids.append(pokemon_species_id)
            
        # Atualizando contador de regioes
        if region in self.region_counts:
            self.region_counts[region] += 1
        else:
            # Caso add regiao nova
            self.region_counts.setdefault(region, 0)
            self.region_counts[region] += 1
            
        # Atualizando tipos
        for t in types:
            t_cap = t.capitalize()
            if t_cap in self.type_counts:
                self.type_counts[t_cap] += 1
    
    def to_dict(self):
        return {
            "_id": self.discord_id,
            "username": self.username,
            "joined_at": self.joined_at,
            "pokedollars": self.pokedollars,
            "level": self.level,
            "xp": self.xp,
            "xp_to_next_level": self.xp_to_next_level,
            "selected_pokemon_id": self.selected_pokemon_id,  
            "total_caught": self.total_caught,
            "pokedex_ids": self.pokedex_ids,
            "pokedex_count": len(self.pokedex_ids),
            "inventory": self.inventory,
            
            "stats": {
                "regions": self.region_counts,
                "types": self.type_counts
            }
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        trainer = cls(
            discord_id=data.get("_id") or data.get("discord_id"),
            username=data.get("username", "Unknown")
        )
        
        trainer.pokedollars = data.get("pokedollars", 0)
        trainer.level = data.get("level", 1)
        trainer.xp = data.get("xp", 0)
        trainer.xp_to_next_level = data.get("xp_to_next_level", 750)
        trainer.total_caught = data.get("total_caught", 0)
        trainer.pokedex_ids = data.get("pokedex_ids", [])
        trainer.inventory = data.get("inventory", {})
        trainer.selected_pokemon_id = data.get("selected_pokemon_id")  # ✅ CORRIGIDO
        
        stats = data.get("stats", {})
        trainer.region_counts = stats.get("regions", trainer.region_counts)
        trainer.type_counts = stats.get("types", trainer.type_counts)
        
        return trainer