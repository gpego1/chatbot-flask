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

load_dotenv()
app = flask.Flask(__name__)

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
    data = flask.request.json
    message = chain.invoke(data["message"])
    return flask.jsonify(message.content)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)


