import discord
from discord.ext import commands
from discord.ui import Button, View
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
    def __init__(self, pokemon_data, base_stats, author, image_url, is_detailed=False):
        super().__init__(timeout=60)
        self.pokemon_data = pokemon_data
        self.base_stats = base_stats
        self.author = author 
        self.image_url = image_url
        self.is_detailed = is_detailed

        label = "Back" if is_detailed else "EVs/Moves"
        style = discord.ButtonStyle.secondary if is_detailed else discord.ButtonStyle.primary
        
        btn = Button(label=label, style=style)
        btn.callback = self.toggle_callback
        self.add_item(btn)

    async def toggle_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message("This menu isn't yours!", ephemeral=True)
        
        self.is_detailed = not self.is_detailed
        
        new_embed = create_info_embed(self.pokemon_data, self.base_stats, self.is_detailed)
        new_embed.set_thumbnail(url=self.author.display_avatar.url)
        
        # Usa a URL salva em vez de tentar ler um attachment perdido
        if self.image_url:
            new_embed.set_image(url=self.image_url)
        
        new_view = InfoView(self.pokemon_data, self.base_stats, self.author, self.image_url, self.is_detailed)
        
        await interaction.response.edit_message(embed=new_embed, view=new_view)

def create_info_embed(pokemon, base, detailed=False):
    stats = pokemon.get('stats', {})
    ivs = pokemon.get('ivs', {})
    
    # --- LÓGICA DE GÊNERO ---
    gender = pokemon.get('gender', 'Unknown')
    if gender == 'Male':
        g_icon = "♂️"
    elif gender == 'Female':
        g_icon = "♀️"
    else:
        g_icon = "❓"
    
    sp_atk = stats.get('sp_atk') or stats.get('special_attack', 0)
    sp_def = stats.get('sp_def') or stats.get('special_defense', 0)

    primary_type = base['types'][0] if base.get('types') else "Normal"
    embed_color = TYPE_COLORS.get(primary_type, 0x00AAFF)
    
    shiny_prefix = "✨ " if pokemon.get('is_shiny') else ""
    name = pokemon.get('species_name', 'Unknown').title()
    
    embed = discord.Embed(
        title=f"Level {pokemon.get('level', 5)} {shiny_prefix}{name} {g_icon}",
        color=embed_color
    )

    if not detailed:
        details_text = (
            f"**XP:** {pokemon.get('total_xp', 0)}\n"
            f"**Nature:** {pokemon.get('nature', 'Unknown')}\n"
            f"**Gender:** {gender} {g_icon}\n"
            f"\u200b" 
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

    @commands.command(name="info")
    async def info(self, ctx, index: int = None):
        trainer = await self.bot.trainer_controller.get_trainer(ctx.author.id)
        
        if not trainer:
            return await ctx.send("Você precisa iniciar sua jornada primeiro! Use `!start`")
            
        if index is None:
            pokemon_id = trainer.get('selected_pokemon_id')
            if not pokemon_id:
                return await ctx.send("Você não tem um Pokémon selecionado. Use `!select <numero>` ou especifique no comando `!info <numero>`.")
            query = {"_id": pokemon_id}
        else:
            query = {"owner_id": ctx.author.id, "catch_order": index}

        pokemon_data = await self.bot.db.caught_pokemons.find_one(query)
        if not pokemon_data:
            return await ctx.send("<:letterx:1473913370171408465> Pokémon não encontrado.")

        base_stats = await self.bot.db.pokemons.find_one({"_id": pokemon_data['species_id']})
        is_shiny = pokemon_data.get('is_shiny', False)
        
        pokemon_id = pokemon_data['species_id']
        pokemon_name = pokemon_data['species_name']
        region = self.bot.spawn_controller.get_region_folder(pokemon_id)

        cache_name = f"info_{pokemon_name}"
        
        cached_url = self.bot.spawn_controller.get_cached_url(region, cache_name, is_shiny)

        embed = create_info_embed(pokemon_data, base_stats)
        embed.set_thumbnail(url=ctx.author.display_avatar.url)

        try:
            if cached_url:
                embed.set_image(url=cached_url)
                view = InfoView(pokemon_data, base_stats, ctx.author, cached_url)
                return await ctx.send(embed=embed, view=view)

            mock_data = {'_id': pokemon_id, 'name': pokemon_name}
            frames_pkm, duracoes = self.bot.spawn_controller.get_image_data_memory(mock_data, is_shiny)
            
            if frames_pkm:
                # Monta o GIF do sprite redimensionado na memória
                output = BytesIO()
                frames_pkm[0].save(
                    output, format="GIF", save_all=True, append_images=frames_pkm[1:],
                    duration=duracoes, loop=0, disposal=2, optimize=True
                )
                output.seek(0)
                
                nome_arquivo = f"{cache_name}_{'shiny' if is_shiny else 'normal'}.gif"
                arquivo_discord = discord.File(fp=output, filename=nome_arquivo)

                cache_channel_id = getattr(self.bot, 'cache_channels', {}).get(region)
                cache_channel = self.bot.get_channel(cache_channel_id) if cache_channel_id else None

                if cache_channel:
                    msg = await cache_channel.send(file=arquivo_discord)
                    nova_url = msg.attachments[0].url
                    self.bot.spawn_controller.save_cached_url(region, cache_name, is_shiny, nova_url)
                    
                    embed.set_image(url=nova_url)
                    view = InfoView(pokemon_data, base_stats, ctx.author, nova_url)
                    await ctx.send(embed=embed, view=view)
                else:
                    # Fallback de emergência: se não achar o canal de cache, envia no próprio chat
                    embed.set_image(url=f"attachment://{nome_arquivo}")
                    output.seek(0)
                    view = InfoView(pokemon_data, base_stats, ctx.author, None) 
                    await ctx.send(file=arquivo_discord, embed=embed, view=view)
            else:
                # Se a PokeAPI falhou
                await ctx.send("Não foi possível carregar a imagem da API.", embed=embed, view=InfoView(pokemon_data, base_stats, ctx.author, None))

        except Exception as e:
            print(f"Erro ao processar comando info: {e}")
            await ctx.send("Ocorreu um erro ao buscar as informações do Pokémon.")

async def setup(bot):
    await bot.add_cog(Info(bot))