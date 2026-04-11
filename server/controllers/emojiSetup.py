import discord
from discord.ext import commands
import asyncio
import json
import os
import aiohttp
from PIL import Image
from io import BytesIO

class EmojiSetup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.owner_id = 505806599034765323
        
        # 8 servidores: Hoenn
        self.guild_ids = [
            810562440811118623, 
            1374151327294292129, 
            1458255579180044310, 
            1491865979607842946,
            1491866234831114413, 
            1435662851959165040,
            1197386408910921750,
            1492273263991066804,
            1456753477844996199,
            1213214506646241281
        ]

        self.cache_dir = os.path.join(os.getcwd(), 'cache', 'cache_icons')
        os.makedirs(self.cache_dir, exist_ok=True)

    def upscale_image(self, img_bytes):
        # Amplia a imagem para 128x128
        img = Image.open(BytesIO(img_bytes))
        img = img.convert("RGBA")
        img_big = img.resize((128, 128), Image.NEAREST)
        
        output = BytesIO()
        img_big.save(output, format="PNG")
        return output.getvalue()

    @commands.command(name="fix_emojis")
    async def fix_emojis(self, ctx):
        if ctx.author.id != self.owner_id:
            return await ctx.send("❌ Negado.")

        await ctx.send("🚀 Iniciando upload das regiões: Kanto, Johto, Hoenn, Sinnoh e Unova!")

        async with aiohttp.ClientSession() as session:
            current_guild_idx = 0

            for poke_id in range(1, 650):
                
                # Definição das Regiões
                if poke_id <= 151:
                    filename = 'kanto.json'
                elif poke_id <= 251:
                    filename = 'johto.json'
                elif poke_id <= 386:
                    filename = 'hoenn.json'
                elif poke_id <= 493:
                    filename = 'sinnoh.json'
                elif poke_id <= 649:
                    filename = 'unova.json'
                
                path_atual = os.path.join(self.cache_dir, filename)
                
                # Carrega o JSON específico para checar se o emoji já existe
                data_especifica = {}
                if os.path.exists(path_atual):
                    with open(path_atual, 'r', encoding='utf-8') as f:
                        data_especifica = json.load(f)
                
                if str(poke_id) in data_especifica:
                    continue 

                # BUSCA SERVIDOR COM ESPAÇO
                target_guild = None
                while current_guild_idx < len(self.guild_ids):
                    guild = self.bot.get_guild(self.guild_ids[current_guild_idx])
                    if not guild:
                        print(f"⚠️ Servidor {self.guild_ids[current_guild_idx]} não encontrado/acessível.")
                        current_guild_idx += 1
                        continue
                    
                    static_emojis = [e for e in guild.emojis if not e.animated]
                    if len(static_emojis) < 50:
                        target_guild = guild
                        break
                    else:
                        print(f"📍 Servidor {guild.name} lotado, pulando para o próximo...")
                        current_guild_idx += 1
                
                if not target_guild:
                    await ctx.send(f"❌ Espaço esgotado! Parei no ID {poke_id}. Adicione mais servidores na lista `guild_ids`.")
                    break

                img_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-vii/icons/{poke_id}.png"
                emoji_name = f"pkmn_{poke_id}"

                try:
                    async with session.get(img_url) as resp:
                        if resp.status == 200:
                            raw_bytes = await resp.read()
                            
                            # Amplia para 128x128 
                            processed_bytes = self.upscale_image(raw_bytes)
                            
                            new_emoji = await target_guild.create_custom_emoji(
                                name=emoji_name, 
                                image=processed_bytes,
                                reason="Setup de Pokédex Ampliado (Pixel Art)"
                            )
                            
                            # Atualiza e salva no JSON correto 
                            data_especifica[str(poke_id)] = str(new_emoji)
                            with open(path_atual, 'w', encoding='utf-8') as f:
                                json.dump(data_especifica, f, indent=4)
                            
                            print(f"[{poke_id:03d}] Criado e salvo em {filename}")
                            
                            # Aguarda o rate limit do Discord
                            await asyncio.sleep(3.5)
                        else:
                            print(f"🔴 ID {poke_id} não encontrado na PokeAPI.")
                except Exception as e:
                    print(f"🔴 Erro crítico no ID {poke_id}: {e}")
                    await asyncio.sleep(10) # Pausa de segurança se der erro de conexão/limite

        await ctx.send("🏁 Processo concluído com sucesso!")

async def setup(bot):
    await bot.add_cog(EmojiSetup(bot))