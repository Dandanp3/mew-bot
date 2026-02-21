import discord
from discord.ext import commands
import os
import json
import math

class PokemonList(discord.ui.View):
    def __init__(self, author, pokemons, emojis, page=1):
        super().__init__(timeout=120)
        self.author = author
        self.pokemons = pokemons
        self.emojis = emojis
        self.page = page
        self.per_page = 20
        self.total_pages = math.ceil(len(pokemons) / self.per_page) or 1

        self.update_buttons()

    def update_buttons(self):
        self.prev_btn.disabled = self.page == 1
        self.next_btn.disabled = self.page == self.total_pages
        self.page_indicator.label = f"Pág {self.page}/{self.total_pages}"

    def generate_embed(self):
        start = (self.page - 1) * self.per_page
        end = start + self.per_page
        page_items = self.pokemons[start:end]

        desc = ""
        for p in page_items:
            catch_id = p.get('catch_order', 0)
            species_id = str(p.get('species_id', 1))
            name = p.get('species_name', 'Unknown').capitalize()
            level = p.get('level', 1)
            
            iv = p.get('iv_percentage', 0.0)
            if isinstance(iv, str):
                iv = float(iv)
            
            emoji = self.emojis.get(species_id, "✨")   
            gender = p.get('gender', 'Unknown')
            if gender == 'Male': g_icon = " ♂️"
            elif gender == 'Female': g_icon = " ♀️"
            else: g_icon = ""

            shiny = "✨ " if p.get('is_shiny') else ""
            
            desc += f"`{catch_id}` {emoji} {shiny}**{name}**{g_icon} • Lvl. {level} • {iv:.2f}%\n"
        embed = discord.Embed(
            title=f"🎒 {self.author.display_name}'s pokemons", 
            description=desc, 
            color=discord.Color.from_str("#FF99CC") 
        )
        embed.set_thumbnail(url=self.author.display_avatar.url)
        total = len(self.pokemons)
        pokeball_icon = "https://cdn-icons-png.flaticon.com/512/188/188987.png"
        embed.set_footer(
            text=f"Exibindo {start+1}–{min(end, total)} de {total} Pokémon", 
            icon_url=pokeball_icon
        )
        
        return embed

    # Seta para voltar
    @discord.ui.button(label="◀", style=discord.ButtonStyle.primary, custom_id="prev_page")
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message("Esta lista não é sua!", ephemeral=True)
            
        self.page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.generate_embed(), view=self)

    @discord.ui.button(label="Pág 1/1", style=discord.ButtonStyle.secondary, custom_id="page_indicator", disabled=True)
    async def page_indicator(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass 

    # Seta para avançar 
    @discord.ui.button(label="▶", style=discord.ButtonStyle.primary, custom_id="next_page")
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message("Esta lista não é sua!", ephemeral=True)
            
        self.page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.generate_embed(), view=self)
        
class PokemonCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.emojis = {}
        cache_dir = os.path.join(os.getcwd(), 'cache', 'cache_icons')
        json_path = os.path.join(cache_dir, 'kanto.json')
        
        try:
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    self.emojis = json.load(f)
                print(f"✅ Emojis carregados para o comando pokemon!")
        except Exception as e:
            print(f"⚠️ Erro ao carregar emojis: {e}")

    @commands.command(name="pokemon", aliases=["p"])
    async def pokemon(self, ctx):
        pokemons = await self.bot.db.caught_pokemons.find(
            {"owner_id": ctx.author.id}
        ).sort("catch_order", 1).to_list(length=None)

        if not pokemons:
            return await ctx.send("❌ Você ainda não tem nenhum Pokémon!")

        view = PokemonList(ctx.author, pokemons, self.emojis)
        embed = view.generate_embed()
        
        if len(pokemons) <= 20:
            view = None

        await ctx.send(embed=embed, view=view)
async def setup(bot):
    await bot.add_cog(PokemonCommand(bot))