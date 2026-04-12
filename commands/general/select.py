import discord
from discord.ext import commands

class TrainerManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="select", aliases=["s"])
    async def select(self, ctx, index: int):
        
        # Buscar o Pokémon na coleção do usuário pelo catch_order
        pokemon_data = await self.bot.db.caught_pokemons.find_one({
            "owner_id": ctx.author.id,
            "catch_order": index
        })

        if not pokemon_data:
            return await ctx.send(f"❌ você não possui um Pokémon com o número `{index}` na sua coleção.")


        result = await self.bot.db.trainers.update_one(
            {"_id": ctx.author.id},
            {"$set": {"selected_pokemon_id": pokemon_data["_id"]}}
        )

        if result.modified_count > 0 or result.matched_count > 0:
            pokemon_name = pokemon_data.get('species_name', 'Pokémon').capitalize()
            level = pokemon_data.get('level', 1)
            
            embed = discord.Embed(
                description=f"{ctx.author.mention} Você selecionou seu **{pokemon_name}** Lvl. {level}!",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Erro ao selecionar Pokémon. Você já iniciou sua jornada com `!start`?")

async def setup(bot):
    await bot.add_cog(TrainerManagement(bot))