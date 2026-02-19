import discord
from discord.ext import commands
import json
import requests
import os
from PIL import Image, ImageSequence
from io import BytesIO

class Starter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.json_path = os.path.join(current_dir, 'starterPokemon.json')
        
        # Cache Config
        project_root = os.path.dirname(os.path.dirname(current_dir))
        self.cache_dir = os.path.join(project_root, 'cache', 'cache_gifs')
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def load_starters(self):
        with open(self.json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
        
    def get_resized_gif(self, pokemon_name, region_name, url, scale=3):
        region_folder = os.path.join(self.cache_dir, region_name)
        if not os.path.exists(region_folder):
            os.makedirs(region_folder)
            
        file_path = os.path.join(region_folder, f"{pokemon_name.lower()}.gif")
        if os.path.exists(file_path):
            return file_path
        
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        
        frames = []
        durations = []
        for frame in ImageSequence.Iterator(img):
            frame = frame.convert('RGBA')
            resized_frame = frame.resize((frame.width * scale, frame.height * scale), Image.NEAREST)
            frames.append(resized_frame)
            durations.append(frame.info.get('duration', 100))
        
        frames[0].save(file_path, format='GIF', save_all=True, append_images=frames[1:], loop=0, duration=durations, disposal=2)
        return file_path

    @commands.command(name="start")
    async def start(self, ctx):
        # tenta criar o treinador
        trainer = await self.bot.trainer_controller.get_trainer(ctx.author.id)
        
        if trainer and trainer.get('selected_pokemon_id'):
            return await ctx.send(f"Hello {ctx.author.mention}, you’ve already started your journey! Use `!info` to check your Pokémon.")

        if not trainer:
            success, msg = await self.bot.trainer_controller.create_trainer(ctx.author.id, ctx.author.name)
        
        # Mostra o Embed de escolha
        data = self.load_starters()
        embed = discord.Embed(
            title="🌟 Welcome to the world of Pokémon!",
            description=f"Hello {ctx.author.mention}! Professor Oak is waiting for you to choose your partner. Use `!pick` <name> to choose",
            color=0xFF0055
        )        
        
        for gen in data['starters']:
            pokes = gen['pokes']
            line = " - ".join([f"{p['emoji']} **{p['name']}**" for p in pokes])
            embed.add_field(name=f"📍 {gen['region']} (Gen {gen['gen']})", value=line, inline=False)
            
        embed.set_footer(text="Choose wisely — this decision will last forever!")
        await ctx.send(embed=embed)
        
    @commands.command(name="pick")
    async def pick(self, ctx, pokemon_name: str):
        # 1. Verifica se o usuário já escolheu
        trainer = await self.bot.trainer_controller.get_trainer(ctx.author.id)
        if not trainer:
            return await ctx.send("You need to type `!start` first!")
            
        if trainer.get('selected_pokemon_id'):
            return await ctx.send("You’ve already picked your starter! Don’t be greedy.")

        # 2. Valida o nome do Pokémon no JSON
        data = self.load_starters()
        pokemon_name = pokemon_name.strip().capitalize()
        chosen_pokemon = None
        region_name = ""
        
        for gen in data['starters']:
            for p in gen['pokes']:
                if p['name'] == pokemon_name:
                    chosen_pokemon = p 
                    region_name = gen['region']
                    break
    
        if not chosen_pokemon:
            return await ctx.send(f"❌ {pokemon_name} is not a valid starter. Check the list in `!start`.")
        
        async with ctx.typing():
            try:
                # CRIA O POKÉMON NO BANCO 
                poke_mongo_id, poke_obj = await self.bot.catch_controller.create_specific_pokemon(
                    owner_id=ctx.author.id,
                    species_id=chosen_pokemon['api_id'],
                    level=5
                )

                if not poke_mongo_id:
                    return await ctx.send("Error: Pokémon not found in the bot’s database.")

                base_poke = await self.bot.db.pokemons.find_one({"_id": chosen_pokemon['api_id']})
                types = base_poke['types']

                await self.bot.trainer_controller.set_starter(
                    discord_id=ctx.author.id,
                    caught_pokemon_id=poke_mongo_id,
                    species_id=chosen_pokemon['api_id'],
                    region=region_name,
                    types=types
                )
                try:
                    gif_url = base_poke['sprites']['front'] 
                    if not gif_url:
                        gif_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-v/black-white/animated/{chosen_pokemon['api_id']}.gif"
                except:
                    gif_url = None

                embed = discord.Embed(color=0x2ecc71)
                embed.title = f"🎉 {ctx.author.name} escolheu {pokemon_name}!"
                embed.description = (
                    f"Your journey in **{region_name}** has begun!\n"
                    f"**Nature:** {poke_obj.nature}\n"
                    f"**IVs:** {poke_obj.iv_percentage}%\n"
                    f"**Moves:** {', '.join(poke_obj.moves)}"
                )
                embed.set_footer(text=f"ID Global: {poke_mongo_id}")
                
                if gif_url:
                    file_path = self.get_resized_gif(pokemon_name, region_name, gif_url)
                    file = discord.File(file_path, filename="starter.gif")
                    embed.set_image(url="attachment://starter.gif")
                    await ctx.send(file=file, embed=embed)
                else:
                    await ctx.send(embed=embed)
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                await ctx.send(f"Ocorreu um erro crítico ao salvar seu inicial: {e}")
                    
async def setup(bot):
    await bot.add_cog(Starter(bot))