from flask import Flask, jsonify, request
import redis, json
from datetime import datetime
import os
from flasgger import Swagger
from resourses.recommendation import execute_feed
from pymongo import MongoClient
from bson import ObjectId


app = Flask(__name__)
swagger = Swagger(app)  


redis_url = 'rediss://default:AVNS_QnEs5Fi6ZSzEKrXrgLJ@peticos-cache-bhavatechteam-a076.h.aivencloud.com:17964'
r = redis.from_url(url=redis_url, decode_responses = True)

## Conexão
uri = 'mongodb+srv://admin:X955pJ8YkBMrVMG@peticos.ajboj.mongodb.net/'
client = MongoClient(uri)
db = client['Peticos']
collection = db['post']

# Keep Alive:

@app.route("/", methods=['GET'])
def keep_alive():
    '''
    
    ## Endpoint para o keep alive 

    ---
    tags:
      - Keep Alive
    responses:
      200:
        description: A aplicação está ativa
        schema:
          type: string
          example: ApiRedis está ativa
      404:
        description: A aplicacação não está ativa
        
    '''
    return "ApiRedis está ativa"

# Dicas do dia:

@app.route('/dayhint/insert', methods=['POST'])
def set_dayhint():
    '''
    
    ## Adiciona dicas do dia

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
        description: A chave 'dicasDoDia' existe.
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Salvo com sucesso"
    '''
    expiration_time = 24 * 60 * 60

    dicas = request.get_json()

    for item in dicas:
        r.lpush("dicasDoDia", json.dumps(item))

    r.expire("dicasDoDia", expiration_time)

    print([json.loads(dica) for dica in r.lrange("dicasDoDia", 0, -1)])  # Exibe os itens desserializados
    return jsonify({"message": "Salvo com sucesso"}), 200

@app.route('/dayhint', methods=['GET'])
def get_dayhint():
    '''
    
    ## Resgatar dicas do dia

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
    '''
    dicas = r.lrange("dicasDoDia", 0, -1)  # Recupera todos os itens da lista
    dicas_decoded = [json.loads(dica) for dica in dicas]  # Desserializa cada item

    return jsonify(dicas_decoded), 200

@app.route('/dayhint/check', methods=['GET'])
def check_dayhint_exists():
    '''
    
    ## Verifica se a chave 'dicasDoDia' existe no Redis

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
    '''
    # Verifica se a chave "dicasDoDia" existe no Redis
    exists = r.exists("dicasDoDia")

    # Retorna uma resposta indicando se a chave existe
    if exists:
        return jsonify({"message": "A chave 'dicasDoDia' existe."}), 200
    else:
        return jsonify({"message": "A chave 'dicasDoDia' não existe."}), 404
    
@app.route('/dayhint', methods=['DELETE'])
def delete_dayhint():
    '''
    
    ## Apaga todas as dicas do dia

    ---
    tags:
      - Dicas do Dia
    responses:
      200:
        description: Sucesso ao apagar as dicas
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Todas as dicas foram apagadas com sucesso."
      404:
        description: Nenhuma dica encontrada para apagar
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Nenhuma dica para apagar."
    '''
    # Verifica se a chave "dicasDoDia" existe
    if r.exists("dicasDoDia"):
        r.delete("dicasDoDia")
        return jsonify({"message": "Todas as dicas foram apagadas com sucesso."}), 200
    else:
        return jsonify({"message": "Nenhuma dica para apagar."}), 404

# Feed
@app.route('/feed/newfeed/<user_id>', methods=['GET'])
def set_new_user_feed(user_id):
  '''
    
    ## Adiciona novos posts ao feed do usuário especificado.

    ---
    tags:
      - Feed
    parameters:
      - name: user_id
        in: path
        required: true
        description: username do usuário cujo feed será atualizado.
        schema:
          type: string
    '''
  
  execute_feed(user_id=user_id)

  feed_items = r.lrange(user_id, 0, -1)
  feed_decoded = [json.loads(item) for item in feed_items]

  if feed_decoded==[]:
    delete_seen(user_id=user_id)
    return set_new_user_feed(user_id=user_id)


  return jsonify(feed_decoded), 200

