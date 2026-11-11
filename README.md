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

O Compose usa as variáveis do `.env`, ignorado pelo Git. Para uma nova instalação, copie `.env.example` para `.env` e preencha `AUTHENTICATION_API_KEY` e `POSTGRES_PASSWORD`. Se já tiver um `.env`, preserve seu conteúdo e adicione apenas as variáveis ausentes. Os campos obrigatórios vazios impedem a inicialização. Use senha hexadecimal para evitar caracteres reservados na URI.

As imagens usam PostgreSQL 17 e Redis 7.4. Se já existir um volume PostgreSQL de outra versão principal, utilize uma imagem compat?vel com ele ou faça uma migração antes de iniciar. Não exclua volumes com dados necess?rios. Alterar a senha no `.env` não altera a senha de um banco já inicializado.

O código Python atual ainda não carrega o `.env`.

### 3. Iniciar a infraestrutura

```bash
docker compose up -d
docker compose ps
```

Endereços dos serviços (a API fica acessível apenas pela interface local):

| Serviço | Endereço |
| --- | --- |
| Evolution API | `http://localhost:8080` |
| PostgreSQL | `postgres:5432` (rede Docker) |
| Redis | `redis:6379` (rede Docker) |

Os dados ficam em volumes Docker. A API aguarda os healthchecks do PostgreSQL e do Redis antes de iniciar. O Redis usa persistência AOF. Para acompanhar a inicialização:

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
