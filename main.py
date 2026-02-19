import discord
import os
import certifi
from dotenv import load_dotenv
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient

# Import dos seus Controllers
from server.controllers.trainerController import TrainerController
from server.controllers.catchController import CatchController

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
MONGO_URI = os.getenv('MONGO_TOKEN')

intents = discord.Intents.default()
intents.message_content = True 

class Mew(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="p!", intents=intents)
        ca = certifi.where()
        self.mongo_client = AsyncIOMotorClient(MONGO_URI, tlsCAFile=ca)
        self.db = self.mongo_client['mew_bot']
        
        self.trainer_controller = TrainerController(self.db)
        self.catch_controller = CatchController(self.db)
        self.add_check(self.check_starter_chosen)

    async def setup_hook(self):
        extensions = [
            'commands.start.starter',
            'commands.general.dex'
        ] 
        
        for ext in extensions:
            try:
                await self.load_extension(ext)
                print(f"✅ Extensão carregada: {ext}")
            except Exception as e:
                print(f"❌ Falha ao carregar {ext}")
                import traceback
                traceback.print_exc()

    async def on_ready(self):
        print(f"Bot conectado como {self.user} ✅")
        print("Comandos disponíveis:")
        for cmd in self.walk_commands():
            print(f" - p!{cmd.name}")

    async def check_starter_chosen(self, ctx):
        # Lista de comandos liberados
        whitelist = ['start', 'pick', 'help', 'ping']
        
        if ctx.command is None or ctx.command.name in whitelist:
            return True

        trainer = await self.trainer_controller.get_trainer(ctx.author.id)
        
        if not trainer:
            await ctx.send(f"❌ {ctx.author.mention}, você ainda não começou sua jornada! Use `p!start`.")
            return False
        
        if not trainer.get('selected_pokemon_id'):
            await ctx.send(f"⚠️ {ctx.author.mention}, você ainda não escolheu seu inicial! Use `p!pick <nome>`.")
            return False

        return True

if __name__ == "__main__":
    bot = Mew()
    bot.run(TOKEN)