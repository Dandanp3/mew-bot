import os
import json
from PIL import Image, ImageSequence
from io import BytesIO
import requests

class SpawnController:
    def __init__(self, project_root):
        self.project_root = project_root
        self.bg_dir = os.path.join(self.project_root, 'cache', 'Background')
        
        # Caminho do arquivo JSON com as coordenadas
        self.coords_file = os.path.join(self.project_root, 'server', 'config', 'coords.json')
        self.pokemon_coords = {}  
    
    def _load_coords(self):

        try:
            with open(self.coords_file, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                if loaded:
                    self.pokemon_coords = loaded
                    return loaded
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"❌ Erro ao carregar coords.json: {e}")
        return {}
    
    def get_region_folder(self, pokemon_id):
        if 1 <= pokemon_id <= 151: return "Kanto"
        elif 152 <= pokemon_id <= 251: return "Johto"
        elif 252 <= pokemon_id <= 386: return "Hoenn"
        elif 387 <= pokemon_id <= 493: return "Sinnoh"
        elif 494 <= pokemon_id <= 649: return "Unova"
        return "Geral"

    def get_pokemon_config(self, pokemon_name):
        self._load_coords()
        
        pokemon_name_lower = pokemon_name.lower()
        config = self.pokemon_coords.get(pokemon_name_lower, {
            "x": 200, "y": 110, "bg": "normal.jpeg"
        })
        return config
    
    def get_background_path(self, bg_filename):
        caminho_completo = os.path.join(self.bg_dir, bg_filename)
        if os.path.exists(caminho_completo):
            return caminho_completo
        
        try:
            tipo_base = bg_filename.split('.')[0]
            for arquivo in os.listdir(self.bg_dir):
                if arquivo.split('.')[0] == tipo_base:
                    return os.path.join(self.bg_dir, arquivo)
        except: pass
        return None

    def get_frame_durations(self, img):
        duracoes = []
        for frame in ImageSequence.Iterator(img):
            duracao = frame.info.get('duration', 100)
            if duracao < 20: duracao = 100
            elif duracao > 200: duracao = 80
            duracoes.append(duracao)
        return duracoes
            
    def process_and_save_gif(self, img_original, caminho_salvamento, escala=3):
        os.makedirs(os.path.dirname(caminho_salvamento), exist_ok=True)
        frames_redimensionados = []
        duracoes = self.get_frame_durations(img_original)
        
        for frame in ImageSequence.Iterator(img_original):
            frame_rgba = frame.convert("RGBA")
            nova_size = (int(frame_rgba.width * escala), int(frame_rgba.height * escala))
            frame_grande = frame_rgba.resize(nova_size, Image.NEAREST)
            frames_redimensionados.append(frame_grande)
        
        frames_redimensionados[0].save(
            caminho_salvamento, save_all=True, append_images=frames_redimensionados[1:],
            duration=duracoes, loop=0, disposal=2, optimize=True
        )
        return caminho_salvamento
        
    def get_image_data(self, pokemon_data, is_shiny):
        # Pegar ID e Nome do banco
        pokemon_id = pokemon_data['_id']
        pokemon_name = pokemon_data['name'].lower()
        nome_do_arquivo = f"{'Shiny_' if is_shiny else ''}{pokemon_name}.gif"
        
        regiao = self.get_region_folder(pokemon_id)
        caminho_sprite = os.path.join(self.project_root, 'cache', 'cache_gifs', regiao, nome_do_arquivo)
        
        # Se ja existe no cache, retorna
        if os.path.exists(caminho_sprite):
            return caminho_sprite
        
        tipo_sprite = "shiny" if is_shiny else "default"
        url_gif = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-v/black-white/animated/{'shiny/' if is_shiny else ''}{pokemon_id}.gif"
        
        try:
            response = requests.get(url_gif, timeout=10)
            if response.status_code != 200:
                # Se não tiver animado, tenta o estático
                url_static = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{'shiny/' if is_shiny else ''}{pokemon_id}.png"
                response = requests.get(url_static, timeout=10)
            
            img = Image.open(BytesIO(response.content))
            return self.process_and_save_gif(img, caminho_sprite)
        except Exception as e:
            print(f"❌ Erro ao baixar sprite para {pokemon_name}: {e}")
            return None

    def create_final_spawn_gif(self, caminho_pokemon, caminho_bg, pokemon_name):
        if not caminho_pokemon or not caminho_bg: return None
        
        pkm_gif = Image.open(caminho_pokemon)
        bg_raw = Image.open(caminho_bg).convert("RGBA")
        
        # Redimensionar fundo
        largura_alvo = 600
        proporcao = largura_alvo / float(bg_raw.size[0])
        altura_alvo = int((float(bg_raw.size[1]) * proporcao))
        bg_image = bg_raw.resize((largura_alvo, altura_alvo), Image.LANCZOS)
        
        pokemon_config = self.get_pokemon_config(pokemon_name)
        coords = (pokemon_config["x"], pokemon_config["y"])
        duracoes = self.get_frame_durations(pkm_gif)
        
        final_frames = []
        for frame in ImageSequence.Iterator(pkm_gif):
            temp_bg = bg_image.copy()
            p_frame = frame.convert("RGBA")
            temp_bg.paste(p_frame, coords, p_frame)
            final_frames.append(temp_bg.convert("P", palette=Image.ADAPTIVE))
        
        output = BytesIO()
        final_frames[0].save(
            output, format="GIF", save_all=True, append_images=final_frames[1:],
            duration=duracoes, loop=0, disposal=2, optimize=True
        )
        output.seek(0) 
        return output