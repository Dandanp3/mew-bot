import discord
import os
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')

intents = discord.Intents.default()
intents.message_content = True 

class Mew(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="p!", intents=intents)
    
    async def setup_hook(self):
        # O caminho é: pasta.nome_do_arquivo (sem o .py)
        extensions = ['commands.start.starter',
                      'commands.general.dex'] 
        
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
            print(f" - !{cmd.name}")

if __name__ == "__main__":
    bot = Mew()
    bot.run(TOKEN)