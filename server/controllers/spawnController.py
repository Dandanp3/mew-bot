import os
import random
from PIL import Image, ImageSequence
from io import BytesIO
import requests

class SpawnController:
    def __init__(self, project_root):
        # Usamos o caminho passado pelo main.py
        self.project_root = project_root
        self.bg_dir = os.path.join(self.project_root, 'cache', 'Background')
        
        # Formato: (pos_x, pos_y)
        self.bg_positions = {
            "fire": (200, 110),   
            "water": (200, 110),  
            "grass": (220, 110),
            "bug": (240, 170),
            "dark": (200, 110),
            "dragon": (200, 110),
            "electric": (200, 110),
            "fighting": (220, 110),
            "flying": (200, 110),
            "ghost": (200, 110),
            "ground": (200, 110),
            "ice": (200, 110),
            "normal": (220, 110),
            "poison": (220, 90),
            "psychic": (200, 110),
            "rock": (220, 110),
            "steel": (200, 110),
        }
    
    def get_region_folder(self, pokemon_id):
        if 1 <= pokemon_id <= 151:
            return "Kanto"
        elif 152 <= pokemon_id <= 251:
            return "Johto"
        return "Geral" 
        
    def get_background_data(self, types_list):
        tipos_disponiveis = [t['type']['name'] for t in types_list]
        tipo_escolhido = random.choice(tipos_disponiveis)
        
        try:
            arquivos_no_diretorio = os.listdir(self.bg_dir)
            for n in arquivos_no_diretorio:
                if n.startswith(tipo_escolhido):
                    caminho_completo = os.path.join(self.bg_dir, n)
                    coords = self.bg_positions.get(tipo_escolhido, (150, 100))
                    return caminho_completo, coords
        except Exception as e:
            print(f"Erro ao acessar backgrounds: {e}")
            
        return None, (150, 100)
    
    def get_frame_durations(self, img):

        duracoes = []
        
        for frame in ImageSequence.Iterator(img):
            duracao = frame.info.get('duration', 100)
            
            # justa durações muito baixas (< 20ms) ou muito altas (> 200ms)
            if duracao <= 0:
                duracao = 100
            elif duracao < 20:
                duracao = 100
            elif duracao > 200:
                duracao = 80
            
            duracoes.append(duracao)
        
        return duracoes
            
    def process_and_save_gif(self, img_original, caminho_salvamento, escala=3):
        # Criar a pasta se n existir
        os.makedirs(os.path.dirname(caminho_salvamento), exist_ok=True)
        
        frames_redimensionados = []
        duracoes = self.get_frame_durations(img_original)
        
        for frame in ImageSequence.Iterator(img_original):
            frame_rgba = frame.convert("RGBA")
            nova_largura = int(frame_rgba.width * escala)
            nova_altura = int(frame_rgba.height * escala)
            
            frame_grande = frame_rgba.resize((nova_largura, nova_altura), Image.NEAREST)
            frames_redimensionados.append(frame_grande)
        
        frames_redimensionados[0].save(
            caminho_salvamento,
            save_all=True,
            append_images=frames_redimensionados[1:],
            duration=duracoes,  # passa as duraçoes individuais de cada frame
            loop=0,
            disposal=2,
            optimize=True # 9otimiza o tamanho do arquivo
        )
        return caminho_salvamento
        
    def get_image_data(self, pokemon_data, is_shiny):
        pokemon_id = pokemon_data['id']
        pokemon_name = pokemon_data['name'].lower()
        nome_do_arquivo = f"{'Shiny_' if is_shiny else ''}{pokemon_name}.gif"
        
        regiao = self.get_region_folder(pokemon_id)
        caminho_sprite = os.path.join(self.project_root, 'cache', 'cache_gifs', regiao, nome_do_arquivo)
        
        if os.path.exists(caminho_sprite):
            return caminho_sprite
        
        gen5 = pokemon_data['sprites']['versions']['generation-v']['black-white']['animated']
        url_gif = gen5['front_shiny'] if is_shiny else gen5['front_default']
        
        # Fallback se não houver GIF animado na Gen 5
        if not url_gif:
            url_gif = pokemon_data['sprites']['front_shiny'] if is_shiny else pokemon_data['sprites']['front_default']

        sprite_baixado = requests.get(url_gif).content
        img = Image.open(BytesIO(sprite_baixado))
        
        return self.process_and_save_gif(img, caminho_sprite)
    
    def create_final_spawn_gif(self, caminho_pokemon, caminho_bg, coords):
        pkm_gif = Image.open(caminho_pokemon)
        
        # CARREGAR E REDIMENSIONAR O FUNDO
        bg_raw = Image.open(caminho_bg).convert("RGBA")
        largura_alvo = 600
        proporcao = largura_alvo / float(bg_raw.size[0])
        altura_alvo = int((float(bg_raw.size[1]) * proporcao))
        bg_image = bg_raw.resize((largura_alvo, altura_alvo), Image.LANCZOS)
        
        # Extrair duraçoes de TODOS os frames
        duracoes = self.get_frame_durations(pkm_gif)
        
        final_frames = []
        for frame in ImageSequence.Iterator(pkm_gif):
            temp_bg = bg_image.copy()
            p_frame = frame.convert("RGBA")
            
            # Colando o pokemon
            temp_bg.paste(p_frame, coords, p_frame)
            final_frames.append(temp_bg.convert("P", palette=Image.ADAPTIVE))
        
        output = BytesIO()
        final_frames[0].save(
            output,
            format="GIF",
            save_all=True,
            append_images=final_frames[1:],
            duration=duracoes,  
            loop=0,
            disposal=2,
            optimize=True
        )
        
        
        output.seek(0) 
        return output