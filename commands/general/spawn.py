import discord
from discord.ext import commands
from random import randint
import random
import json
import requests
from server.models.caughtPokemonModel import CaughtPokemonModel
from server.models.trainerModel import TrainerModel

class PokemonSpawn(commands.Cog):
    def __init__(self, bot, server_controller, spawn_controller):
        self.bot = bot
        self.pokemon_collection = bot.db['pokemons']
        self.caught_collection = bot.db['caught_pokemons']
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
            

    async def send_spawn_message(self, channel, pokemon_data, is_shiny=False, is_legendary=False):
        name = pokemon_data['name'].capitalize()
        
        pokemon_config = self.spawn_controller.get_pokemon_config(pokemon_data['name'])
        

        caminho_bg = self.spawn_controller.get_background_path(pokemon_config['bg'])
        
        if not caminho_bg:
            print(f"⚠️ Aviso: Background '{pokemon_config['bg']}' não encontrado para {name}")
            return
        
        # Obter sprite do Pokémon
        caminho_pokemon = self.spawn_controller.get_image_data(pokemon_data, is_shiny)
        
        # Criar GIF final
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
            is_shiny = randint(1, 2) == 1  # eh true se cair 1
            
            if is_legendary:
                pkm_name = random.choice(self.legendaries)
                pokemon_data = self.get_pokemon_data(pkm_name)
                self.active_spawns[server_id] = {
                    "name": pkm_name,
                    "shiny": is_shiny  # ✅ Agora é boolean (True/False)
                }
            else:
                while True:
                    random_id = randint(1, 151)
                    data = await self.pokemon_collection.find_one({"_id": random_id}) 
                    if data and data['name'].lower() not in [n.lower() for n in self.legendaries]:
                        pokemon_data = data
                        self.active_spawns[server_id] = {
                            "name": data['name'],
                            "shiny": is_shiny  # ✅ Agora é boolean (True/False)
                        }
                        break

            channel = self.bot.get_channel(server_spawn["channel_id"]) or \
                      await self.bot.fetch_channel(server_spawn["channel_id"])
            
            if channel:
                await self.send_spawn_message(channel, pokemon_data, is_shiny, is_legendary)
        
    @commands.command(name="catch")
    async def catch_command(self, ctx, *, pokemon_name: str):
        pokemon_name = pokemon_name.strip().lower()
        
        # Pega os dados do banco
        trainer_data = await self.bot.trainer_controller.get_trainer(ctx.author.id)
        
        if not trainer_data:
            return await ctx.send("❌ Você precisa iniciar sua jornada primeiro! Use !start.")
        trainer = TrainerModel.from_dict(trainer_data)
        
        if ctx.guild.id in self.active_spawns:
            spawn_data = self.active_spawns[ctx.guild.id]
            
            if pokemon_name == spawn_data["name"].lower():
                pokemon_name_formatado = pokemon_name.capitalize()
                
                # Busca os dados base do pokémon
                pokemon_base = await self.pokemon_collection.find_one({"name": pokemon_name_formatado})
                
                if not pokemon_base:
                    return await ctx.send("Pokémon não encontrado no banco de dados!")
                
                pokemon_id = pokemon_base["_id"]
                pokemon_types = pokemon_base["types"]
                
                # Logica de Regiao
                if pokemon_id <= 151: region = "Kanto"
                elif pokemon_id <= 251: region = "Johto"
                elif pokemon_id <= 386: region = "Hoenn"
                elif pokemon_id <= 493: region = "Sinnoh"
                else: region = "Unova"
                
                # registra a captura 
                trainer.register_catch(pokemon_id, region, pokemon_types)
                level_sorteado = random.randint(1, 40)
                
                await self.bot.catch_controller.create_specific_pokemon(
                    owner_id=ctx.author.id,
                    species_id=pokemon_id,
                    level=level_sorteado,
                    is_shiny=spawn_data["shiny"]  # ✅ NOVO: Passa is_shiny
                )
                
                #salva o treinador atualizado no banco
                await self.bot.trainer_controller.update_trainer(trainer)
                
                # Mensagem de sucesso
                status_shiny = "**SHINY** " if spawn_data["shiny"] else ""
                await ctx.send(f"{ctx.author.mention} Congratulations! You captured a {status_shiny}{pokemon_name_formatado} level {level_sorteado}! (Nº {trainer.total_caught})")
                
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