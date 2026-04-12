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
        
        self.cache_channels = {
            "Kanto": 1492555040550948904, 
            "Johto": 1492555060679544943, 
            "Hoenn": 1492555081965371495, 
            "Sinnoh": 1492555101213167798, 
            "Unova": 1492555120813146192  
        }
        
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
        if isinstance(name_or_id, int) or str(name_or_id).isdigit():
            query = {"_id": int(name_or_id)}
        else:
            query = {"name": name_or_id.capitalize()}
            
        return await self.pokemon_collection.find_one(query)

    async def send_spawn_message(self, channel, pokemon_data, is_shiny=False, is_legendary=False):
        pokemon_name = pokemon_data['name']
        pokemon_id = pokemon_data['_id']
        region = self.spawn_controller.get_region_folder(pokemon_id)
        
        cached_url = self.spawn_controller.get_cached_url(region, pokemon_name, is_shiny)
        
        embed = discord.Embed(title="Wild pokemon", color=discord.Color.random())
        
        if cached_url:
            embed.set_image(url=cached_url)
            await channel.send(embed=embed)
            return

        pokemon_config = self.spawn_controller.get_pokemon_config(pokemon_name)
        caminho_bg = self.spawn_controller.get_background_path(pokemon_config['bg'])
        
        if not caminho_bg:
            print(f"⚠️ Background '{pokemon_config['bg']}' não encontrado para {pokemon_name}")
            return
        
        frames_pkm, duracoes = self.spawn_controller.get_image_data_memory(pokemon_data, is_shiny)
        
        if not frames_pkm:
            print(f"❌ Falha ao obter frames para {pokemon_name}")
            return

        # Processa Fundo + Pokemon 
        gif_final_bytes = self.spawn_controller.create_final_spawn_gif(
            frames_pkm,    
            duracoes,     
            caminho_bg,    
            pokemon_name   
        )
        
        if not gif_final_bytes:
            return

        nome_arquivo = f"{pokemon_name}_{'shiny' if is_shiny else 'normal'}.gif"
        
        # 3. Pega o chat de upload da região correspondente
        cache_channel_id = self.cache_channels.get(region)
        cache_channel = self.bot.get_channel(cache_channel_id)
        
        if cache_channel:
            # Envia o arquivo pesado pro chat escondido
            gif_final_bytes.seek(0)
            arquivo_discord = discord.File(fp=gif_final_bytes, filename=nome_arquivo)
            cache_msg = await cache_channel.send(file=arquivo_discord)
            
            # Pega o link definitivo do CDN do Discord
            nova_url = cache_msg.attachments[0].url
            
            # Salva esse link no JSON pra próxima vez
            self.spawn_controller.save_cached_url(region, pokemon_name, is_shiny, nova_url)
            embed.set_image(url=nova_url)
            await channel.send(embed=embed)
        else:
            # Fallback de segurança: se o chat de cache falhar, ele envia normal anexado
            print(f"⚠️ Chat de cache da região {region} não configurado ou bot sem acesso.")
            gif_final_bytes.seek(0)
            arquivo_fallback = discord.File(fp=gif_final_bytes, filename=nome_arquivo)
            embed.set_image(url=f"attachment://{nome_arquivo}")
            await channel.send(embed=embed, file=arquivo_fallback)

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
                    random_id = randint(1, 386)
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
            if pokemon_name == self.active_spawns[ctx.guild.id]["name"].lower():
                spawn_data = self.active_spawns.pop(ctx.guild.id)
                
                pokemon_base = await self.get_pokemon_data(pokemon_name)
                if not pokemon_base: 
                    return
                
                pokemon_id = pokemon_base["_id"]
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

        async with ctx.typing():
            pokemon_data = await self.get_pokemon_data(pokemon_name)
            
            if not pokemon_data:
                return await ctx.send(f"❌ Pokémon `{pokemon_name}` não encontrado no Banco de Dados.")

            is_shiny = status.lower() == "shiny"
            is_legendary = pokemon_data['name'].lower() in [n.lower() for n in self.legendaries]
            
            self.active_spawns[ctx.guild.id] = {
                "name": pokemon_data['name'],
                "shiny": is_shiny
            }

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