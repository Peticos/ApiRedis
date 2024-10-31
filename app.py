from flask import Flask, jsonify, request
import redis, json
from datetime import datetime

app = Flask(__name__)

redis_url = 'rediss://default:AVNS_QnEs5Fi6ZSzEKrXrgLJ@peticos-cache-bhavatechteam-a076.h.aivencloud.com:17964'
r = redis.Redis.from_url(url=redis_url, ssl_cert_reqs=None)

@app.route('/dayhint', methods=['POST'])
def set_dayhint():
    expiration_time = 24 * 60 * 60

    dicas = request.get_json()

    for item in dicas:
        r.lpush("dicasDoDia", json.dumps(item))

    r.expire("dicasDoDia", 7)

    print([json.loads(dica) for dica in r.lrange("dicasDoDia", 0, -1)])  # Exibe os itens desserializados
    return jsonify({"sim": "sim"}), 200



@app.route('/dayhint', methods=['GET'])
def get_dayhint():
    dicas = r.lrange("dicasDoDia", 0, -1)  # Recupera todos os itens da lista
    dicas_decoded = [json.loads(dica) for dica in dicas]  # Desserializa cada item

    return jsonify(dicas_decoded), 200


@app.route('/dayhint/check', methods=['GET'])
def check_dayhint_exists():
    # Verifica se a chave "dicasDoDia" existe no Redis
    exists = r.exists("dicasDoDia")

    # Retorna uma resposta indicando se a chave existe
    if exists:
        return jsonify({"message": "A chave 'dicasDoDia' existe."}), 200
    else:
        return jsonify({"message": "A chave 'dicasDoDia' não existe."}), 404

    

if __name__ == '__main__':
    app.run(debug=True)
