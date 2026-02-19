import discord
from discord.ext import commands
import os
import requests
from PIL import Image, ImageSequence
from io import BytesIO
from server.controllers.pokemonController import PokemonController

class ShinyButton(discord.ui.View):
    """View que gerencia o botão de alternar para Shiny"""
    def __init__(self, cog, pokemon_data):
        super().__init__(timeout=60)
        self.cog = cog
        self.pokemon_data = pokemon_data
        self.is_shiny = False

    @discord.ui.button(label="Shiny", emoji="✨", style=discord.ButtonStyle.secondary)
    async def toggle_shiny(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.is_shiny = not self.is_shiny
        
        # Atualiza o botão
        button.label = "Normal" if self.is_shiny else "Shiny"
        button.style = discord.ButtonStyle.primary if self.is_shiny else discord.ButtonStyle.secondary
        
        # Gera/Busca o GIF no cache
        file_path = self.cog.get_cached_gif(self.pokemon_data, is_shiny=self.is_shiny)
        file = discord.File(file_path, filename="pokemon.gif")
        
        embed = interaction.message.embeds[0]
        embed.set_image(url="attachment://pokemon.gif")
        
        await interaction.response.edit_message(attachments=[file], embed=embed, view=self)

class Pokedex(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.controller = PokemonController()
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        self.cache_dir = os.path.join(project_root, 'cache_gifs')

    def get_cached_gif(self, pokemon_data, scale=3, is_shiny=False):
        """Gerencia cache diferenciando Normal de Shiny"""
        poke_id = pokemon_data['_id']
        region = "Kanto" if 1 <= poke_id <= 151 else "Outros"
        
        pokemon_name = pokemon_data['name'].lower()
        # Adiciona o shiny no nome do arquivo se necessário
        filename = f"Shiny_{pokemon_name}.gif" if is_shiny else f"{pokemon_name}.gif"
        
        region_folder = os.path.join(self.cache_dir, region)
        if not os.path.exists(region_folder):
            os.makedirs(region_folder)
            
        file_path = os.path.join(region_folder, filename)
        
        if os.path.exists(file_path):
            return file_path
        
        # Busca a URL correta baseada no estado
        url = pokemon_data['sprites'].get('front_shiny' if is_shiny else 'front')
        
        # Fallback caso não tenha o sprite específico
        if not url:
            url = pokemon_data['sprites'].get('front')

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

    @commands.command(name="dex")
    async def dex(self, ctx, *, pokemon_name: str):
        pokemon_name = pokemon_name.strip().capitalize()
        
        async with ctx.typing():
            pokemon_data = self.controller.collection.find_one({"name": pokemon_name})
            
            if not pokemon_data:
                return await ctx.send(f"❌ Pokémon **{pokemon_name}** not found!")
            
            file_path = self.get_cached_gif(pokemon_data, is_shiny=False)
            file = discord.File(file_path, filename="pokemon.gif")
            
            s = pokemon_data['stats']
            total_stats = sum(s.values())

            embed = discord.Embed(
                title=f"#{pokemon_data['_id']} — {pokemon_name}", 
                color=0xe67e22
            )
            
            embed.add_field(name="Types", value="\n".join(pokemon_data['types']), inline=True)
            embed.add_field(name="Abilities", value="\n".join(pokemon_data['abilities']), inline=True)
            embed.add_field(name="Region", value="Kanto", inline=True)

            stats_list = (
                f"**HP:** {s['hp']}\n"
                f"**Attack:** {s['attack']}\n"
                f"**Defense:** {s['defense']}\n"
                f"**Sp. Atk:** {s['special_attack']}\n"
                f"**Sp. Def:** {s['special_defense']}\n"
                f"**Speed:** {s['speed']}\n"
                f"**Total:** {total_stats}"
            )
            embed.add_field(name="Base Stats", value=stats_list, inline=True)

            if pokemon_data.get('evolutions'):
                evo_txt = ""
                for evo in pokemon_data['evolutions']:
                    via = f" (Level {evo['min_level']})" if evo['min_level'] else f" ({evo['trigger'].replace('-', ' ').title()})"
                    evo_txt += f"{pokemon_name} evolves into **{evo['target']}**{via}\n"
                embed.add_field(name="Evolution", value=evo_txt, inline=False)

            embed.set_image(url="attachment://pokemon.gif")
            embed.set_footer(text="Database Mew Bot • Gen 5 Animated")
            
            view = ShinyButton(self, pokemon_data)
            
            await ctx.send(file=file, embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Pokedex(bot))