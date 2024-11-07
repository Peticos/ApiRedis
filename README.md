# API Peticos - Flask com Redis

## Índice
- [Descrição](#descrição)
- [Tecnologias](#tecnologias)
- [Uso da API](#uso-da-api)
  - [URLs](#urls)
  - [Instalação](#instalação)
  - [Documentação](#documentação)
- [Equipe](#equipe)

## Descrição
Esta API foi desenvolvida utilizando Flask e Redis e faz parte do sistema do aplicativo Peticos. Ela é responsável por gerenciar as funcionalidades de **dicas do dia** e **posts personalizáveis**, garantindo que cada usuário receba conteúdos adaptados às suas preferências.

As funcionalidades principais incluem:
- **Dicas do Dia**: A API fornece 3 dicas diferentes diariamente, que foram adicionada no redis pela possibilidade de expirar as chaves
- **Feed Personalizável**: Cada usuário pode ter um feed personalizado, criado atraves de uma IA de recomendação. tudo para criar uma experiência única para cada usuário.

## Tecnologias
- **Python 3.10**
- **Flask**: Framework web para criar a API.
- **Redis**: Usado para cache e armazenamento temporário, acelerando o acesso a dados como dicas e posts.

## Uso da API

### URLs
- **Ambiente de Desenvolvimento**: ```https://apicachedev.onrender.com```
- **Ambiente de Produção**: ```https://apiredis-n0ke.onrender.com```

### Instalação

#### Pré-requisitos
- **Python 3.10**
- **Redis** instalado e em execução[
- Para garantir que a lógica de recomendação de posts está atualizada, mantenha o arquivo `recommendation.py` sincronizado com a versão mais recente no repositório [Peticos/Post_Recommending_ML](https://github.com/Peticos/Post_Recommending_ML/blob/main/recommendation.py).


#### Passos para rodar a API localmente:
1. Clone o repositório:
   ```bash
   git clone https://github.com/Peticos/ApiFlask.git
   cd ApiFlask
   ```

2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Execute a API:
   ```bash
   flask run
   ```

### Documentação
A documentação da API, com todos os endpoints e detalhes de uso, está disponível via Swagger (se configurado) ou como uma coleção no Postman.

- **Desenvolvimento**: [Swagger Dev]() 
- **Produção**: [Swagger Prod](https://apiredis-n0ke.onrender.com/apidocs/#/) 

## Equipe
- **Bianca Machado** - Desenvolvedor(a)
- **Guilherme Lanzoni** - Desenvolvedor da IA 
