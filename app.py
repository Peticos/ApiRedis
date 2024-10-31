from flask import Flask, jsonify, request
import redis, json
from datetime import datetime
import os
from flasgger import Swagger


app = Flask(__name__)
swagger = Swagger(app)  # Adicione isso para inicializar o Swagger


redis_url = 'rediss://default:AVNS_QnEs5Fi6ZSzEKrXrgLJ@peticos-cache-bhavatechteam-a076.h.aivencloud.com:17964'
r = redis.Redis.from_url(url=redis_url, ssl_cert_reqs=None)

@app.route('/dayhint/insert', methods=['POST'])
def set_dayhint():
    """Adiciona dicas do dia
    ---
    tags:
      - Dicas do Dia
    parameters:
      - in: body
        name: dicas
        required: true
        schema:
          type: array
          items:
            type: object
            properties:
              hint_text:
                type: string
                example: "Ofereça rações específicas para filhotes e evite comida caseira."
              idHint:
                type: integer
                example: 8
              link:
                type: string
                example: "http://link8.com"
              title:
                type: string
                example: "Alimentação adequada para filhotes"
    responses:
      200:
        description: Sucesso
        schema:
          type: array
          items:
            type: object
            properties:
              hint_text:
                type: string
                example: "Ofereça rações específicas para filhotes e evite comida caseira."
              idHint:
                type: integer
                example: 8
              link:
                type: string
                example: "http://link8.com"
              title:
                type: string
                example: "Alimentação adequada para filhotes"
    """
    expiration_time = 24 * 60 * 60

    dicas = request.get_json()

    for item in dicas:
        r.lpush("dicasDoDia", json.dumps(item))

    r.expire("dicasDoDia", expiration_time)

    print([json.loads(dica) for dica in r.lrange("dicasDoDia", 0, -1)])  # Exibe os itens desserializados
    return jsonify({"sim": "sim"}), 200



@app.route('/dayhint', methods=['GET'])
def get_dayhint():
    """Resgatar dicas do dia
    ---
    tags:
      - Dicas do Dia
    responses:
      200:
        description: Sucesso
        schema:
          type: array
          items:
            type: object
            properties:
              hint_text:
                type: string
                example: "Ofereça rações específicas para filhotes e evite comida caseira."
              idHint:
                type: integer
                example: 8
              link:
                type: string
                example: "http://link8.com"
              title:
                type: string
                example: "Alimentação adequada para filhotes"
    """
    dicas = r.lrange("dicasDoDia", 0, -1)  # Recupera todos os itens da lista
    dicas_decoded = [json.loads(dica) for dica in dicas]  # Desserializa cada item

    return jsonify(dicas_decoded), 200


@app.route('/dayhint/check', methods=['GET'])
def check_dayhint_exists():
    """Verifica se a chave 'dicasDoDia' existe no Redis
    ---
    tags:
      - Dicas do Dia
    responses:
      200:
        description: A chave 'dicasDoDia' existe.
        schema:
          type: object
          properties:
            message:
              type: string
              example: "A chave 'dicasDoDia' existe."
      404:
        description: A chave 'dicasDoDia' não existe.
        schema:
          type: object
          properties:
            message:
              type: string
              example: "A chave 'dicasDoDia' não existe."
    """
    # Verifica se a chave "dicasDoDia" existe no Redis
    exists = r.exists("dicasDoDia")

    # Retorna uma resposta indicando se a chave existe
    if exists:
        return jsonify({"message": "A chave 'dicasDoDia' existe."}), 200
    else:
        return jsonify({"message": "A chave 'dicasDoDia' não existe."}), 404

    
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
