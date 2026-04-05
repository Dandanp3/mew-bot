import os
import random
from PIL import Image, ImageSequence
from io import BytesIO
import requests

class SpawnController:
    def __init__(self, project_root):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.dirname(os.path.dirname(current_dir))
        
        
        self.bg_dir = os.path.join(project_root, 'cache', 'Background')
        
        # Formato: (pos_x, pos_y)
        self.bg_positions = {
            "fire": (150, 250),   
            "water": (150, 180),  
            "grass": (150, 200),

        }
    
    def get_region_folder(self, pokemon_id):
        if 1 <= pokemon_id <= 151:
            return "Kanto"
        elif 152 <= pokemon_id <= 251:
            return "Johto"
        
    def get_background_data(self, types_list):
        # extrai os nomes dos tipos e sorteia um
        tipos_disponiveis = [t['type']['name'] for t in types_list]
        tipo_escolhido = random.choice(tipos_disponiveis)
        
        arquivos_no_diretorio = os.listdir(self.bg_dir)
        
        #procurando o background correto de acordo com a tipagem
        for n in arquivos_no_diretorio:
            if n.startswith(tipo_escolhido):
                bg = n
                
                if bg:
                    caminho_completo = os.path.join(self.bg_dir, bg)

                    # pegando as coordenadas da tabela
                    coords = self.bg_positions.get(tipo_escolhido, (150, 200)) # padrao se n tiver na tabela
                    return caminho_completo, coords
                
                break
            
    # Funçao para redimensionar o tamanho dos sprites
    def process_and_save_gif(self, img_original, caminho_salvamento, escala=3):
        frames_redimensionados = []
        
        for frame in ImageSequence.Iterator(img_original):
            # converter para rgba (n perde transparencia)
            frame_rgba = frame.convert("RGBA")
            
            #calculando novas dimensões
            nova_largura = int(frame_rgba.width * escala)
            nova_altura = int(frame_rgba.height * escala)
            
            # redimensionando 
            frame_grande = frame_rgba.resize((nova_largura, nova_altura), Image.NEAREST)
            frames_redimensionados.append(frame_grande)
        
        #salvando lisrta de frames
        duracao_original = img_original.info.get('duration', 100)
        
        frames_redimensionados[0].save(
            caminho_salvamento,
            save_all=True,
            append_images=frames_redimensionados[1:],
            duration=duracao_original,
            loop=0,
            disposal=2   
        )
        return caminho_salvamento
        
        
        
    def get_image_data(self, pokemon_data, is_shiny):
        pokemon_id = pokemon_data['id']
        pokemon_name = pokemon_data['name'].lower()
        
        # definindo nome do arquivo
        if is_shiny:
            nome_do_arquivo = f"Shiny_{pokemon_name}.gif"
        else:
            nome_do_arquivo = f"{pokemon_name}.gif"
        
        # Usando a funçao de pegar regiao
        regiao = self.get_region_folder(pokemon_id)
        caminho_sprite = os.path.join(self.project_root, 'cache', 'cache_gifs', regiao, nome_do_arquivo)
        
        # verifica se ja existe no cache
        if os.path.exists(caminho_sprite):
            return caminho_sprite
        
        # se nao, vai fazer um
        else:
            
            gen5 = pokemon_data['sprites']['versions']['generation-v']['black-white']['animated']
            
            if is_shiny:
                url_gif = gen5['front_shiny']
            else:
                url_gif = gen5['front_default']
        
            sprite_baixado = requests.get(url_gif).content
            img = Image.open(BytesIO(sprite_baixado))
            
            return self.process_and_save_gif(img, caminho_sprite)
    
    def create_final_spawn_gif(self, caminho_pokemon, caminho_bg, coords):
        pkm_gif = Image.open(caminho_pokemon)
        bg_image = Image.open(caminho_bg).convert("RGBA")
        
        final_frames = []
        
        for frame in ImageSequence.Iterator(pkm_gif):
            # cria uma copia do fundo pra esse frame
            temp_bg = bg_image.copy()
            
            # converter para rgba por segurança
            p_frame = frame.convert("RGBA")
            
            #colando pokemon no fundo
            temp_bg.paste(p_frame, coords, p_frame)
            final_frames.append(temp_bg)
        
        # transforma a lista em um arquivo de bytes
        output = BytesIO()
        final_frames[0].save(
            output,
            format="GIF",
            save_all=True,
            append_images=final_frames[1:],
            duration=pkm_gif.info.get('duration', 100),
            loop=0,
            disposal=2
        )
        output.seek(0)
        return output
        
        
        
        
        
         
        

            