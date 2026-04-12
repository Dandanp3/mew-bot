import os
import json
from PIL import Image, ImageSequence
from io import BytesIO
import requests

class SpawnController:
    def __init__(self, project_root):
        self.project_root = project_root
        self.bg_dir = os.path.join(self.project_root, 'cache', 'Background')
        self.cache_json_dir = os.path.join(self.project_root, 'cache', 'cache_gifs')
        os.makedirs(self.cache_json_dir, exist_ok=True)
        
        self.coords_file = os.path.join(self.project_root, 'server', 'config', 'coords.json')
        self.pokemon_coords = {}
        self._load_coords()
    
    def _load_coords(self):
        try:
            with open(self.coords_file, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                if loaded:
                    self.pokemon_coords = loaded
                    return loaded
        except (FileNotFoundError, json.JSONDecodeError):
            pass
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
        return self.pokemon_coords.get(pokemon_name.lower(), {"x": 200, "y": 110, "bg": "normal.jpeg"})

    def get_background_path(self, bg_filename):
        caminho = os.path.join(self.bg_dir, bg_filename)
        if os.path.exists(caminho): return caminho
        try:
            base = bg_filename.split('.')[0]
            for f in os.listdir(self.bg_dir):
                if f.split('.')[0] == base: return os.path.join(self.bg_dir, f)
        except: pass
        return None

    # --- SISTEMA DE CACHE JSON ---
    def get_cached_url(self, region, pokemon_name, is_shiny):
        file_path = os.path.join(self.cache_json_dir, f"{region.lower()}.json")
        if not os.path.exists(file_path): return None
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get(f"{pokemon_name.lower()}_{'shiny' if is_shiny else 'normal'}")
        except: return None

    def save_cached_url(self, region, pokemon_name, is_shiny, url):
        file_path = os.path.join(self.cache_json_dir, f"{region.lower()}.json")
        data = {}
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f: data = json.load(f)
            except: pass
        data[f"{pokemon_name.lower()}_{'shiny' if is_shiny else 'normal'}"] = url
        with open(file_path, 'w', encoding='utf-8') as f: json.dump(data, f, indent=4)

    # --- LÓGICA DE FRAMES DO CÓDIGO ANTIGO ---
    def get_frame_durations(self, img):
        duracoes = []
        for frame in ImageSequence.Iterator(img):
            duracao = frame.info.get('duration', 100)
            if duracao < 20: duracao = 100
            elif duracao > 200: duracao = 80
            duracoes.append(duracao)
        return duracoes

    def get_image_data_memory(self, pokemon_data, is_shiny, escala=3):
        # Esta função faz o que seu 'process_and_save_gif' fazia, mas sem salvar no HD
        pokemon_id = pokemon_data['_id']
        url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-v/black-white/animated/{'shiny/' if is_shiny else ''}{pokemon_id}.gif"
        
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{'shiny/' if is_shiny else ''}{pokemon_id}.png"
                resp = requests.get(url, timeout=10)
            
            pkm_img = Image.open(BytesIO(resp.content))
            
            # Redimensiona os frames do Pokémon IGUAL ao seu código antigo
            frames_redimensionados = []
            for frame in ImageSequence.Iterator(pkm_img):
                frame_rgba = frame.convert("RGBA")
                nova_size = (int(frame_rgba.width * escala), int(frame_rgba.height * escala))
                frames_redimensionados.append(frame_rgba.resize(nova_size, Image.NEAREST))
            
            # Retorna a lista de frames e a imagem original para as durações
            return frames_redimensionados, self.get_frame_durations(pkm_img)
        except: return None, None

    def create_final_spawn_gif(self, frames_pkm, duracoes, caminho_bg, pokemon_name):
        if not frames_pkm or not caminho_bg: return None
        
        bg_raw = Image.open(caminho_bg).convert("RGBA")
        
        # Redimensionamento do fundo IGUAL ao antigo
        largura_alvo = 600
        proporcao = largura_alvo / float(bg_raw.size[0])
        altura_alvo = int((float(bg_raw.size[1]) * proporcao))
        bg_image = bg_raw.resize((largura_alvo, altura_alvo), Image.LANCZOS)
        
        pokemon_config = self.get_pokemon_config(pokemon_name)
        coords = (pokemon_config["x"], pokemon_config["y"])
        
        final_frames = []
        for p_frame in frames_pkm:
            temp_bg = bg_image.copy()
            # O paste usa o frame do pkm como máscara para manter transparência
            temp_bg.paste(p_frame, coords, p_frame)
            final_frames.append(temp_bg.convert("P", palette=Image.ADAPTIVE))
        
        output = BytesIO()
        final_frames[0].save(
            output, format="GIF", save_all=True, append_images=final_frames[1:],
            duration=duracoes, loop=0, disposal=2, optimize=True
        )
        output.seek(0)
        return output