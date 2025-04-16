from flask import Flask, jsonify
import requests
import time

app = Flask(__name__)

# url da API B que vai fornecer os dados de clima
API_B_URL = "http://localhost:5001/weather/{}"
# segundos para o cache expirar
CACHE_EXPIRATION_SECONDS = 60

# estrutura de cache
weather_cache = {}

# função que vai dar a recomendação de acordo com a temperatura
def gerar_recomendacao(temp):
    if temp > 30:
        return "Está muito quente! Lembre-se de se hidratar e usar protetor solar."
    elif 15 < temp <= 30:
        return "O clima está agradável. Aproveite o seu dia!"
    else:
        return "Está frio! Não esqueça de usar um casaco."

# rota da API A que gera a recomendação de acordo com a cidade
@app.route('/recommendation/<city>', methods=['GET'])
def get_recommendation(city):

    # captura o tempo atual
    current_time = time.time()
    # normaliza o nome da cidade
    city_key = city.replace(" ", "").replace("_", "")

    # verifica se a cidade ta no cache e se ainda é valido 
    if city_key in weather_cache:
        cached = weather_cache[city_key]
        if current_time - cached["timestamp"] < CACHE_EXPIRATION_SECONDS:
            # usa o dado do cache
            weather = cached["data"]
            recomendacao = gerar_recomendacao(weather["temp"])
            return jsonify({
                **weather,
                "recommendation": recomendacao,
                "cached": True
            })

    try:
        # chama a API B para obter o clima
        response = requests.get(API_B_URL.format(city))
        # verifica se a resposta da API B teve sucesso
        if response.status_code == 200:
            weather = response.json()

            # atualiza o cache
            weather_cache[city_key] = {
                "data": weather,
                "timestamp": current_time
            }

            # gera a recomendação de acordo com a temparatura 
            recomendacao = gerar_recomendacao(weather["temp"])
            return jsonify({
                **weather,
                "recommendation": recomendacao,
                "cached": False
            }), 200
        else:
            # erro caso a cidade não seja encontrada
            return jsonify({"error": "Cidade não encontrada na API B"}), 404

    except Exception as e:
        # aponta erros genéricos
        return jsonify({"error": "Erro ao consultar a API B", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000)
