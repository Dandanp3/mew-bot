import discord
from discord.ext import commands
from random import randint
import random
import json
import os
import aiohttp
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
            if os.path.exists('legendaries.json'):
                with open('legendaries.json', 'r') as f:
                    self.legendaries = json.load(f)
            else:
                self.legendaries = []
        except Exception as e:
            print(f"⚠️ Erro ao carregar legendaries.json: {e}")
            self.legendaries = []

    async def get_pokemon_data(self, name_or_id):
        query = {}
        if isinstance(name_or_id, int) or name_or_id.isdigit():
            query = {"_id": int(name_or_id)}
        else:
            # Busca ignorando maiúsculas/minúsculas
            query = {"name": name_or_id.capitalize()}
            
        return await self.pokemon_collection.find_one(query)

    async def send_spawn_message(self, channel, pokemon_data, is_shiny=False, is_legendary=False):
        name = pokemon_data['name'].capitalize()
        pokemon_config = self.spawn_controller.get_pokemon_config(pokemon_data['name'])
        caminho_bg = self.spawn_controller.get_background_path(pokemon_config['bg'])
        
        if not caminho_bg:
            print(f"⚠️ Background '{pokemon_config['bg']}' não encontrado para {name}")
            return
        
        caminho_pokemon = self.spawn_controller.get_image_data(pokemon_data, is_shiny)
        gif_final_bytes = self.spawn_controller.create_final_spawn_gif(
            caminho_pokemon, 
            caminho_bg, 
            pokemon_data['name']
        )
            
        arquivo_discord = discord.File(fp=gif_final_bytes, filename="pokemon_spawn.gif")
        embed = discord.Embed(title="Wild pokemon", color=discord.Color.random())
        embed.set_image(url="attachment://pokemon_spawn.gif")
        
        await channel.send(embed=embed, file=arquivo_discord)

    async def increment_message(self, server_id):
        if server_id not in self.spawns:
            channel_id = await self.server_controller.get_chat_id(server_id)
            self.spawns[server_id] = {"current": 0, "target": 10, "channel_id": channel_id}

        server_spawn = self.spawns[server_id]
        server_spawn["current"] += 1

        if server_spawn["current"] >= server_spawn["target"]:
            server_spawn["current"] = 0
            server_spawn["target"] = randint(15, 40) 
            
            is_legendary = randint(1, 500) == 1
            is_shiny = randint(1, 2000) == 1 
            
            if is_legendary and self.legendaries:
                pkm_name = random.choice(self.legendaries)
                pokemon_data = await self.get_pokemon_data(pkm_name)
            else:
                while True:
                    random_id = randint(1, 251)
                    pokemon_data = await self.get_pokemon_data(random_id)
                    if pokemon_data and pokemon_data['name'].lower() not in [n.lower() for n in self.legendaries]:
                        break

            if pokemon_data:
                self.active_spawns[server_id] = {
                    "name": pokemon_data['name'],
                    "shiny": is_shiny  
                }

                channel = self.bot.get_channel(server_spawn["channel_id"])
                if not channel:
                    try: channel = await self.bot.fetch_channel(server_spawn["channel_id"])
                    except: return

                await self.send_spawn_message(channel, pokemon_data, is_shiny, is_legendary)
        
    @commands.command(name="catch")
    async def catch_command(self, ctx, *, pokemon_name: str):
        pokemon_name = pokemon_name.strip().lower()
        trainer_data = await self.bot.trainer_controller.get_trainer(ctx.author.id)
        
        if not trainer_data:
            return await ctx.send("❌ Você precisa iniciar sua jornada primeiro! Use `p!start`.")
        
        trainer = TrainerModel.from_dict(trainer_data)
        
        if ctx.guild.id in self.active_spawns:
            # Verifica se o nome está certo ANTES de mexer no dicionário
            if pokemon_name == self.active_spawns[ctx.guild.id]["name"].lower():
                spawn_data = self.active_spawns.pop(ctx.guild.id)
                
                # Agora sim fazemos as consultas demoradas (awaits)
                pokemon_base = await self.get_pokemon_data(pokemon_name)
                if not pokemon_base: 
                    return
                
                pokemon_id = pokemon_base["_id"]
                # Definição de região baseada no ID
                region = "Kanto" if pokemon_id <= 151 else "Johto"
                
                trainer.register_catch(pokemon_id, region, pokemon_base["types"])
                level_sorteado = random.randint(1, 40)
                
                await self.bot.catch_controller.create_specific_pokemon(
                    owner_id=ctx.author.id,
                    species_id=pokemon_id,
                    level=level_sorteado,
                    is_shiny=spawn_data["shiny"]  
                )
                
                await self.bot.trainer_controller.update_trainer(trainer)
                
                status_shiny = "✨ **SHINY** " if spawn_data["shiny"] else ""
                await ctx.send(f"{ctx.author.mention} Congratulations! You captured a {status_shiny}**{spawn_data['name'].capitalize()}** level {level_sorteado}!")
                
            else:
                await ctx.send("Wrong pokemon.")
        else:
            pass

    @commands.command(name="pokespawn")
    async def force_spawn(self, ctx, pokemon_name: str, status: str = ""):
        if ctx.author.id != self.admin_id:
            return 

        # Ativa o "Digitando..." para evitar o erro 503/Timeout
        async with ctx.typing():
            pokemon_data = await self.get_pokemon_data(pokemon_name)
            
            if not pokemon_data:
                return await ctx.send(f"❌ Pokémon `{pokemon_name}` não encontrado no Banco de Dados.")

            # Verifica se você digitou "shiny" após o nome do pokemon
            is_shiny = status.lower() == "shiny"
            
            is_legendary = pokemon_data['name'].lower() in [n.lower() for n in self.legendaries]
            
            # Registra no spawn ativo para poder ser capturado corretamente
            self.active_spawns[ctx.guild.id] = {
                "name": pokemon_data['name'],
                "shiny": is_shiny
            }

            # Envia a mensagem (o processamento do GIF acontece aqui dentro)
            await self.send_spawn_message(
                ctx.channel, 
                pokemon_data, 
                is_shiny=is_shiny, 
                is_legendary=is_legendary
            )

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
            
        prefix = await self.bot.get_prefix(message)
        if message.content.startswith(prefix):
            return
            
        await self.increment_message(message.guild.id)

async def setup(bot):
    await bot.add_cog(PokemonSpawn(bot, bot.server_controller, bot.spawn_controller))