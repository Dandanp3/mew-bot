import os
import random
from PIL import Image, ImageSequence
from io import BytesIO

class SpawnController:
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        
        
        self.bg_dir = os.path.join(project_root, 'cache', 'Background')
        
        # Formato: "nome_do_tipo": (pos_x, pos_y)
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
        
    def get_image_data(self):
        
        self.pokemon_sprite = os.path.join(project_root, 'cache', 'cache_gifs', '')     
        

            