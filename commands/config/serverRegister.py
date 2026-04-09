import discord
from discord.ext import commands

class ServerAutoRegister(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"\n📊 Verificando e registrando servidores...")
        
        for guild in self.bot.guilds:
            await self.bot.server_controller.server_register(guild.id)

async def setup(bot):
    await bot.add_cog(ServerAutoRegister(bot))