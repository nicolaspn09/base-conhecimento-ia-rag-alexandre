from dotenv import load_dotenv
from openai import OpenAI
import os
import base64
import tempfile


class GeraImagem:
    def __init__(self):
        pass


    def geracao_imagem(self, prompt_imagem, tipo_imagem):
        load_dotenv()

        client = OpenAI(api_key=os.getenv("GPT_API_KEY"))
        
        prompt = f"""
        {prompt_imagem}
        """

        if str(tipo_imagem) == "1":
            size = "auto"
        elif str(tipo_imagem) == "2":
            size = "1024x1536"
        else:
            size = "auto"

        print(size)

        result = client.images.generate(
            model="gpt-image-1.5", # gpt-image-1
            prompt=prompt,
            # response_format="b64_json",
            size=size,
        )

        image_base64 = result.data[0].b64_json
        image_bytes = base64.b64decode(image_base64)

        temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        with open(temp_file.name, "wb") as f:
            f.write(image_bytes)
        
        print(f"Imagem salva temporariamente em: {temp_file.name}")
        return temp_file.name



    # --- FUNÇÃO DE LIMPEZA ---
    def cleanup_file(self, file_path: str):
        """
        Exclui um arquivo do sistema.
        """
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Arquivo temporário {file_path} excluído com sucesso.")
            except OSError as e:
                print(f"Erro ao excluir o arquivo {file_path}: {e}")