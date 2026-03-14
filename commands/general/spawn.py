import discord
from discord.ext import commands
from random import randint
import random
import json
import requests



class PokemonSpawn(commands.Cog):
    def __init__(self, bot, controller):
        self.bot = bot
        self.controller = controller
        self.spawns = {}
        
        # Pegando os lendários disponiveis
        try:
            with open('legendaries.json', 'r') as f:
                self.legendaries = json.load(f)
        except Exception as e:
            print(f"⚠️ Erro ao carregar legendaries.json: {e}")
            self.legendaries = []
            
    def get_pokemon_data(self, pokemon_id_or_name):
        url = f"https://pokeapi.co/api/v2/pokemon/{str(pokemon_id_or_name).lower()}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return None

    async def increment_message(self, server_id):
        # Inicializa o cache do servidor se n existir
        if server_id not in self.spawns:
            channel_id = await self.controller.get_chat_id(server_id)
            self.spawns[server_id] = {
                "current": 0,
                "target": 2, 
                "channel_id": channel_id
            }

        server_spawn = self.spawns[server_id]
        server_spawn["current"] += 1

        # Contador
        if server_spawn["current"] >= server_spawn["target"]:
            server_spawn["current"] = 0
            server_spawn["target"] = randint(1, 3)
            
            pokemon_data = None
            
            # Sortear pokemons
            is_legendary_roll = randint(1, 5) <= 2
            # sorteio shiny 2% por enquanto
            is_shiny = randint(1, 2) == 1 
            
            # escolhendo o pokemon
            # pega um lendario da lista se for verdade
            if is_legendary_roll:
                pokemon_name = random.choice(self.legendaries)
                pokemon_data = self.get_pokemon_data(pokemon_name)
                # pegar o ID na API dps
            else:
                while True:
                    possible_id = randint(1, 151)
                    data = self.get_pokemon_data(possible_id)
                    
                    # Verificando se nao eh lendario
                    if data and data['name'].lower() not in [n.lower() for n in self.legendaries]:
                        pokemon_data = data
                        break
            
            # enviar para o dc
            if pokemon_data:
                name = pokemon_data['name'].capitalize()
                # pega a imagem shiny ou normal
                gen5_sprites = pokemon_data['sprites']['versions']['generation-v']['black-white']['animated']
            
                if is_shiny:
                    sprite_url = gen5_sprites['front_shiny'] or pokemon_data['sprites']['front_shiny']
                else:
                    sprite_url = gen5_sprites['front_default'] or pokemon_data['sprites']['front_default']

                status = "UM POKEMON SHINY APARECEU" if is_shiny else "Um pokemon selvagem apareceu"
                if is_legendary_roll:
                    status = f"UM LENDARIO APARECEU"
                
                channel = self.bot.get_channel(server_spawn["channel_id"]) or \
                          await self.bot.fetch_channel(server_spawn["channel_id"])
                          
                if channel:
                    embed = discord.Embed(title=status, description=f"É um {name}")
                    embed.set_image(url=sprite_url)
                    await channel.send(embed=embed)
                
                
                
                
            

    @commands.Cog.listener()
    async def on_message(self, message):
        # ignora ele e outros bots
        if message.author.bot or not message.guild:
            return
            
        await self.increment_message(message.guild.id)
    
    


async def setup(bot):
    await bot.add_cog(PokemonSpawn(bot, bot.server_controller))