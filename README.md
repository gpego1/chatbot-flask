<a id="english"></a>

# WhatsApp Chatbot

[English](#english) | [Português](#portugues)

A virtual assistant for a clothing store built with Flask, LangChain and Groq. It receives messages through the Evolution API, retrieves store policies using RAG, and can look up products in a catalog before replying on WhatsApp.

## How it works

1. Evolution forwards messages to `POST /webhook`.
2. The webhook ignores outgoing messages, groups, blocked contacts and messages without text.
3. Vector search retrieves up to four records from `Q&A.csv` to build the context.
4. The LLM can call `consultar_catalogo` to look up prices, sizes, colors, materials and stock.
5. The generated text is sent to the sender and returned in the HTTP response.

Each request is independent: conversation history is not retained between messages. The bot reads stock from the CSV; it does not reserve products or update quantities.

## Technologies and structure

- Python, Flask, Requests and python-dotenv.
- LangChain and ChatGroq with tool calling.
- Hugging Face embeddings: `sentence-transformers/all-MiniLM-L6-v2`.
- Chroma for the persistent vector index.
- Docker Compose: Evolution API `v2.3.7`, PostgreSQL 17 and Redis 7.4.

| File | Purpose |
| --- | --- |
| `chabot.py` | Flask application, RAG, chain and filters |
| `catalog.py` | Catalog lookup tool |
| `catalogo.csv` | Products, prices, sizes and stock |
| `Q&A.csv` | Store questions and answers |
| `utils/evolutionAPI.py` | Message delivery client |
| `docker-compose.yml` | Evolution API, PostgreSQL and Redis |
| `requirements.txt` | Python dependencies |
| `.env.example` | Partial configuration example |
| `main.py` | PyCharm sample; does not start the bot |
| `chroma_db/` | Locally generated index |

## Run locally

### 1. Set up Python

Install Python with `pip` and Docker with Docker Compose. From the project directory, in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2. Configure `.env`

For a new installation, copy `.env.example` to `.env`. If the file already exists, preserve its values and add only the missing variables:

```dotenv
# Groq key: the current code uses this variable name.
OPENAI_API_KEY=YOUR_GROQ_KEY
# Groq model with tool calling support.
MODEL=MODEL_IDENTIFIER

AUTHENTICATION_API_KEY=YOUR_EVOLUTION_KEY
POSTGRES_DB=evolution
POSTGRES_USER=evolution
POSTGRES_PASSWORD=DATABASE_PASSWORD

# Optional: country code and area code included, comma-separated.
BOT_BLOCKED_CONTACTS=5511999999999,5521988888888
```

Despite its name, `OPENAI_API_KEY` authenticates `ChatGroq`. An `OpenAI` client is also initialized, but it does not generate responses. `OPENAI_BASE_URL` is optional and affects only that client.

The instance, delivery API key and recipient come from the request. The `EVOLUTION_INSTANCE_NAME`, `EVOLUTION_API_KEY` and `EVOLUTION_RECIPIENT_NUMBER` variables in the older example are not used by the current webhook.

Leave `BOT_BLOCKED_CONTACTS` empty to allow all individual contacts. Full identifiers such as `123456789@lid` are also supported. If Evolution sends only a LID, block that full identifier; phone numbers can also be recognized when provided through `remoteJidAlt`. Restart Flask after changing `.env`.

### 3. Start the infrastructure

```powershell
docker compose up -d
docker compose ps
```

| Service | Address |
| --- | --- |
| Evolution API | `http://localhost:8080` |
| PostgreSQL on the host | `localhost:5441` |
| PostgreSQL on the Docker network | `postgres:5432` |
| Redis on the Docker network | `redis:6379` |

Services use persistent volumes. Evolution waits for PostgreSQL and Redis health checks. Changing the password in `.env` does not change the password of an already initialized database.

### 4. Start the bot

```powershell
.\.venv\Scripts\python.exe chabot.py
```

Flask listens on `0.0.0.0:5000`. The first startup may take time to download the embedding model and build the index. Keep the process running.

### 5. Configure the webhook

Connect the instance to WhatsApp and configure its webhook in the Evolution dashboard:

| Field | Value for Docker Desktop on Windows with Flask on the host |
| --- | --- |
| Enabled | On |
| URL | `http://host.docker.internal:5000/webhook` |
| Webhook by Events | Off |
| Webhook Base64 | Off |
| Event | `MESSAGES_UPSERT` |

The URL must be reachable from the container. In this setup, `localhost` inside the container refers to the container itself. Adapt the address if services run on other machines or containers.

Send a message from another phone number to the connected WhatsApp account. Outgoing and group messages are ignored with HTTP 200.

## Test a request

In Postman or Insomnia, send `POST http://127.0.0.1:5000/webhook` with `Content-Type: application/json` and this JSON body:

```json
{
  "event": "messages.upsert",
  "instance": "ACTUAL_INSTANCE_NAME",
  "apikey": "ACTUAL_EVOLUTION_KEY",
  "data": {
    "key": {
      "remoteJid": "5511999999999@s.whatsapp.net",
      "fromMe": false
    },
    "message": {
      "conversation": "Qual o preço e os tamanhos disponíveis do produto RP001?"
    }
  }
}
```

Replace the placeholders with real values. This test generates a response and sends a real message to the specified number. The example asks about product RP001; the assistant is configured to reply in Brazilian Portuguese.

The webhook also accepts `instance` inside `data`, `apiKey` instead of `apikey`, `remoteId` instead of `remoteJid`, and text in `data.message.extendedTextMessage.text`.

| Response | Meaning |
| --- | --- |
| `200` with a JSON string | Response generated and send request accepted by Evolution; does not confirm delivery or reading |
| `200` with `status: ignored` | Event ignored without generating or sending a response |
| `400` | Invalid JSON or required fields |
| `500` | Unhandled exception during generation, lookup or sending; check the Flask terminal |

## Update the data sources

### Store policies: `Q&A.csv`

A UTF-8, comma-separated CSV with two columns and **no header**: question and answer. Values containing commas or line breaks must be quoted.

```csv
Do you offer installments?,"Enter the store's actual payment terms here."
```

Each record becomes a Chroma document. Restart Flask after editing the file: its contents determine the collection used. Stable IDs prevent duplicates when restarting with the same version. Previous collections remain in storage.

### Products: `catalogo.csv`

A UTF-8, semicolon-separated CSV with this header. Keep the field names unchanged:

```text
id_produto;produto;categoria;publico;cor;material;preco_brl;tamanhos_disponiveis;estoque_por_tamanho;estoque_total;descricao
```

The tool reads the file on every lookup, so updates do not require reindexing or restarting. It searches codes or terms from product names, categories and attributes, ignoring case and accents. It returns up to ten products and the total match count. A supplied `RP...` code must match exactly.

The LLM can refine searches for up to three rounds of tool calls, then generates a response without additional tools. Catalog lookup depends on the LLM's decision and the model's tool calling support.

## Troubleshooting and shutdown

Follow Evolution logs with:

```powershell
docker compose logs -f evolution-api
```

For webhook errors, read the traceback in the `chabot.py` terminal. If sending returns 404, check the instance and URL. For authentication failures, check the submitted API key. If Flask receives no requests, check the instance connection, configured event and webhook URL connectivity.

Stop Flask with `Ctrl+C`. To stop the infrastructure while preserving volumes:

```powershell
docker compose down
```

---

<a id="portugues"></a>

[English](#english) | [Português](#portugues)

# Chatbot para WhatsApp

Atendente virtual de uma loja de roupas com Flask, LangChain e Groq. Recebe mensagens pela Evolution API, consulta as políticas da loja por RAG e pode buscar produtos no catálogo antes de responder pelo WhatsApp.

## Funcionamento

1. A Evolution encaminha mensagens para `POST /webhook`.
2. O webhook ignora mensagens próprias, grupos, contatos bloqueados e mensagens sem texto.
3. A busca vetorial recupera até quatro registros de `Q&A.csv` para compor o contexto.
4. A LLM pode chamar `consultar_catalogo` para consultar preços, tamanhos, cores, materiais e estoque.
5. O texto gerado é enviado ao remetente e retornado na resposta HTTP.

Cada requisição é independente: não há histórico de conversa entre mensagens. O bot consulta o estoque do CSV; não reserva produtos nem atualiza quantidades.

## Tecnologias e estrutura

- Python, Flask, Requests e python-dotenv.
- LangChain e ChatGroq com chamadas de ferramentas.
- Embeddings Hugging Face: `sentence-transformers/all-MiniLM-L6-v2`.
- Chroma para o índice vetorial persistente.
- Docker Compose: Evolution API `v2.3.7`, PostgreSQL 17 e Redis 7.4.

| Arquivo | Função |
| --- | --- |
| `chabot.py` | Aplicação Flask, RAG, chain e filtros |
| `catalog.py` | Ferramenta de consulta ao catálogo |
| `catalogo.csv` | Produtos, preços, tamanhos e estoque |
| `Q&A.csv` | Perguntas e respostas sobre a loja |
| `utils/evolutionAPI.py` | Cliente de envio de mensagens |
| `docker-compose.yml` | Evolution API, PostgreSQL e Redis |
| `requirements.txt` | Dependências Python |
| `.env.example` | Exemplo parcial de configuração |
| `main.py` | Exemplo do PyCharm; não inicia o bot |
| `chroma_db/` | Índice gerado localmente |

## Executar localmente

### 1. Preparar o ambiente Python

Tenha Python com `pip` e Docker com Docker Compose disponíveis. Na pasta do projeto, no PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2. Configurar o `.env`

Em uma instalação nova, copie `.env.example` para `.env`. Se o arquivo já existir, preserve seus valores e acrescente apenas as variáveis ausentes:

```dotenv
# Chave da Groq: o código atual usa este nome de variável.
OPENAI_API_KEY=CHAVE_DA_GROQ
# Modelo Groq com suporte a chamadas de ferramentas.
MODEL=IDENTIFICADOR_DO_MODELO

AUTHENTICATION_API_KEY=CHAVE_DA_EVOLUTION
POSTGRES_DB=evolution
POSTGRES_USER=evolution
POSTGRES_PASSWORD=SENHA_DO_BANCO

# Opcional: números com país e DDD, separados por vírgula.
BOT_BLOCKED_CONTACTS=5511999999999,5521988888888
```

`OPENAI_API_KEY` autentica o `ChatGroq`, apesar do nome. O cliente `OpenAI` também é inicializado, mas não participa da geração das respostas. `OPENAI_BASE_URL` é opcional e afeta apenas esse cliente.

A instância, a chave de envio e o destinatário vêm da requisição. As variáveis `EVOLUTION_INSTANCE_NAME`, `EVOLUTION_API_KEY` e `EVOLUTION_RECIPIENT_NUMBER` presentes no exemplo antigo não são usadas pelo webhook atual.

Deixe `BOT_BLOCKED_CONTACTS` vazio para não bloquear contatos individuais. Também são aceitos identificadores completos, como `123456789@lid`. Se a Evolution enviar apenas um LID, bloqueie esse identificador completo; números também podem ser reconhecidos quando enviados em `remoteJidAlt`. Reinicie o Flask após alterar o `.env`.

### 3. Iniciar a infraestrutura

```powershell
docker compose up -d
docker compose ps
```

| Serviço | Endereço |
| --- | --- |
| Evolution API | `http://localhost:8080` |
| PostgreSQL no host | `localhost:5441` |
| PostgreSQL na rede Docker | `postgres:5432` |
| Redis na rede Docker | `redis:6379` |

Os serviços usam volumes persistentes. A Evolution aguarda os healthchecks do PostgreSQL e do Redis. Alterar a senha no `.env` não altera a senha de um banco já inicializado.

### 4. Iniciar o bot

```powershell
.\.venv\Scripts\python.exe chabot.py
```

O Flask escuta em `0.0.0.0:5000`. A primeira inicialização pode demorar para baixar o modelo de embeddings e criar o índice. Mantenha o processo em execução.

### 5. Configurar o webhook

Conecte a instância ao WhatsApp e configure seu webhook no painel da Evolution:

| Campo | Valor para Docker Desktop no Windows e Flask no host |
| --- | --- |
| Enabled | Ativado |
| URL | `http://host.docker.internal:5000/webhook` |
| Webhook by Events | Desativado |
| Webhook Base64 | Desativado |
| Evento | `MESSAGES_UPSERT` |

A URL precisa ser acessível pelo container. Nesse cenário, `localhost` dentro do container aponta para o próprio container. Adapte o endereço se os serviços estiverem em outras máquinas ou containers.

Envie uma mensagem de outro número ao WhatsApp conectado. Mensagens próprias e de grupos são ignoradas com retorno HTTP 200.

## Testar uma requisição

No Postman ou Insomnia, envie `POST http://127.0.0.1:5000/webhook`, com `Content-Type: application/json` e body JSON:

```json
{
  "event": "messages.upsert",
  "instance": "NOME_REAL_DA_INSTANCIA",
  "apikey": "CHAVE_REAL_DA_EVOLUTION",
  "data": {
    "key": {
      "remoteJid": "5511999999999@s.whatsapp.net",
      "fromMe": false
    },
    "message": {
      "conversation": "Qual o preço e os tamanhos disponíveis do produto RP001?"
    }
  }
}
```

Substitua os exemplos pelos dados reais. Esse teste gera uma resposta e envia uma mensagem real ao número informado.

Também são aceitos `instance` dentro de `data`, `apiKey` no lugar de `apikey`, `remoteId` no lugar de `remoteJid` e texto em `data.message.extendedTextMessage.text`.

| Retorno | Significado |
| --- | --- |
| `200` com texto JSON | Resposta gerada e envio aceito pela Evolution; não confirma entrega ou leitura |
| `200` com `status: ignored` | Evento ignorado, sem geração ou envio de resposta |
| `400` | JSON ou campos obrigatórios inválidos |
| `500` | Exceção não tratada na geração, consulta ou envio; consulte o terminal do Flask |

## Atualizar as fontes

### Políticas: `Q&A.csv`

CSV UTF-8 separado por vírgula, com duas colunas **sem cabeçalho**: pergunta e resposta. Valores com vírgulas ou quebras de linha devem ficar entre aspas.

```csv
Vocês parcelam a compra?,"Insira aqui as condições reais da loja."
```

Cada registro vira um documento no Chroma. Reinicie o Flask após editar o arquivo: o conteúdo determina a coleção utilizada. IDs estáveis evitam duplicatas nas reinicializações da mesma versão. Coleções anteriores permanecem no armazenamento.

### Produtos: `catalogo.csv`

CSV UTF-8 separado por ponto e vírgula, com o cabeçalho:

```text
id_produto;produto;categoria;publico;cor;material;preco_brl;tamanhos_disponiveis;estoque_por_tamanho;estoque_total;descricao
```

A ferramenta lê o arquivo a cada consulta: alterações não exigem reindexação ou reinicialização. Busca códigos ou termos do nome, categoria e características, sem diferenciar maiúsculas e acentos. Retorna até dez produtos e informa o total de correspondências. Um código `RP...` informado precisa coincidir exatamente.

A LLM pode refinar a busca durante até três rodadas de chamadas de ferramentas; depois, gera uma resposta sem novas ferramentas. A consulta depende da decisão da LLM e do suporte do modelo a tool calling.

## Diagnóstico e encerramento

Acompanhe a Evolution com:

```powershell
docker compose logs -f evolution-api
```

Para erros no webhook, leia o traceback no terminal de `chabot.py`. Se o envio retornar 404, confira a instância e a URL. Para falhas de autenticação, confira a chave enviada. Se o Flask não receber requisições, confira a conexão da instância, o evento configurado e a conectividade da URL do webhook.

Pare o Flask com `Ctrl+C`. Para parar a infraestrutura preservando os volumes:

```powershell
docker compose down
```
