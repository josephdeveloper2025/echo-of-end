# Importa as bibliotecas necessárias para a aplicação web e requisições HTTP
from flask import Flask, request, jsonify # Flask para criar o servidor web, request para lidar com requisições, jsonify para retornar JSON
from flask_cors import CORS # Flask-CORS para lidar com políticas de Cross-Origin Resource Sharing (CORS)
import requests # Para fazer requisições HTTP para APIs externas
import os # Para interagir com o sistema operacional, como ler variáveis de ambiente

# Inicializa a aplicação Flask
app = Flask(__name__)
# Habilita CORS para todas as rotas e origens.
# EM AMBIENTE DE PRODUÇÃO, É ALTAMENTE RECOMENDÁVEL RESTRINGIR ISSO
# PARA O DOMÍNIO ESPECÍFICO DO SEU FRONTEND POR RAZÕES DE SEGURANÇA.
# Ex: CORS(app, origins="http://seu-dominio.com")
CORS(app)

# --- Configuração da Chave API da SerpApi ---
# É CRÍTICO armazenar chaves API como variáveis de ambiente, especialmente em produção.
# Isso evita que sua chave seja exposta diretamente no código-fonte e em repositórios públicos.
# O `os.environ.get()` tenta buscar a variável de ambiente `SERPAPI_API_KEY`.
# O segundo argumento é um valor padrão caso a variável de ambiente não seja encontrada.
# Este valor padrão é sua chave, incluída aqui para facilitar o teste local.
SERPAPI_API_KEY = os.environ.get('SERPAPI_API_KEY', 'd84bc1abcf90136956eb186041bed1e9cb47bed87b4b6f92541a2db5cfc101c7')

# Verifica se a chave API foi definida e avisa se não.
if not SERPAPI_API_KEY:
    print("ERRO: A chave API da SerpApi não foi definida!")
    print("Por favor, defina a variável de ambiente 'SERPAPI_API_KEY' ou edite 'app.py' com sua chave.")
    print("Para definir no terminal (Linux/macOS): 'export SERPAPI_API_KEY=\"sua_chave_aqui\"'")
    print("Ou use um arquivo .env e a biblioteca python-dotenv.")

# --- Rota para Buscar Notícias ---
# Este endpoint '/api/news' será o ponto de comunicação para o seu frontend.
# Ele aceitará requisições GET.
@app.route('/api/news', methods=['GET'])
def get_news():
    """
    Endpoint para buscar notícias mundiais usando a SerpApi.
    Recebe o parâmetro 'query' da requisição GET do frontend.
    Faz a chamada segura para a SerpApi e retorna os resultados JSON.
    """
    # Obtém o valor do parâmetro 'query' da URL da requisição (ex: /api/news?query=guerra).
    # 'notícias mundiais' é um valor padrão se nenhum 'query' for fornecido.
    search_query = request.args.get('query', 'notícias mundiais')

    # Validação simples para garantir que uma query foi fornecida.
    if not search_query:
        return jsonify({"error": "Parâmetro 'query' é obrigatório"}), 400

    # Parâmetros que serão enviados na requisição para a SerpApi.
    params = {
        'api_key': SERPAPI_API_KEY, # Sua chave API
        'engine': 'google_news',   # Especifica que queremos resultados do Google Notícias
        'q': search_query,         # A string de busca fornecida pelo usuário
        'hl': 'pt',                # Idioma dos resultados (Português)
        'gl': 'br',                # Localização geográfica para os resultados (Brasil). Pode ser ajustado para global.
        'num': 10                  # Número de resultados a serem retornados (máximo de 100 por requisição na SerpApi)
    }

    try:
        # Faz a requisição HTTP GET para o endpoint da SerpApi
        response = requests.get('https://serpapi.com/search', params=params)
        # `raise_for_status()` verifica se a requisição foi bem-sucedida (status 2xx).
        # Se não for, ele levanta uma exceção HTTPError.
        response.raise_for_status()

        # Converte o corpo da resposta JSON em um dicionário Python
        data = response.json()
        print(f"DEBUG: Resposta bruta da SerpApi para a query '{search_query}': {data}") # Log para depuração

        # Verifica se o campo 'news_results' existe na resposta da SerpApi
        if 'news_results' in data:
            # Retorna apenas a lista de notícias (news_results) para o frontend.
            # O status 200 indica sucesso.
            return jsonify(data['news_results']), 200
        else:
            # Se 'news_results' não for encontrado, informa que não há notícias ou a estrutura é inesperada.
            return jsonify({"message": "Nenhuma notícia encontrada ou estrutura de resposta inesperada da SerpApi."}), 404

    except requests.exceptions.RequestException as e:
        # Captura exceções relacionadas a problemas de rede, conexão, timeouts, etc.
        print(f"ERRO: Erro ao chamar a SerpApi (conexão/HTTP): {e}")
        # Retorna uma mensagem de erro genérica para o frontend com status 500 (Erro Interno do Servidor).
        return jsonify({"error": f"Erro ao conectar com a API de notícias: {str(e)}"}), 500
    except Exception as e:
        # Captura qualquer outra exceção inesperada que possa ocorrer.
        print(f"ERRO: Erro inesperado no backend: {e}")
        return jsonify({"error": f"Erro interno do servidor: {str(e)}"}), 500

# --- Execução da Aplicação Flask ---
# Este bloco garante que o servidor Flask só seja executado quando o script é chamado diretamente.
if __name__ == '__main__':
    # `app.run()` inicia o servidor web Flask.
    # `debug=True`: Ativa o modo de depuração. Útil para desenvolvimento (recarrega o servidor ao salvar, exibe erros detalhados).
    #               DESATIVE ISSO EM AMBIENTE DE PRODUÇÃO POR SEGURANÇA.
    # `host='0.0.0.0'`: Faz com que o servidor seja acessível de qualquer IP, não apenas do seu localhost.
    #                    Importante para cenários de deploy ou acesso de outras máquinas na mesma rede.
    # `port=5000`: Define a porta TCP/IP na qual o servidor irá escutar.
    app.run(debug=False, host='0.0.0.0', port=5000) # Mude debug para False
