# Chatbot

Projeto em estágio inicial para desenvolvimento de um chatbot em Python, com Flask nas dependências e infraestrutura local para Evolution API, PostgreSQL e Redis via Docker Compose.

## Estado atual

O projeto contém a configuração inicial das dependências e dos serviços. O arquivo `main.py` ainda é o exemplo padrão do PyCharm: ao executá-lo, imprime `Hi, PyCharm`. As rotas Flask, o recebimento de mensagens e a integração com a Evolution API ainda não foram implementados.

## Tecnologias

- Python
- Flask
- Requests
- python-dotenv
- Evolution API `v2.1.1`
- PostgreSQL
- Redis
- Docker Compose

## Estrutura

```text
.
├── docker-compose.yml   # Evolution API, PostgreSQL e Redis
├── main.py              # Ponto de entrada Python; atualmente um exemplo
├── requirements.txt     # Dependências Python
├── .gitignore           # Ignora o arquivo .env
└── README.md
```

## Executar localmente

É necessário ter Python com `pip` e Docker com Docker Compose disponíveis.

### 1. Preparar o ambiente Python

Na pasta do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

No Linux ou macOS, ative o ambiente com:

```bash
source .venv/bin/activate
```

### 2. Revisar a configuração dos serviços

Antes de iniciar a infraestrutura, revise `docker-compose.yml`:

- Ajuste a chave `AUTHENTICATION_API_KEY` e as credenciais do PostgreSQL conforme o ambiente.
- A variável `CACHE_REDIS_URI` aponta para `evo_redis`, mas o serviço Redis se chama `redis`. Altere o valor para `redis://redis:6379/1` para utilizar o nome do serviço na rede do Compose.

O arquivo `.env` está ignorado pelo Git, mas o código Python atual não o carrega e o Compose contém os valores de configuração diretamente no YAML.

### 3. Iniciar a infraestrutura

```bash
docker compose up -d
docker compose ps
```

Portas configuradas no host:

| Serviço | Endereço |
| --- | --- |
| Evolution API | `http://localhost:8080` |
| PostgreSQL | `localhost:5432` |
| Redis | `localhost:6379` |

Os dados dos serviços ficam armazenados em volumes Docker. O Compose ainda não configura verificações de saúde nem dependências de inicialização; consulte os logs para verificar se os serviços ficaram disponíveis:

```bash
docker compose logs -f
```

### 4. Executar o código Python

```bash
python main.py
```

Saída atual:

```text
Hi, PyCharm
```

Esse comando ainda não inicia um servidor Flask ou um chatbot.

## Parar a infraestrutura

```bash
docker compose down
```

Esse comando preserva os volumes de dados.

## Próximos passos

- Criar a aplicação Flask e uma rota de verificação de funcionamento.
- Implementar um webhook para receber mensagens.
- Integrar o envio de respostas com a Evolution API.
- Carregar configurações por variáveis de ambiente.
- Adicionar testes para o processamento de mensagens.
