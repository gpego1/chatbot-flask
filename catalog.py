import csv
import json
import re
import unicodedata
from pathlib import Path

from langchain_core.tools import tool


CATALOG_PATH = Path(__file__).resolve().with_name("catalogo.csv")


def normalize(text):
    return "".join(
        char for char in unicodedata.normalize("NFKD", text.casefold())
        if not unicodedata.combining(char)
    )


@tool
def consultar_catalogo(busca: str) -> str:
    """Consulte produtos, precos, cores, materiais, tamanhos e estoque da loja.

    Use um codigo de produto, nome, categoria ou caracteristicas, por exemplo
    'RP001', 'camiseta branca' ou 'vestido'. Use busca vazia para listar o catalogo.
    Retorna ate 10 registros e o total de correspondencias; refine a busca se
    houver mais resultados. Estoque por tamanho e a disponibilidade sao os do CSV.
    """
    with CATALOG_PATH.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter=";"))

    terms = re.findall(r"\w+", normalize(busca))
    stopwords = {"de", "da", "do", "das", "dos", "em", "e", "a", "o", "um", "uma"}
    terms = [term for term in terms if term not in stopwords]
    matches = []
    for row in rows:
        product_id = normalize(row.get("id_produto", ""))
        searchable = normalize(" ".join(row.get(field, "") for field in (
            "produto", "categoria", "publico", "cor", "material", "descricao"
        )))
        # O codigo deve coincidir exatamente; um codigo inexistente nao pode
        # retornar outro produto por causa de palavras genericas na consulta.
        ids = [term for term in terms if re.fullmatch(r"rp\d+", term)]
        if ids and product_id not in ids:
            continue
        score = sum(term in searchable or term == product_id for term in terms)
        if terms and not score:
            continue
        matches.append((score, row))

    matches.sort(key=lambda item: item[0], reverse=True)
    return json.dumps({
        "total_encontrado": len(matches),
        "resultados_limitados": len(matches) > 10,
        "produtos": [row for _, row in matches[:10]],
    }, ensure_ascii=False)
