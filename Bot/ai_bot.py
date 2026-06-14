import os
import requests
from langchain_groq import ChatGroq
from langchain_postgres.vectorstores import PGVector # Importe PGVector
from langchain.chains.combine_documents import create_stuff_documents_chain # Retorna um chain pronto
from langchain.chains.retrieval import create_retrieval_chain # Chain que usa o retriever (busca nos dados)
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import random # NOVO: Módulo para fazer a escolha aleatória
import psycopg # NOVO: Biblioteca para conectar diretamente ao PostgreSQL
from psycopg import sql # NOVO: Para construir a query SQL de forma segura
from geraImagem import GeraImagem
from enviaEmail import GmailSender


load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

model = ChatGroq(
    model = "moonshotai/kimi-k2-instruct",
)

# --- Configurações do PostgreSQL ---
# Use as credenciais que você confirmou no EasyPanel e no DBeaver
# É altamente recomendado colocar essas variáveis no seu arquivo .env para segurança!
PG_HOST = os.getenv("PG_HOST") # O IP público do seu servidor Hostinger
PG_PORT = os.getenv("PG_PORT")
PG_DATABASE = os.getenv("PG_DATABASE") # O nome do banco de dados do EasyPanel
PG_USER = os.getenv("PG_USER") # O usuário do banco de dados
PG_PASSWORD = os.getenv("PG_PASSWORD") # A senha do banco de dados

# String de conexão para o PGVector
CONNECTION_STRING = PGVector.connection_string_from_db_params(
    host=PG_HOST,
    port=PG_PORT,
    database=PG_DATABASE,
    user=PG_USER,
    password=PG_PASSWORD,
    driver="psycopg",
)

# --- NOVA FUNÇÃO: Para buscar os nomes dos livros no banco de dados ---
def get_available_books(db_params: dict, collection_name: str) -> list[str]:
    """
    Conecta ao banco de dados PostgreSQL e busca todos os valores únicos
    do metadado 'source' da tabela de coleção.
    """
    book_files = []
    try:
        # A conexão usa apenas os parâmetros do banco de dados.
        with psycopg.connect(**db_params) as conn:
            with conn.cursor() as cur:
                # O collection_name é usado apenas para construir a query SQL.
                query = sql.SQL(f"SELECT distinct cmetadata FROM vector.langchain_pg_embedding where collection_id = (select uuid from vector.langchain_pg_collection where name = '{collection_name}')")
                cur.execute(query)
                results = cur.fetchall()
                book_files = [item[0] for item in results]
    except Exception as e:
        print(f"Erro ao buscar livros no banco de dados: {e}")
    return book_files

# --- Alteração aqui: Definindo o schema e o nome da tabela ---
COLLECTION_NAME = "livros_embeddings" # Usamos o mesmo nome de coleção do rag.py

embedding = HuggingFaceEmbeddings()
# --- Inicialização do PGVector para recuperação ---
vector_store = PGVector(
    connection=CONNECTION_STRING,
    embeddings=embedding,
    collection_name=COLLECTION_NAME, # Usamos o COLLECTION_NAME com o schema
)

# --- LÓGICA PRINCIPAL ---
# 1. Pega a lista de todos os livros disponíveis no banco de dados
print("Buscando a lista de livros disponíveis no banco de dados...")
# Dicionário com os parâmetros *apenas para a conexão*
db_connection_params = {
    "host": PG_HOST,
    "port": PG_PORT,
    "dbname": PG_DATABASE,
    "user": PG_USER,
    "password": PG_PASSWORD,
}

def executa_tabela_sheet():
    url = "https://script.google.com/macros/s/AKfycbx2v6YovcHwQEr3488xOr08vlzMQApIy2f_LxWu76vXkZc_j87OYFj0tk0NW5444y_i/exec?action=getInfo"

    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        
        # Process the data as needed
        return data
    else:
        print(f"Erro ao buscar informações da tabela: {response.status_code}")

executar = False

tabela = executa_tabela_sheet()

for i in tabela:
    linha = i["linha"]
    book_file_name = i["livro"]
    executar = i["executar"]
    post_storie = i["post_storie"]

    print(f"Linha: {linha}, Livro: {book_file_name}, Executar: {executar}")
    
    if executar == True:
        break

if executar == False:
    raise Exception("Nenhum livro selecionado para execução. Verifique a tabela.")

