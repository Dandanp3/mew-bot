import discord
from discord.ext import commands
from random import randint
import random
import json
import requests

class PokemonSpawn(commands.Cog):
    def __init__(self, bot, server_controller, spawn_controller):
        self.bot = bot
        self.server_controller = server_controller
        self.spawn_controller = spawn_controller
        self.spawns = {}
        self.admin_id = 505806599034765323
        self.active_spawns = {}  
        
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

    async def send_spawn_message(self, channel, pokemon_data, is_shiny=False, is_legendary=False):
        name = pokemon_data['name'].capitalize()
        
        # ✅ NOVO: Obter configuração do Pokémon (x, y, bg)
        pokemon_config = self.spawn_controller.get_pokemon_config(pokemon_data['name'])
        
        # ✅ NOVO: Usar o background definido em coords.py
        caminho_bg = self.spawn_controller.get_background_path(pokemon_config['bg'])
        
        if not caminho_bg:
            print(f"⚠️ Aviso: Background '{pokemon_config['bg']}' não encontrado para {name}")
            return
        
        # Obter sprite do Pokémon
        caminho_pokemon = self.spawn_controller.get_image_data(pokemon_data, is_shiny)
        
        # Criar GIF final (passa pokemon_name para pegar coordenadas)
        gif_final_bytes = self.spawn_controller.create_final_spawn_gif(
            caminho_pokemon, 
            caminho_bg, 
            pokemon_data['name']
        )
        
        if is_legendary:
            status = "✨ UM LENDÁRIO APARECEU ✨"
        elif is_shiny:
            status = "🌟 UM POKÉMON SHINY APARECEU 🌟"
        else:
            status = "Um pokémon selvagem apareceu!"
            
        arquivo_discord = discord.File(fp=gif_final_bytes, filename="pokemon_spawn.gif")
        embed = discord.Embed(title=status, description=f"É um {name}!", color=discord.Color.random())
        embed.set_image(url="attachment://pokemon_spawn.gif")
        
        await channel.send(embed=embed, file=arquivo_discord)
        

    async def increment_message(self, server_id):
        if server_id not in self.spawns:
            channel_id = await self.server_controller.get_chat_id(server_id)
            self.spawns[server_id] = {
                "current": 0,
                "target": 3, 
                "channel_id": channel_id
            }

        server_spawn = self.spawns[server_id]
        server_spawn["current"] += 1

        if server_spawn["current"] >= server_spawn["target"]:
            server_spawn["current"] = 0
            server_spawn["target"] = randint(1, 3) 
            
            # Sorteios
            is_legendary = randint(1, 1000) <= 2
            is_shiny = randint(1, 2) 
            
            if is_legendary:
                pkm_name = random.choice(self.legendaries)
                pokemon_data = self.get_pokemon_data(pkm_name)
                self.active_spawns[server_id] = {
                    "name": pkm_name,
                    "shiny": is_shiny
                }
            else:
                while True:
                    data = self.get_pokemon_data(randint(1, 151))
                    if data and data['name'].lower() not in [n.lower() for n in self.legendaries]:
                        pokemon_data = data
                        self.active_spawns[server_id] = {
                            "name": data['name'],
                            "shiny": is_shiny
                        }
                        break

            channel = self.bot.get_channel(server_spawn["channel_id"]) or \
                      await self.bot.fetch_channel(server_spawn["channel_id"])
            
            if channel:
                await self.send_spawn_message(channel, pokemon_data, is_shiny, is_legendary)
        
    # Comando de captura
    @commands.command(name="catch")
    async def catch_command(self, ctx, *, pokemon_name: str):
        pokemon_name = pokemon_name.strip().lower()
        trainer = await self.bot.trainer_controller.get_trainer(ctx.author.id)
        
        if ctx.guild.id in self.active_spawns:
            spawn_data = self.active_spawns[ctx.guild.id]
            # compara o pokemon com o dicionario de pokemons spawnados em servidores
            if pokemon_name == spawn_data["name"].lower():
                # limpa o pokemon do dict do server atual
                if spawn_data["shiny"]:
                    await ctx.send(f"{ctx.author.mention} Congratulations! You cauptured a **SHINY** {pokemon_name}!")
                else:
                    await ctx.send(f"{ctx.author.mention} Congratulations! You cauptured a {pokemon_name}!")
                del self.active_spawns[ctx.guild.id]
                
            else:
                await ctx.send("Wrong pokemon.")
                
            
        
    
    
    # comando admin pokespawn
    @commands.command(name="pokespawn")
    async def force_spawn(self, ctx, pokemon_name: str):
        # Verifica ID
        if ctx.author.id != self.admin_id:
            return # Simplesmente ignora 

        pokemon_data = self.get_pokemon_data(pokemon_name)
        
        if not pokemon_data:
            return await ctx.send(f"❌ Pokémon '{pokemon_name}' não encontrado na PokeAPI.")

        # Verifica se é lendário ou shiny 
        is_legendary = pokemon_data['name'].lower() in [n.lower() for n in self.legendaries]
        
        await self.send_spawn_message(ctx.channel, pokemon_data, is_shiny=False, is_legendary=is_legendary)

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignora bots e DMs
        if message.author.bot or not message.guild:
            return
            
        # NÃO soma se for um comando do bot 
        prefix = await self.bot.get_prefix(message)
        if isinstance(prefix, list): 
            if any(message.content.startswith(p) for p in prefix):
                return
        elif message.content.startswith(prefix):
            return
            
        await self.increment_message(message.guild.id)

async def setup(bot):
    await bot.add_cog(PokemonSpawn(bot, bot.server_controller, bot.spawn_controller))