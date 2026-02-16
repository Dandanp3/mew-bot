from typing import List, Dict, Union, Optional

class PokemonBaseModel:
    def __init__(self, 
                 id: int, 
                 name: str, 
                 types: List[str], 
                 stats: Dict[str, int], 
                 moves: Dict[str, List[Dict[str, Union[str, int]]]], 
                 abilities: List[str],
                 evolutions: List[Dict] = [],
                 sprites: Dict[str, str] = {} 
                 ):
        
        self._id = id  
        self.name = name
        self.types = types
        self.stats = stats
        self.abilities = abilities
        self.moves = moves
        self.evolutions = evolutions
        self.sprites = sprites

    def to_dict(self):
        return {
            "_id": self._id,
            "name": self.name,
            "types": self.types,
            "stats": self.stats,
            "abilities": self.abilities,
            "moves": self.moves,
            "evolutions": self.evolutions,
            "sprites": self.sprites
        }
