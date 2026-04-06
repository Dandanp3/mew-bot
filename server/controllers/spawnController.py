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
        self.pokemon_coords = self._load_coords()
    
    def _load_coords(self):
 
        try:
            with open(self.coords_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️ Aviso: Arquivo '{self.coords_file}' não encontrado!")
            return {}
        except json.JSONDecodeError as e:
            print(f"❌ Erro ao decodificar JSON: {e}")
            return {}
    
    def get_region_folder(self, pokemon_id):
        if 1 <= pokemon_id <= 151:
            return "Kanto"
        elif 152 <= pokemon_id <= 251:
            return "Johto"
        return "Geral" 
    def get_pokemon_config(self, pokemon_name):
        coords = self._load_coords()
        
        pokemon_name_lower = pokemon_name.lower()
        config = coords.get(pokemon_name_lower, {
            "x": 200,
            "y": 110,
            "bg": "normal.jpeg"
        })
        return config
    
    def get_background_path(self, bg_filename):
        caminho_completo = os.path.join(self.bg_dir, bg_filename)
        
        if os.path.exists(caminho_completo):
            return caminho_completo
        try:
            arquivos = os.listdir(self.bg_dir)
            # Procurar por um arquivo que comece com o tipo
            tipo_base = bg_filename.split('.')[0]
            for arquivo in arquivos:
                if arquivo.split('.')[0] == tipo_base:
                    return os.path.join(self.bg_dir, arquivo)
        except Exception as e:
            print(f"Erro ao procurar background: {e}")
        
        return None
    
    def get_frame_durations(self, img):
        duracoes = []
        
        for frame in ImageSequence.Iterator(img):
            duracao = frame.info.get('duration', 100)
            
            # Ajusta durações muito baixas (< 20ms) ou muito altas (> 200ms)
            if duracao <= 0:
                duracao = 100
            elif duracao < 20:
                duracao = 100
            elif duracao > 200:
                duracao = 80
            
            duracoes.append(duracao)
        
        return duracoes
            
    def process_and_save_gif(self, img_original, caminho_salvamento, escala=3):
        os.makedirs(os.path.dirname(caminho_salvamento), exist_ok=True)
        
        frames_redimensionados = []
        duracoes = self.get_frame_durations(img_original)
        
        for frame in ImageSequence.Iterator(img_original):
            frame_rgba = frame.convert("RGBA")
            nova_largura = int(frame_rgba.width * escala)
            nova_altura = int(frame_rgba.height * escala)
            
            # NEAREST 
            frame_grande = frame_rgba.resize((nova_largura, nova_altura), Image.NEAREST)
            frames_redimensionados.append(frame_grande)
        
        frames_redimensionados[0].save(
            caminho_salvamento,
            save_all=True,
            append_images=frames_redimensionados[1:],
            duration=duracoes,  
            loop=0,
            disposal=2,
            optimize=True # Otimiza o tamanho do arquivo
        )
        return caminho_salvamento
        
    def get_image_data(self, pokemon_data, is_shiny):
        
        #Baixa e processa o sprite do Pokémon
        
        pokemon_id = pokemon_data['id']
        pokemon_name = pokemon_data['name'].lower()
        nome_do_arquivo = f"{'Shiny_' if is_shiny else ''}{pokemon_name}.gif"
        
        regiao = self.get_region_folder(pokemon_id)
        caminho_sprite = os.path.join(self.project_root, 'cache', 'cache_gifs', regiao, nome_do_arquivo)
        
        if os.path.exists(caminho_sprite):
            return caminho_sprite
        
        gen5 = pokemon_data['sprites']['versions']['generation-v']['black-white']['animated']
        url_gif = gen5['front_shiny'] if is_shiny else gen5['front_default']
        
        # Fallback se não houver gif animado na Gen 5
        if not url_gif:
            url_gif = pokemon_data['sprites']['front_shiny'] if is_shiny else pokemon_data['sprites']['front_default']
 
        sprite_baixado = requests.get(url_gif).content
        img = Image.open(BytesIO(sprite_baixado))
        
        return self.process_and_save_gif(img, caminho_sprite)
    
    def create_final_spawn_gif(self, caminho_pokemon, caminho_bg, pokemon_name):
        pkm_gif = Image.open(caminho_pokemon)
        
        # CARREGAR E REDIMENSIONAR O FUNDO
        bg_raw = Image.open(caminho_bg).convert("RGBA")
        largura_alvo = 600
        proporcao = largura_alvo / float(bg_raw.size[0])
        altura_alvo = int((float(bg_raw.size[1]) * proporcao))
        bg_image = bg_raw.resize((largura_alvo, altura_alvo), Image.LANCZOS)
        
        # Obter configuração do Pokémon 
        pokemon_config = self.get_pokemon_config(pokemon_name)
        coords = (pokemon_config["x"], pokemon_config["y"])
        
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