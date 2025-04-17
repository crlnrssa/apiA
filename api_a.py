from flask import Flask, jsonify
import requests
import redis
import json

app = Flask(__name__)

# URL da API B (que fornece a temperatura)
API_B_URL = "http://localhost:5001/weather/{}"

# Conexão com o Redis (padrão local)
redis_client = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True  # Retorna strings ao invés de bytes
)

# Tempo de cache: 60 segundos
CACHE_EXPIRATION_SECONDS = 60

# Gera uma recomendação com base na temperatura
def gerar_recomendacao(temp):
    if temp > 30:
        return "o dia está muito quente, passe protetor"
    elif 15 < temp <= 30:
        return "o clima está bom, pode aproveitar"
    else:
        return "frio demais, use um casaco"

# Endpoint principal: gera recomendação para uma cidade
@app.route('/recommendation/<city>', methods=['GET'])
def get_recommendation(city):
    # Normaliza o nome da cidade para usar como chave no Redis
    city_key = city.replace(" ", "").replace("_", "").lower()

    # Tenta pegar do cache Redis
    cached_data = redis_client.get(city_key)

    if cached_data:
        # Se encontrar, converte de JSON para dicionário
        weather = json.loads(cached_data)
        recomendacao = gerar_recomendacao(weather["temp"])
        return jsonify({
            **weather,
            "recommendation": recomendacao,
            "cached": True
        }), 200

    try:
        # Se não estiver no cache, consulta a API B
        response = requests.get(API_B_URL.format(city))

        if response.status_code == 200:
            weather = response.json()

            # Armazena o resultado no Redis com expiração
            redis_client.setex(city_key, CACHE_EXPIRATION_SECONDS, json.dumps(weather))

            recomendacao = gerar_recomendacao(weather["temp"])
            return jsonify({
                **weather,
                "recommendation": recomendacao,
                "cached": False
            }), 200
        else:
            return jsonify({"error": "Cidade não encontrada na API B"}), 404

    except Exception as e:
        return jsonify({"error": "Erro ao consultar a API B", "details": str(e)}), 500

# Inicia a API na porta 5000
if __name__ == '__main__':
    app.run(port=5000)
