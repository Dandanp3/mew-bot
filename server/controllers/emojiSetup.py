import discord
from discord.ext import commands
import asyncio
import json
import os
import aiohttp

class EmojiSetup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.owner_id = 505806599034765323
        
        self.guild_ids = [
            1458255579180044310, 
            1472264036421992708, 
            1474599440844197900, 
            1474600343210819705  
        ]

        self.cache_dir = os.path.join(os.getcwd(), 'cache', 'cache_icons')
        os.makedirs(self.cache_dir, exist_ok=True)
        self.json_path = os.path.join(self.cache_dir, 'kanto.json')

    @commands.command(name="fix_emojis")
    async def fix_emojis(self, ctx):
        if ctx.author.id != self.owner_id:
            return await ctx.send("❌ Negado.")

        await ctx.send("🔍 Verificando emojis já existentes")
        print("\nMAPEANDO EMOJIS EXISTENTES")

        emojis_data = {}
        for guild_id in self.guild_ids:
            guild = self.bot.get_guild(guild_id)
            if not guild: continue
            
            for emoji in guild.emojis:
                if emoji.name.startswith("pkmn_"):
                    try:
                        poke_id = emoji.name.split("_")[1]
                        emojis_data[str(poke_id)] = str(emoji)
                        print(f"🔎 Encontrado: ID {poke_id} no servidor {guild.name}")
                    except:
                        continue

        # Salva o progresso atual no JSON
        with open(self.json_path, 'w', encoding='utf-8') as f:
            json.dump(emojis_data, f, indent=4)
        
        await ctx.send(f"✅ Mapeamento concluído. {len(emojis_data)} emojis encontrados.")
        print(f"\nCONTINUANDO UPLOAD (Faltam {151 - len(emojis_data)})")

        # Continua o upload do que falta
        async with aiohttp.ClientSession() as session:
            current_guild_idx = 0

            for poke_id in range(1, 152):
                if str(poke_id) in emojis_data:
                    continue 

                # Procura servidor com espaço
                while current_guild_idx < len(self.guild_ids):
                    guild = self.bot.get_guild(self.guild_ids[current_guild_idx])
                    if not guild:
                        current_guild_idx += 1
                        continue
                    
                    static_emojis = [e for e in guild.emojis if not e.animated]
                    if len(static_emojis) < 50:
                        break
                    else:
                        current_guild_idx += 1
                
                if current_guild_idx >= len(self.guild_ids):
                    await ctx.send("❌ Sem espaço nos servidores fornecidos!")
                    break

                # Download e Upload
                img_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-vii/icons/{poke_id}.png"
                emoji_name = f"pkmn_{poke_id}"

                async with session.get(img_url) as resp:
                    if resp.status == 200:
                        img_bytes = await resp.read()
                        try:
                            new_emoji = await guild.create_custom_emoji(name=emoji_name, image=img_bytes)
                            emojis_data[str(poke_id)] = str(new_emoji)
                            print(f"🟢 Criado: ID {poke_id:03d} -> {guild.name}")
                            with open(self.json_path, 'w', encoding='utf-8') as f:
                                json.dump(emojis_data, f, indent=4)
                            
                            await asyncio.sleep(4)
                        except Exception as e:
                            print(f"🔴 Erro no ID {poke_id}: {e}")
                            await asyncio.sleep(10)

        await ctx.send("Operação finalizada")

async def setup(bot):
    await bot.add_cog(EmojiSetup(bot))