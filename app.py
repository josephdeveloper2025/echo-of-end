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

# --- Configuração da Chave API do NewsAPI.ai ---
NEWSAPI_AI_API_KEY = os.environ.get('NEWSAPI_AI_API_KEY')

if not NEWSAPI_AI_API_KEY:
    print("ERRO CRÍTICO NO BACKEND: A chave API do NewsAPI.ai não foi definida!")
    print("Por favor, verifique se 'NEWSAPI_AI_API_KEY' está configurada nas variáveis de ambiente do Render.")
    @app.route('/api/news', methods=['GET'])
    def missing_api_key_error_route():
        return jsonify({"error": "Erro de configuração do servidor: Chave API do NewsAPI.ai não encontrada no backend."}), 500

# --- Rota para Procurar Notícias ---
@app.route('/api/news', methods=['GET'])
def get_news():
    search_query = request.args.get('query', 'notícias mundiais')

    if not search_query:
        return jsonify({"error": "Parâmetro 'query' é obrigatório"}), 400

    if not NEWSAPI_AI_API_KEY:
        return jsonify({"error": "Erro de configuração do servidor: Chave API do NewsAPI.ai não encontrada no backend."}), 500

    params = {
        'apiKey': NEWSAPI_AI_API_KEY,
        'q': search_query,
        'language': 'pt',
        'country': 'br',
        'articlesPage': 1,
        'results': 10,
        'sortBy': 'relevancy'
    }

    try:
        # !!! LINHA CORRIGIDA: Adicionado 'api.' ao URL da NewsAPI.ai !!!
        newsapi_response = requests.get('https://api.newsapi.ai/api/v1/search', params=params)
        
        print(f"DEBUG: URL de requisição COMPLETA para NewsAPI.ai: {newsapi_response.url}")
        print(f"DEBUG: Status da resposta NewsAPI.ai: {newsapi_response.status_code}")
        
        newsapi_response.raise_for_status() # Levanta HTTPError para 4xx/5xx

        newsapi_data = newsapi_response.json()
        print(f"DEBUG: Resposta BRUTA do NewsAPI.ai para a query '{search_query}': {newsapi_data}")

        processed_articles = []
        if 'articles' in newsapi_data and newsapi_data['articles']:
            for article in newsapi_data['articles']:
                processed_articles.append({
                    'title': article.get('title', 'Título não disponível'),
                    'snippet': article.get('description', 'Descrição não disponível'),
                    'link': article.get('url', '#'),
                    'thumbnail': article.get('image', None),
                    'source': article.get('source', {}).get('title', 'Fonte desconhecida'),
                    'date': article.get('publishedAt', 'Data não disponível').split('T')[0]
                })
            return jsonify(processed_articles), 200
        else:
            print(f"DEBUG: NewsAPI.ai retornou sem artigos ou estrutura inesperada para '{search_query}'. Resposta: {newsapi_data}")
            return jsonify({"message": "Nenhuma notícia encontrada para a busca ou a NewsAPI.ai retornou uma resposta sem artigos. Verifique a consulta ou os limites do seu plano."}), 404

    except requests.exceptions.RequestException as e:
        print(f"ERRO: Erro ao chamar o NewsAPI.ai (conexão/HTTP): {e}")
        if hasattr(e, 'response') and e.response is not None:
            error_body = e.response.text
            try:
                error_json = e.response.json()
                error_body = error_json.get('errors', error_json.get('message', e.response.text))
            except ValueError:
                pass
            print(f"ERRO: Status da resposta NewsAPI.ai: {e.response.status_code}")
            print(f"ERRO: Corpo da resposta NewsAPI.ai: {error_body}")
            return jsonify({"error": f"Erro da API de notícias (NewsAPI.ai): Status {e.response.status_code} - {error_body}"}), e.response.status_code if e.response.status_code in [401, 403, 429] else 500
        else:
            return jsonify({"error": f"Erro ao conectar com a API de notícias (NewsAPI.ai): {str(e)}"}), 500
    except Exception as e:
        print(f"ERRO: Erro inesperado no backend: {e}")
        return jsonify({"error": f"Erro interno do servidor: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
