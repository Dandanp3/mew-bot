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
        
        # RAIZ DO PROJETO
        project_root = os.path.dirname(os.path.dirname(current_dir))
        # Pasta cache principal
        self.cache_dir = os.path.join(project_root, 'cache_gifs')
        
        # Cria a pasta raiz do cache se não existir
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def load_starters(self):
        with open(self.json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
        
    # ATUALIZADO: Agora recebe 'region_name'
    def get_resized_gif(self, pokemon_name, region_name, url, scale=3):
        # 1. Define a pasta da região (ex: cache_gifs/Kanto)
        region_folder = os.path.join(self.cache_dir, region_name)
        
        # 2. Se a pasta da região não existe, cria ela
        if not os.path.exists(region_folder):
            os.makedirs(region_folder)
            
        # 3. O arquivo final fica dentro da pasta da região
        file_path = os.path.join(region_folder, f"{pokemon_name.lower()}.gif")
        
        # Verifica se já existe
        if os.path.exists(file_path):
            return file_path
        
        # --- Processamento da Imagem ---
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        
        frames = []
        durations = []
        
        for frame in ImageSequence.Iterator(img):
            frame = frame.convert('RGBA')
            resized_frame = frame.resize(
                (frame.width * scale, frame.height * scale),
                Image.NEAREST
            )
            frames.append(resized_frame)
            durations.append(frame.info.get('duration', 100))
        
        frames[0].save(
            file_path,
            format='GIF',
            save_all=True,
            append_images=frames[1:],
            loop=0,
            duration=durations,
            disposal=2
        )
        return file_path

    @commands.command(name="start")
    async def start(self, ctx):
        data = self.load_starters()
        
        embed = discord.Embed(
            title="Seja bem vindo ao mundo pokémon!",
            description="Para começar a sua jornada escolha um dos pokémons abaixo usando o comando `!pick <nome do pokémon>`.",
            color=0xFF0055
        )        
        
        for gen in data['starters']:
            pokes = gen['pokes']
            line = " - ".join([f"{p['emoji']} **{p['name']}**" for p in pokes])
            
            embed.add_field(
                name=f"Geração {gen['gen']} ({gen['region']})",
                value=line,
                inline=False   
            )
            
        embed.set_footer(text="A jornada começa agora!")
        await ctx.send(embed=embed) # Correção: Indentado para fora do loop
        
    @commands.command(name="pick")
    async def pick(self, ctx, pokemon_name: str):
        data = self.load_starters()
        pokemon_name = pokemon_name.strip().capitalize()
        
        chosen_pokemon = None
        region_name = ""
        
        # Loop para achar o pokémon e a região dele
        for gen in data['starters']:
            for p in gen['pokes']:
                if p['name'] == pokemon_name:
                    chosen_pokemon = p 
                    region_name = gen['region'] # Aqui pegamos "Kanto", "Johto", etc.
                    break
    
        if not chosen_pokemon:
            return await ctx.send(f"❌ **{pokemon_name}** não é um inicial válido")
        
        async with ctx.typing():
            try:
                api_url = f"https://pokeapi.co/api/v2/pokemon/{chosen_pokemon['api_id']}"
                api_data = requests.get(api_url).json()
                
                try:
                    image_url = api_data['sprites']['versions']['generation-v']['black-white']['animated']['front_default']
                except KeyError:
                    image_url = None
                
                embed = discord.Embed(color=0x2ecc71)
                embed.title = f"✨ {pokemon_name}, eu escolho você!"
                embed.description = f"**{ctx.author.name}** começou sua jornada em **{region_name}**!"
                embed.set_footer(text=f"ID: #{chosen_pokemon['api_id']} | Nível: 5")
                
                if image_url:
                    # PASSAMOS A REGIÃO AQUI
                    file_path = self.get_resized_gif(pokemon_name, region_name, image_url)
                    
                    file = discord.File(file_path, filename="pokemon.gif")
                    embed.set_image(url="attachment://pokemon.gif")
                    await ctx.send(file=file, embed=embed)
                
                else:
                    artwork_url = api_data['sprites']['other']['official-artwork']['front_default']
                    embed.set_image(url=artwork_url)
                    await ctx.send(embed=embed)
                
            except Exception as e:
                print(f"Erro no pick: {e}")
                await ctx.send("Houve um erro ao processar seu Pokémon.")                   
                    
async def setup(bot):
    await bot.add_cog(Starter(bot))