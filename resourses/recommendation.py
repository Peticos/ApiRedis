# Importações
import pandas as pd
from pymongo import MongoClient
from sklearn.neighbors import NearestNeighbors
import sys
import redis
import json
from bson import ObjectId
from datetime import datetime



# Funções
## Função para criar o DataFrame com os dados do MongoDB
def get_df():
    # Leitura dos dados
    ## Conexão
    uri = 'mongodb+srv://admin:X955pJ8YkBMrVMG@peticos.ajboj.mongodb.net/'
    client = MongoClient(uri,serverSelectionTimeoutMS=30000 )
    db = client['Peticos']
    collection = db['post']
    
    ## Criação do DataFrame
    df = pd.DataFrame(collection.find())[['_id', 'likes', 'shares']]
    
    return df, collection

## Função para transformar o DataFrame em uma matriz de interação de usuários e posts
def matrix():
    df, collection = get_df()

    init_df = df
    
    # Criação do DataFrame de interações
    dict_df = {
        'user_id': [],
        'post_id': [],
        'interaction': []
    }

    for column in ['likes', 'shares']:
        for i in range(df[column].count()):
            if df[column].iloc[i] != None:
                for value in list(df[column].iloc[i]):
                    dict_df['user_id'].append(value)
                    dict_df['post_id'].append(str(df['_id'].iloc[i]))
                    dict_df['interaction'].append(column[:-1])
    
    df = pd.DataFrame(dict_df)

    # Mudando o DataFrame para quantidade de interações (quanto mais a pessoa interagiu, mais ela gostou)
    df = df.groupby(['user_id', 'post_id']).size().reset_index(name='interaction')
    df = df.loc[df['user_id'] != '']

    # Criação da matriz de interação por usuário e post
    df = df.pivot_table(index='user_id', columns='post_id', values='interaction', fill_value=0)
    
    for post in init_df.loc[(init_df['likes'].str.len() == 0) & (init_df['shares'].str.len() == 0), '_id']:
        df[str(post)] = 0
    
    return df, collection

## Função para calcular a propensão
def calculate_propensity(user_id, user_item_matrix, knn):
    if user_id in user_item_matrix.index:
        user_index = user_item_matrix.index.get_loc(user_id)
        
        # Pegando as distâncias e os vizinhos mais próximos
        indices = knn.kneighbors(user_item_matrix.iloc[user_index, :].values.reshape(1, -1), return_distance=False)
        
        # Cálculo da média de quantidade de interação dos vizinhos mais próximos
        neighbor_indices = indices.flatten()
        propensity_scores = user_item_matrix.iloc[neighbor_indices, :].mean(axis=0)
        
        # Convertendo os dados em um DataFrame para poder ordená-los
        propensity_df = {'post': user_item_matrix.columns, 'score': propensity_scores}
        propensity_df = pd.DataFrame(propensity_df).sort_values(by='score')
        
        # Removendo os posts que o usuário já interagiu
        interacted = [column for column in user_item_matrix.columns if user_item_matrix.iloc[user_index][column] > 0]
                
        propensity_df = propensity_df.loc[~propensity_df['post'].isin(interacted)]

        return propensity_df['post'].to_list()
    else:
        # Cálculo da média de quantidade de interação de todas as pessoas
        propensity_scores = user_item_matrix.mean(axis=0)
        
        # Convertendo os dados em um DataFrame para poder ordená-los
        propensity_df = {'post': user_item_matrix.columns, 'score': propensity_scores}
        propensity_df = pd.DataFrame(propensity_df).sort_values(by='score')
        
        return propensity_df['post'].to_list()

# Verificando se o parâmetro foi realmente passado corretamente
def execute_feed(user_id):
    # Matriz criada
    user_item_matrix, collection = matrix()

    # Treinamento do modelo
    knn = NearestNeighbors(n_neighbors=3, metric='cosine')
    knn.fit(user_item_matrix)

    # Calculando a propensão do usuário
    recommended_posts = calculate_propensity(user_id, user_item_matrix, knn)
    
    # Conexão com o Redis
    r = redis.from_url('rediss://default:AVNS_QnEs5Fi6ZSzEKrXrgLJ@peticos-cache-bhavatechteam-a076.h.aivencloud.com:17964', decode_responses=True)
    
    # Filtrando os posts já vistos
    seen_name = user_id + '.seen'
    
    seen = []
    
    if r.exists(seen_name):
        seen = r.lrange(seen_name, 0, -1)
    
    # Enviando os dados para o redis
    
    # transforma o _id dos posts em string
    recommended_posts = [post for post in recommended_posts if post not in seen]

    # Filtra os 10 primeiros caso existam 10 sobrando, caso não, retorna todos os valores
    recommended_posts = recommended_posts[:min(10, len(recommended_posts))]
    
    recommended_posts = list(collection.find({'_id': {'$in': [ObjectId(id) for id in recommended_posts]}}))
    
    formated_posts = []
    for post in recommended_posts:
        # Verifica e converte '_id' para string
        post['_id'] = str(post['_id'])

        # Formata a data se o campo 'post_date' existir e for do tipo datetime
        if 'post_date' in post and isinstance(post['post_date'], datetime):
            post['post_date'] = post['post_date'].strftime('%Y-%m-%d %H:%M:%S')
        formated_posts.append(json.dumps(post))

    # Serializar para JSON após garantir que todos os posts têm _id como string
    recommended_posts = formated_posts
    
    # Remove a lista antiga e adiciona a nova no Redis
    r.delete(user_id)
    for post in recommended_posts:
        r.lpush(user_id, post)
        id = str(json.loads(post)["_id"])
        r.lpush(seen_name, id)