@app.route('/feed/<user_id>', methods=['GET'])
def get_user_feed(user_id):
  '''
    
    ## Retorna o feed do usuário especificado.

    ---
    tags:
      - Feed
    parameters:
      - name: user_id
        in: path
        required: true
        description: username do usuário cujo feed será buscado.
        schema:
          type: string
  '''
  
  user_feed_key = f"{user_id}"

  if not r.exists(user_feed_key):
    execute_feed(user_id=user_id)
  
  feed_items = r.lrange(user_feed_key, 0, -1)
  feed_decoded = [json.loads(item) for item in feed_items]

  return jsonify(feed_decoded), 200

@app.route('/like/<post_id>/<username>', methods=['POST'])
def like_post(post_id, username):
  '''
    
    ## Da like no post no feed do usuário especificado.

    ---
    tags:
      - Feed
    parameters:
      - name: username
        in: path
        required: true
        description: username do usuário cujo feed será buscado.
        schema:
          type: string
      - name: post_id
        in: path
        required: true
        description: id do post que vai ser curtido
        schema:
          type: string
  '''
  feed_key = f"{username}"

  feed_items = r.lrange(feed_key, 0, -1)
  feed_decoded = [json.loads(item) for item in feed_items]    

  post_found = False
  for post in feed_decoded:
    if post['_id'] == post_id:
        post_found = True
        if username not in post['likes']:
            post['likes'].append(username)
            break

  if not post_found:
    return jsonify({"message": "Post não encontrado."}), 404
  
  delete_feed(user_id=username)
  
  for item in feed_decoded[::-1]:
    r.lpush(feed_key, json.dumps(item))


  collection.update_one({"_id":ObjectId(post_id)}, {'$addToSet': {'likes': username}})


  return jsonify({"message": "Like adicionado com sucesso."}), 200

@app.route('/dislike/<post_id>/<username>', methods=['POST'])
def dislike_post(post_id, username):
  '''
    
    ## Tira like no post no feed do usuário especificado.

    ---
    tags:
      - Feed
    parameters:
      - name: username
        in: path
        required: true
        description: username do usuário cujo feed será buscado.
        schema:
          type: string
      - name: post_id
        in: path
        required: true
        description: id do post que vai ser curtido
        schema:
          type: string
  '''
  feed_key = f"{username}"

  feed_items = r.lrange(feed_key, 0, -1)
  feed_decoded = [json.loads(item) for item in feed_items]    

  post_found = False
  for post in feed_decoded:
      if post['_id'] == post_id:
          post_found = True
          if username in post['likes']:
              post['likes'].remove(username)
              break

  if not post_found:
      return jsonify({"message": "Post não encontrado."}), 404
  
  delete_feed(user_id=username)
  
  for item in feed_decoded[::-1]:
    r.lpush(feed_key, json.dumps(item))


  collection.update_one({"_id": ObjectId(post_id)}, {'$pull': {'likes': username}})

  return jsonify({"message": "Like remmovido com sucesso."}), 200

@app.route('/delete_feed/<user_id>', methods=['DELETE'])
def delete_feed(user_id):
    user_feed_key = f"{user_id}"

    # Verifica se a chave existe
    if r.exists(user_feed_key):
        r.delete(user_feed_key)
        return jsonify({"message": "Feed deletado com sucesso."}), 200
    else:
        return jsonify({"message": "Feed não encontrado."}), 404


@app.route('/deleteseen/<user_id>', methods=['DELETE'])
def delete_seen(user_id):
    user_feed_key = f"{user_id}.seen"

    # Verifica se a chave existe
    if r.exists(user_feed_key):
        r.delete(user_feed_key)
        return jsonify({"message": "Feed deletado com sucesso."}), 200
    else:
        return jsonify({"message": "Feed não encontrado."}), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)