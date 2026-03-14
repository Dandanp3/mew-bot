import discord
from discord.ext import commands
from random import randint

class PokemonSpawn(commands.Cog):
    def __init__(self, bot, controller):
        self.bot = bot
        self.controller = controller
        self.spawns = {}

    async def increment_message(self, server_id):
        # Inicializa o cache do servidor se n existir
        if server_id not in self.spawns:
            channel_id = await self.controller.get_chat_id(server_id)
            self.spawns[server_id] = {
                "current": 0,
                "target": 2, 
                "channel_id": channel_id
            }

        server_spawn = self.spawns[server_id]
        server_spawn["current"] += 1

        # Verifica se atingiu o contador
        if server_spawn["current"] >= server_spawn["target"]:
            server_spawn["current"] = 0
            server_spawn["target"] = randint(20, 50) 

            channel = self.bot.get_channel(server_spawn["channel_id"]) or \
                      await self.bot.fetch_channel(server_spawn["channel_id"])
            
            if channel:
                await channel.send("Um pokemon selvagem apareceu..")

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignora bots e mensagens fora de servidores
        if message.author.bot or not message.guild:
            return
            
        await self.increment_message(message.guild.id)

async def setup(bot):
    await bot.add_cog(PokemonSpawn(bot, bot.server_controller))