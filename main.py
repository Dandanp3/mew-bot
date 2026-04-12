import discord
import os
import certifi
from dotenv import load_dotenv
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient

# controllers
from server.controllers.trainerController import TrainerController
from server.controllers.catchController import CatchController
from server.controllers.serverController import ServerController
from server.controllers.spawnController import SpawnController
from server.controllers.xpController import XPController 

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
MONGO_URI = os.getenv('MONGO_TOKEN')

intents = discord.Intents.default()
intents.message_content = True 
intents.guilds = True  

class Mew(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="p!", intents=intents)
        ca = certifi.where()
        self.mongo_client = AsyncIOMotorClient(MONGO_URI, tlsCAFile=ca)
        self.db = self.mongo_client['mew_bot']
        
        root_path = os.path.dirname(os.path.abspath(__file__))
        
        # Instanciando os controllers
        self.trainer_controller = TrainerController(self.db)
        self.catch_controller = CatchController(self.db)
        self.server_controller = ServerController(self.db)
        self.spawn_controller = SpawnController(root_path)
        self.xp_controller = XPController(self) 
        
        self.add_check(self.check_starter_chosen)

    async def setup_hook(self):
        extensions = [
            'commands.start.starter',
            'commands.general.dex',
            'commands.general.info',
            'commands.general.pokemons',
            'commands.general.spawn',
            'server.controllers.emojiSetup',
            'commands.config.serverRegister',
            'commands.general.select' 
        ] 
        
        for ext in extensions:
            try:
                await self.load_extension(ext)
                print(f"✅ Extensão carregada: {ext}")
            except Exception as e:
                print(f"❌ Falha ao carregar {ext}")
                import traceback
                traceback.print_exc()

    async def on_message(self, message):
        # Ignora bots e mensagens que não são de texto
        if message.author.bot or not message.guild:
            return

        # Tenta dar XP ao Pokémon selecionado
        try:
            # result retorna {'leveled_up': bool, 'new_level': int, 'pokemon_name': str}
            result = await self.xp_controller.add_xp(message.author.id, 100)
            
            if result and result.get("leveled_up"):
                await message.channel.send(
                    f"🎊 **{message.author.display_name}**, seu **{result['pokemon_name']}** subiu para o nível **{result['new_level']}**!"
                )
        except Exception as e:
            print(f"Erro ao processar XP: {e}")

        await self.process_commands(message)

    async def on_ready(self):
        print(f"\n🟢 Bot conectado como {self.user}")
        print(f"📊 O bot está em {len(self.guilds)} servidor(es)")
        print("Comandos disponíveis:")
        for cmd in self.walk_commands():
            print(f" - p!{cmd.name}")
        print()

    async def on_guild_join(self, guild: discord.Guild):
        print(f"Bot entrou no servidor: {guild.name} (ID: {guild.id})")
        await self.server_controller.server_register(guild.id)

    async def check_starter_chosen(self, ctx):
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