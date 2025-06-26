# Importa as bibliotecas necessárias para a aplicação web e requisições HTTP
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do ficheiro .env (se existir)
load_dotenv()

# Inicializa a aplicação Flask
app = Flask(__name__)
# Habilita CORS para todas as rotas e origens.
CORS(app)

# --- Configuração do Token API do theNewsAPI.com ---
# O token API é lido da variável de ambiente `THENEWSAPI_TOKEN`.
THENEWSAPI_TOKEN = os.environ.get('THENEWSAPI_TOKEN')

if not THENEWSAPI_TOKEN:
    print("ERRO CRÍTICO NO BACKEND: O token API do theNewsAPI.com NÃO ESTÁ CONFIGURADO!")
    print("Por favor, verifique se 'THENEWSAPI_TOKEN' está configurado nas variáveis de ambiente do Render.")
    @app.route('/api/news', methods=['GET'])
    def missing_api_token_error_route():
        return jsonify({"error": "Erro de configuração do servidor: Token API do theNewsAPI.com não encontrado no backend."}), 500

# --- Rota para Procurar Notícias ---
@app.route('/api/news', methods=['GET'])
def get_news():
    search_query = request.args.get('query', 'notícias mundiais')

    if not search_query:
        return jsonify({"error": "Parâmetro 'query' é obrigatório"}), 400

    if not THENEWSAPI_TOKEN:
        return jsonify({"error": "Erro de configuração do servidor: Token API do theNewsAPI.com não encontrado no backend."}), 500

    # --- Parâmetros para a chamada do theNewsAPI.com ---
    # Usaremos o endpoint 'all' para pesquisa geral.
    # Documentação da API: https://www.thenewsapi.com/documentation
    params = {
        'api_token': THENEWSAPI_TOKEN,  # Seu token API
        'search': search_query,         # A string de procura
        'language': 'pt',               # Idioma dos resultados (Português)
        'limit': 10                     # Número de resultados por página
    }

    try:
        thenewsapi_response = requests.get('https://api.thenewsapi.com/v1/news/all', params=params)
        
        print(f"DEBUG: URL de requisição COMPLETA para theNewsAPI.com: {thenewsapi_response.url}")
        print(f"DEBUG: Status da resposta theNewsAPI.com: {thenewsapi_response.status_code}")
        
        thenewsapi_response.raise_for_status() # Levanta HTTPError para 4xx/5xx

        thenewsapi_data = thenewsapi_response.json()
        print(f"DEBUG: Resposta BRUTA do theNewsAPI.com para a query '{search_query}': {thenewsapi_data}")

        processed_articles = []
        if thenewsapi_data.get('data'): # Verifica se 'data' existe e não está vazia
            for article in thenewsapi_data['data']:
                processed_articles.append({
                    'title': article.get('title', 'Título não disponível'),
                    'snippet': article.get('snippet', article.get('description', 'Descrição não disponível')),
                    'link': article.get('url', '#'),
                    'thumbnail': article.get('image_url', None),
                    'source': article.get('source', 'Fonte desconhecida'),
                    'date': article.get('published_at', 'Data não disponível').split(' ')[0]
                })
            return jsonify(processed_articles), 200
        else:
            print(f"DEBUG: theNewsAPI.com retornou sem artigos ou status inesperado para '{search_query}'. Resposta: {thenewsapi_data}")
            return jsonify({"message": "Nenhuma notícia encontrada para a busca ou a theNewsAPI.com retornou uma resposta sem artigos. Verifique a consulta ou os limites do seu plano."}), 404

    except requests.exceptions.RequestException as e:
        print(f"ERRO: Erro ao chamar o theNewsAPI.com (conexão/HTTP): {e}")
        if hasattr(e, 'response') and e.response is not None:
            error_body = e.response.text
            try:
                error_json = e.response.json()
                error_body = error_json.get('message', e.response.text) 
            except ValueError:
                pass
            print(f"ERRO: Status da resposta theNewsAPI.com: {e.response.status_code}")
            print(f"ERRO: Corpo da resposta theNewsAPI.com: {error_body}")
            return jsonify({"error": f"Erro da API de notícias (theNewsAPI.com): Status {e.response.status_code} - {error_body}"}), e.response.status_code if e.response.status_code in [401, 403, 429] else 500
        else:
            return jsonify({"error": f"Erro ao conectar com a API de notícias (theNewsAPI.com): {str(e)}"}), 500
    except Exception as e:
        print(f"ERRO: Erro inesperado no backend: {e}")
        return jsonify({"error": f"Erro interno do servidor: {str(e)}"}), 500

# --- ESTE BLOCO DEVE ESTAR NO INÍCIO DA LINHA, SEM ESPAÇOS OU TABULAÇÕES ANTES DELE ---
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
