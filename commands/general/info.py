import discord
from discord.ext import commands
from discord.ui import Button, View
import os
from PIL import Image
import requests
from io import BytesIO

TYPE_COLORS = {
    "Normal": 0xA8A77A, "Fire": 0xEE8130, "Water": 0x6390F0,
    "Electric": 0xF7D02C, "Grass": 0x7AC74C, "Ice": 0x96D9D6,
    "Fighting": 0xC22E28, "Poison": 0xA33EA1, "Ground": 0xE2BF65,
    "Flying": 0xA98FF3, "Psychic": 0xF95587, "Bug": 0xA6B91A,
    "Rock": 0xB6A136, "Ghost": 0x735797, "Dragon": 0x6F35FC,
    "Steel": 0xB7B7CE, "Fairy": 0xD685AD, "Dark": 0x705746
}

class InfoView(View):
    def __init__(self, pokemon_data, base_stats, author, is_detailed=False):
        super().__init__(timeout=60)
        self.pokemon_data = pokemon_data
        self.base_stats = base_stats
        self.author = author 
        self.is_detailed = is_detailed

        label = "Voltar" if is_detailed else "EVs/Moves"
        style = discord.ButtonStyle.secondary if is_detailed else discord.ButtonStyle.primary
        
        btn = Button(label=label, style=style)
        btn.callback = self.toggle_callback
        self.add_item(btn)

    async def toggle_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message("Este menu não é seu!", ephemeral=True)
        self.is_detailed = not self.is_detailed
        
        new_embed = create_info_embed(self.pokemon_data, self.base_stats, self.is_detailed)
        
        new_embed.set_thumbnail(url=self.author.display_avatar.url)
        new_embed.set_image(url="attachment://pokemon.gif")
        
        new_view = InfoView(self.pokemon_data, self.base_stats, self.author, self.is_detailed)
        
        await interaction.response.edit_message(embed=new_embed, view=new_view)

def create_info_embed(pokemon, base, detailed=False):
    stats = pokemon.get('stats', {})
    ivs = pokemon.get('ivs', {})
    
    # Normalização de nomes de stats
    sp_atk = stats.get('sp_atk') or stats.get('special_attack', 0)
    sp_def = stats.get('sp_def') or stats.get('special_defense', 0)

    # Cores e Title
    primary_type = base['types'][0] if base.get('types') else "Normal"
    embed_color = TYPE_COLORS.get(primary_type, 0x00AAFF)
    
    shiny_prefix = "✨ " if pokemon.get('is_shiny') else ""
    name = pokemon.get('species_name', 'Unknown').title()
    
    embed = discord.Embed(
        title=f"Level {pokemon.get('level', 5)} {shiny_prefix}{name}",
        color=embed_color
    )

    if not detailed:
        details_text = (
            f"**XP:** {pokemon.get('xp', 0)}/2025\n"
            f"**Nature:** {pokemon.get('nature', 'Unknown')}\n"
            f"**Gender:** {pokemon.get('gender', 'Unknown')}\n"
            f"\u200b" # Linha vazia para respiro
        )
        embed.add_field(name="Details", value=details_text, inline=False)

        stats_text = (
            f"**HP:** {stats.get('hp', 0)} — IV: {ivs.get('hp', 0)}/31\n"
            f"**Attack:** {stats.get('attack', 0)} — IV: {ivs.get('attack', 0)}/31\n"
            f"**Defense:** {stats.get('defense', 0)} — IV: {ivs.get('defense', 0)}/31\n"
            f"**Sp. Atk:** {sp_atk} — IV: {ivs.get('sp_atk', 0)}/31\n"
            f"**Sp. Def:** {sp_def} — IV: {ivs.get('sp_def', 0)}/31\n"
            f"**Speed:** {stats.get('speed', 0)} — IV: {ivs.get('speed', 0)}/31\n"
            f"**Total IV:** {pokemon.get('iv_percentage', 0)}%"
        )
        embed.add_field(name="Stats", value=stats_text, inline=False)
    else:
        evs = pokemon.get('evs', {})
        moves = pokemon.get('moves', [])
        moves_list = "\n".join([f"• {m}" for m in moves]) if moves else "Nenhum move."
        
        embed.add_field(name="Moves Atuais", value=moves_list + "\n\u200b", inline=False)
        
        evs_text = (
            f"**HP:** {evs.get('hp', 0)} | **Atk:** {evs.get('attack', 0)}\n"
            f"**Def:** {evs.get('defense', 0)} | **SpA:** {evs.get('sp_atk', 0)}\n"
            f"**SpD:** {evs.get('sp_def', 0)} | **Spe:** {evs.get('speed', 0)}"
        )
        embed.add_field(name="Effort Values (EVs)", value=evs_text, inline=False)

    embed.set_footer(text=f"Displaying pokémon {pokemon.get('catch_order', 1)}.\nID: {pokemon.get('_id')}")
    return embed

class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cache_dir = os.path.join(os.getcwd(), 'cache', 'cache_gifs')

    async def get_pokemon_image(self, pokemon_name, region, image_url):
        # Garante que a pasta existe
        region_path = os.path.join(self.cache_dir, region.capitalize())
        os.makedirs(region_path, exist_ok=True)
        
        file_path = os.path.join(region_path, f"{pokemon_name.lower()}.gif")

        # Se não existe no cache, baixa e redimensiona
        if not os.path.exists(file_path):
            response = requests.get(image_url)
            img = Image.open(BytesIO(response.content))
            
            # Redimensiona 
            img = img.resize((250, 250), Image.Resampling.LANCZOS)
            img.save(file_path, format="GIF", save_all=True) if getattr(img, "is_animated", False) else img.save(file_path, format="PNG")
            
        return file_path

    @commands.command(name="info")
    async def info(self, ctx, index: int = None):
        trainer = await self.bot.trainer_controller.get_trainer(ctx.author.id)
        
        if index is None:
            pokemon_id = trainer.get('selected_pokemon_id')
            query = {"_id": pokemon_id}
        else:
            query = {"owner_id": ctx.author.id, "catch_order": index}

        pokemon_data = await self.bot.db.caught_pokemons.find_one(query)
        if not pokemon_data:
            return await ctx.send("❌ Pokémon não encontrado.")

        base_stats = await self.bot.db.pokemons.find_one({"_id": pokemon_data['species_id']})
        
        region = base_stats.get('region', 'Kanto')
        img_url = base_stats['sprites'].get('animated') or base_stats['sprites']['front']
        
        try:
            local_path = await self.get_pokemon_image(pokemon_data['species_name'], region, img_url)
            file = discord.File(local_path, filename="pokemon.gif")
            
            embed = create_info_embed(pokemon_data, base_stats)
            
            embed.set_thumbnail(url=ctx.author.display_avatar.url) 
            embed.set_image(url="attachment://pokemon.gif")       
            
            view = InfoView(pokemon_data, base_stats, ctx.author) 
            await ctx.send(file=file, embed=embed, view=view)

        except Exception as e:
            print(f"Erro ao processar imagem: {e}")
            embed = create_info_embed(pokemon_data, base_stats)
            embed.set_thumbnail(url=ctx.author.display_avatar.url) 
            embed.set_image(url=img_url)
            await ctx.send(embed=embed, view=InfoView(pokemon_data, base_stats, ctx.author))

async def setup(bot):
    await bot.add_cog(Info(bot))