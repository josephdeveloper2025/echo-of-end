# Importa as bibliotecas necessárias para a aplicação web e requisições HTTP
from flask import Flask, request, jsonify # Flask para criar o servidor web, request para lidar com requisições, jsonify para retornar JSON
from flask_cors import CORS # Flask-CORS para lidar com políticas de Cross-Origin Resource Sharing (CORS)
import requests # Para fazer requisições HTTP para APIs externas
import os # Para interagir com o sistema operacional, como ler variáveis de ambiente
from dotenv import load_dotenv # Importa load_dotenv para carregar variáveis do .env

# Carrega as variáveis de ambiente do ficheiro .env (se existir)
load_dotenv()

# Inicializa a aplicação Flask
app = Flask(__name__)
# Habilita CORS para todas as rotas e origens.
# EM AMBIENTE DE PRODUÇÃO, É ALTAMENTE RECOMENDÁVEL RESTRINGIR ISSO
# PARA O DOMÍNIO ESPECÍFICO DO SEU FRONTEND POR RAZÕES DE SEGURANÇA.
# Ex: CORS(app, origins="http://seu-dominio.com")
CORS(app)

# --- Configuração da Chave API do NewsAPI.ai ---
# A chave API é lida da variável de ambiente `NEWSAPI_AI_API_KEY`.
# É crucial que esta variável esteja definida no ambiente onde o backend está a correr (localmente ou no Render).
NEWSAPI_AI_API_KEY = os.environ.get('NEWSAPI_AI_API_KEY')

# Verifica se a chave API foi definida. Se não, imprime um erro no console do backend.
if not NEWSAPI_AI_API_KEY:
    print("ERRO CRÍTICO NO BACKEND: A chave API do NewsAPI.ai não foi definida!")
    print("Por favor, verifique se 'NEWSAPI_AI_API_KEY' está configurada nas variáveis de ambiente do Render.")
    # Em produção, pode-se querer sair da aplicação aqui se a chave for essencial.

# --- Rota para Procurar Notícias ---
# Este endpoint '/api/news' será o ponto de comunicação para o seu frontend.
# Ele aceitará requisições GET.
@app.route('/api/news', methods=['GET'])
def get_news():
    """
    Endpoint para procurar notícias mundiais usando a NewsAPI.ai.
    Recebe o parâmetro 'query' da requisição GET do frontend.
    Faz a chamada segura para a NewsAPI.ai e retorna os resultados JSON.
    """
    # Obtém o valor do parâmetro 'query' da URL da requisição (ex: /api/news?query=guerra).
    # 'notícias mundiais' é um valor padrão se nenhum 'query' for fornecido.
    search_query = request.args.get('query', 'notícias mundiais')

    # Validação simples para garantir que uma query foi fornecida.
    if not search_query:
        return jsonify({"error": "Parâmetro 'query' é obrigatório"}), 400

    # Verifica novamente se a chave API está disponível antes de fazer a chamada à API externa.
    if not NEWSAPI_AI_API_KEY:
        # Retorna um erro 500 se a chave não for encontrada, pois é um erro de configuração do servidor.
        return jsonify({"error": "Erro de configuração do servidor: Chave API do NewsAPI.ai não encontrada no backend."}), 500

    # --- Parâmetros para a chamada da NewsAPI.ai ---
    # Documentação da API: https://newsapi.ai/documentation
    # Endpoint de busca: https://newsapi.ai/api/v1/search
    params = {
        'apiKey': NEWSAPI_AI_API_KEY, # Sua chave API
        'q': search_query,            # A string de procura fornecida pelo utilizador
        'language': 'pt',             # Idioma dos resultados (Português)
        'country': 'br',              # País dos resultados (Brasil). NewsAPI.ai pode ser mais global por padrão dependendo do plano.
        'articlesPage': 1,            # Página de artigos (1 é a primeira página). Cuidado com limites de plano!
        'results': 10,                # Número de resultados por página
        'sortBy': 'relevancy'         # Ordenar por relevância
    }

    try:
        # Faz a requisição HTTP GET para o endpoint de procura da NewsAPI.ai
        newsapi_response = requests.get('https://newsapi.ai/api/v1/search', params=params)
        
        # Loga a URL completa da requisição para depuração no Render
        print(f"DEBUG: URL de requisição para NewsAPI.ai: {newsapi_response.url}")
        
        # Levanta uma exceção HTTPError se a resposta da NewsAPI.ai tiver um status de erro (4xx ou 5xx).
        newsapi_response.raise_for_status()

        # Converte o corpo da resposta JSON em um dicionário Python
        newsapi_data = newsapi_response.json()
        print(f"DEBUG: Resposta bruta do NewsAPI.ai para a query '{search_query}': {newsapi_data}") # Log detalhado da resposta

        # --- Processamento dos resultados para o formato esperado pelo frontend ---
        processed_articles = []
        # A NewsAPI.ai retorna os artigos dentro da chave 'articles'
        if 'articles' in newsapi_data and newsapi_data['articles']:
            for article in newsapi_data['articles']:
                # Mapeia os campos da resposta da NewsAPI.ai para o formato que seu frontend espera
                processed_articles.append({
                    'title': article.get('title', 'Título não disponível'),
                    'snippet': article.get('description', 'Descrição não disponível'),
                    'link': article.get('url', '#'),
                    'thumbnail': article.get('image', None), # NewsAPI.ai usa 'image' para a URL da imagem
                    'source': article.get('source', {}).get('title', 'Fonte desconhecida'), # NewsAPI.ai tem 'source' como objeto com 'title'
                    'date': article.get('publishedAt', 'Data não disponível').split('T')[0] # Pega apenas a parte da data
                })
            return jsonify(processed_articles), 200 # Retorna a lista de notícias processadas com status 200 (OK)
        else:
            # Caso a API não retorne artigos ou a estrutura seja diferente
            print(f"DEBUG: NewsAPI.ai retornou sem artigos ou estrutura inesperada para '{search_query}'. Resposta: {newsapi_data}")
            # Retornamos um 404 para o frontend se não há artigos, informando que a busca não encontrou nada.
            return jsonify({"message": "Nenhuma notícia encontrada ou estrutura de resposta inesperada do NewsAPI.ai."}), 404

    except requests.exceptions.RequestException as e:
        # Captura exceções relacionadas a problemas de rede (DNS, conexão, timeout, SSL, etc.)
        # ou respostas HTTP de erro da NewsAPI.ai (ex: 401 Unauthorized, 403 Forbidden, 429 Too Many Requests).
        print(f"ERRO: Erro ao chamar o NewsAPI.ai (conexão/HTTP): {e}")
        # Tenta obter mais detalhes do erro da resposta HTTP se for um HTTPError
        if hasattr(e, 'response') and e.response is not None:
            print(f"ERRO: Status da resposta NewsAPI.ai: {e.response.status_code}")
            print(f"ERRO: Corpo da resposta NewsAPI.ai: {e.response.text}")
            return jsonify({"error": f"Erro da API de notícias: Status {e.response.status_code} - {e.response.text}"}), 500
        else:
            return jsonify({"error": f"Erro ao conectar com a API de notícias: {str(e)}"}), 500
    except Exception as e:
        # Captura qualquer outro erro inesperado que possa ocorrer no processamento
        print(f"ERRO: Erro inesperado no backend: {e}")
        return jsonify({"error": f"Erro interno do servidor: {str(e)}"}), 500

# --- Execução da Aplicação Flask (APENAS PARA DESENVOLVIMENTO LOCAL) ---
# Este bloco deve estar no nível superior de indentação (sem espaços à esquerda)
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
