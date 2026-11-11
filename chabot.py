from openai import OpenAI
from dotenv import load_dotenv
import flask
import csv
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
import os
from utils.evolutionAPI import EvolutionAPI

load_dotenv()
app = flask.Flask(__name__)

e = EvolutionAPI()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
)

documents = []

with open("Q&A.csv", "r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)

    for index, row in enumerate(reader):
        content = "\n".join(
            f"{key}: {value}"
            for key, value in row.items()
        )

    document = Document(
        page_content=content,
        metadata={
            "source": "Q&A.csv",
            "row":index
        }
    )
    documents.append(document)

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

vector_store = Chroma.from_documents(
    documents=documents,
    embedding=embeddings,
    persist_directory="./chroma_db"
)

retriever = vector_store.as_retriever()

llm = ChatGroq(
    model=os.getenv("MODEL"),
    api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0.7
)

template = "você é um atendente virtual de uma loja de roupas que precisa responder as perguntas de um cliente. Conext: {context}, pergunta: {pergunta}"
prompt = ChatPromptTemplate.from_template(template)

chain = (
    {
        "context": retriever,
        "pergunta": RunnablePassthrough()
    }
    | prompt
    | llm

)
@app.route("/webhook", methods=["POST"])
def webhook():
    payload = flask.request.get_json(silent=True)
    if not isinstance(payload, dict):
        return flask.jsonify(error="Envie um objeto JSON v?lido."), 400

    event = payload.get("event")
    if event and event not in ("messages.upsert", "MESSAGES_UPSERT"):
        return flask.jsonify(status="ignored"), 200

    data = payload.get("data")
    if not isinstance(data, dict):
        return flask.jsonify(error="O campo data deve ser um objeto."), 400
    key = data.get("key")
    incoming = data.get("message")
    if not isinstance(key, dict) or not isinstance(incoming, dict):
        return flask.jsonify(error="Os campos data.key e data.message s?o obrigat?rios."), 400
    if key.get("fromMe") is True:
        return flask.jsonify(status="ignored"), 200

    instance = payload.get("instance") or data.get("instance")
    api_secret = payload.get("apikey") or payload.get("apiKey")
    remote_id = key.get("remoteJid") or key.get("remoteId")
    extended = incoming.get("extendedTextMessage")
    question = incoming.get("conversation") or (
        extended.get("text") if isinstance(extended, dict) else None
    )
    if question is None:
        return flask.jsonify(status="ignored", reason="Mensagem sem texto."), 200
    fields = {"instance": instance, "apikey": api_secret,
              "data.key.remoteJid": remote_id, "texto": question}
    invalid = [name for name, value in fields.items()
               if not isinstance(value, str) or not value.strip()]
    if invalid:
        return flask.jsonify(error="Campos ausentes ou inv?lidos: " + ", ".join(invalid)), 400

    message = chain.invoke(question)
    e.send_message(instance, api_secret, remote_id.split("@")[0], message.content)
    return flask.jsonify(message.content)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)


