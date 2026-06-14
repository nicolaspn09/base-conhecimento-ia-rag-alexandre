from Bot.ai_bot import AIBot

# Função para interagir com o bot no terminal
def run_bot(bot):
    print("Olá! Eu sou o assistente do escritor Alex Bitten. Como posso ajudar você hoje?")

    while True:
        # Recebe a entrada do usuário
        question = input("Você: ")

        # Encerra o bot se o usuário digitar 'sair'
        if question.lower() == "sair":
            print("Até logo!")
            break

        # Chama o método 'invoke' para gerar a resposta
        response = bot.invoke(question)

        # Verifica se a resposta é um dicionário e possui a chave 'text'
        if isinstance(response, dict) and 'text' in response:
            # Exibe a resposta do bot de forma legível, sem o texto "Você é um assistente virtual"
            print(f"\nBot: {response['text']}\n{'-'*50}")
        else:
            # Caso a resposta não seja um dicionário, extraímos o conteúdo da resposta diretamente
            response_text = str(response).strip()  # Converte para string e remove espaços extras
            print(f"\nBot: {response_text}\n{'-'*50}")

# Inicia o bot
if __name__ == "__main__":
    bot = AIBot()  # Cria uma instância do bot
    run_bot(bot)  # Executa o bot com a instância criada