# available_books = get_available_books(db_params=db_connection_params, collection_name=COLLECTION_NAME)

# # 2. Verifica se algum livro foi encontrado e escolhe um aleatoriamente
# if not available_books:
#     print("Nenhum livro encontrado no banco de dados. Verifique sua coleção e a conexão.")
#     exit()

# # ALTERADO: Em vez de definir o nome manualmente, escolhemos um da lista
# book_file_name = random.choice(available_books)
print(f"\n--- Livro selecionado para a postagem: {book_file_name} ---\n")


# 2. Configure o retriever para filtrar pelo nome do arquivo
# O filter fará a busca apenas nos chunks que possuem o metadado 'source' igual ao nome do arquivo
retriever = vector_store.as_retriever(
    search_type="mmr",
    search_kwargs={
        "k": 4, # Busque 4 chunks deste livro
        "fetch_k": 10,
        "filter": {"source": {"$eq": book_file_name}} # Filtra pelo metadado
    }
)

# retriever = vector_store.as_retriever(search_kwargs={"k": 4, "filter": {"source": book_file_name}})
# retriever = vector_store.as_retriever(search_type="mmr", search_kwargs={"k": 1, "fetch_k": 10})

# Monta o prompt
system_prompt = '''
Use o contexto para responder as perguntas.
Contexto: {context}
'''

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{input}"),
    ]
)

# Cria um chain já pré preenchido (feito pela comunidade do langchain)
question_answer_chain = create_stuff_documents_chain(
    llm=model,
    prompt=prompt,
)
chain = create_retrieval_chain(
    retriever=retriever,
    combine_docs_chain=question_answer_chain,
)

query = "Quero que você crie uma postagem para o Instagram, dando detalhes sobre a trama para prender a atenção e aumentar a venda do livro. O tema da postagem deve condizer com o tema principal. Não force nada no texto, apenas faça uma postagem que prenda a atenção do público, evite o uso de emojis, o tom é sério. Obs.: Os personagens devem condizer com a história do livro que você está buscando no contexto. Não invente nada, apenas use o contexto para criar a postagem."

response = chain.invoke(
    {"input": query},
)

print(response["answer"])
resposta = response["answer"]


print("Gerando imagem")
query_imagem = f"Me dê um prompt para enviar para o DALL-E e gerar uma imagem para a postagem no instagram (a imagem deve ser séria para o intuito do nosso agente). O prompt deve ser em inglês e descritivo, para que a imagem seja gerada de forma correta. Adicione no prompt a informação para gerar o nome do escritor: 'Alex Bitten' no topo da imagem. Não gere como uma capa de um livro, e sim como uma imagem para contextualizar o trecho do livro. Contexto para a criação do prompt da imagem: {resposta}"

response_imagem = chain.invoke(
    {"input": query_imagem},
)

print(response_imagem["answer"])
resposta_imagem = response_imagem["answer"]

try:
    # 1. Tarefa de geração de imagem
    imagem = GeraImagem()
    local_imagem = imagem.geracao_imagem(prompt_imagem=resposta_imagem, tipo_imagem=post_storie)

    # 2. Tarefa de Envio de E-mail
    gmail_sender = GmailSender()
    destinatario = ["nicolaspn09@gmail.com", "alexandre_bittencourt@hotmail.com"]

    gmail_sender.send_email(
        to=destinatario,
        subject=f"""Instagram - Livro {str(book_file_name).replace(".docx", "").strip()}""",
        body=f"""Olá!\n\nSegue a proposta para a geração do post para o livro {str(book_file_name).replace(".docx", "").strip()}:\n\n{str(resposta).split("---")[0].strip()}""",
        attachment_path=local_imagem
    )

    # 3. Tarefa de Limpeza
    imagem.cleanup_file(local_imagem)

except Exception as e:
    print(f"Erro ao executar o bot: {e}")
    # 2. Tarefa de Envio de E-mail
    gmail_sender = GmailSender()
    destinatario = ["nicolaspn09@gmail.com", "alexandre_bittencourt@hotmail.com"]
    
    gmail_sender.send_email(
        to=destinatario,
        subject=f"""ERRO - Bot - Livro {str(book_file_name).replace(".docx", "").strip()}""",
        body=f"""Olá!\n\nErro ao gerar imagem para o livro {str(book_file_name).replace(".docx", "").strip()}:\n\n{str(e)}""",
    )