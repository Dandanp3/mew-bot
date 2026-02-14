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
        # Pasta cache/gifs
        self.cache_dir = os.path.join(project_root, 'cache_gifs')
        
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def load_starters(self):
        with open(self.json_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    @commands.command(name="start")
    async def start(self, ctx):
        data = self.load_starters()
        
        embed = discord.Embed(
            title="Seja bem vindo ao mundo pokémon!",
            description="Para começar a sua jornada escolha um dos pokémons abaixo usando o comando `!pick <nome do pokémon>.`"
            color=0xFF0055
            
        )         
        