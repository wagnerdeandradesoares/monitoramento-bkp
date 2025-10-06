from PIL import Image
import os

# Caminhos das imagens
file_paths = {
    "Instalador": r"C:\Users\wagner.soares\Desktop\Monitoramento BKP\icons\Instalador.png",
}


# Pasta de saída
output_dir = "ico_outputs"
os.makedirs(output_dir, exist_ok=True)

# Função de conversão
def convert_to_ico(image_path, output_name):
    with Image.open(image_path) as img:
        img = img.convert("RGBA")
        img = img.resize((256, 256), Image.LANCZOS)
        output_path = os.path.join(output_dir, f"{output_name}.ico")
        img.save(output_path, format="ICO", sizes=[(256, 256)])
        print(f"Convertido: {output_path}")

# Converter todas as imagens
for name, path in file_paths.items():
    convert_to_ico(path, name)
