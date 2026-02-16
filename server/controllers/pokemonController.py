import requests
import os
import certifi
from pymongo import MongoClient
from dotenv import load_dotenv
from server.models.pokemonsModel import PokemonBaseModel

load_dotenv()

class PokemonController:
    def __init__(self):
        ca = certifi.where()
        self.client = MongoClient(os.getenv('MONGO_TOKEN'), tlsCAFile=ca)
        self.db = self.client['mew_bot']
        self.collection = self.db['pokemons']

    def get_evolution_data(self, pokemon_id):
        try:
            species_res = requests.get(f"https://pokeapi.co/api/v2/pokemon-species/{pokemon_id}/").json()
            evo_url = species_res.get('evolution_chain', {}).get('url')
            if not evo_url: return []

            chain_data = requests.get(evo_url).json().get('chain', {})
            evolutions = []
            
            def parse_chain(node):
                if not node: return
                if node.get('species', {}).get('name') == species_res.get('name'):
                    for evo in node.get('evolves_to', []):
                        details = evo.get('evolution_details', [{}])[0]
                        evolutions.append({
                            "target": evo.get('species', {}).get('name', '').capitalize(),
                            "trigger": details.get('trigger', {}).get('name', 'level-up'),
                            "min_level": details.get('min_level'),
                            "item": details.get('item', {}).get('name') if details.get('item') else None
                        })
                for next_node in node.get('evolves_to', []):
                    parse_chain(next_node)

            parse_chain(chain_data)
            return evolutions
        except Exception as e:
            print(f"Erro na evolução do ID {pokemon_id}: {e}")
            return []

    async def seed_kanto(self):
        print("🚀 Iniciando importação de Kanto com Sprites Completos (151 Pokémons)...")
        
        for i in range(1, 152):
            try:
                if self.collection.find_one({"_id": i}):
                    print(f"ID {i} já existe, pulando...")
                    continue

                res = requests.get(f"https://pokeapi.co/api/v2/pokemon/{i}").json()
                
                # Stats
                stats = {s['stat']['name'].replace('-', '_'): s['base_stat'] for s in res['stats']}
                
                # Tipos e Habilidades
                types = [t['type']['name'].capitalize() for t in res['types']]
                abilities = [a['ability']['name'].capitalize() for a in res['abilities']]
                
                # Moves (Level-up na Gen 5)
                level_up_moves = []
                for m in res.get('moves', []):
                    for detail in m.get('version_group_details', []):
                        if detail['version_group']['name'] == 'black-white' and \
                           detail['move_learn_method']['name'] == 'level-up':
                            level_up_moves.append({
                                "name": m['move']['name'].replace('-', ' ').title(),
                                "level": detail['level_learned_at']
                            })
                
                level_up_moves = sorted(level_up_moves, key=lambda x: x['level'])

                # Evoluções
                evolutions = self.get_evolution_data(i)

                gen5_path = res['sprites']['versions']['generation-v']['black-white']['animated']
                
                sprites_map = {
                    "front": gen5_path['front_default'],
                    "back": gen5_path['back_default'],
                    "front_shiny": gen5_path['front_shiny'],
                    "back_shiny": gen5_path['back_shiny']
                }

                # Criando o objeto com o novo Model
                pokemon = PokemonBaseModel(
                    id=i,
                    name=res['name'].capitalize(),
                    types=types,
                    stats=stats,
                    moves={"level_up": level_up_moves},
                    abilities=abilities,
                    evolutions=evolutions,
                    sprites=sprites_map
                )

                self.collection.insert_one(pokemon.to_dict())
                print(f"✅ {pokemon.name} (# {i}) importado com sucesso!")

            except Exception as e:
                print(f"❌ Erro ao importar ID {i}: {e}")

        print("✨ Database atualizada com novos sprites!")