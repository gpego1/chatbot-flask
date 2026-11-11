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
