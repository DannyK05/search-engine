import math
from urllib.parse import urljoin, urlsplit


def url_parser(href: str, base: str):
    """
    (str, str) -> str | None

    Normalizes an href into an absolute URL when possible.

    Root-relative URLs are combined with the base URL.
    Absolute HTTP/HTTPS URLs are returned unchanged.
    Unsupported or unrecognized href values return None.
    """
    if len(href) == 0:
        return None
    
    if href[0] == "/":
        return urljoin(base, href)

    url_components = urlsplit(href)

    if url_components.scheme in ["http", "https"]:
        url_components = url_components._replace(fragment="")
        if "login" in url_components.path or "signup" in url_components.path or "register" in url_components.path:
            url_components = url_components._replace(query="")
        return url_components.geturl()
    else:
        return None




def tokenize(query: str):
    """
    (str) => list[str]

    Returns processed tokens from a string;

    """
    tokens = query.split(" ")
    processed_tokens = []
    for token in tokens:
        stripped_token = token.strip()
        if stripped_token == "":
            continue
        processed_tokens.append(stripped_token.lower())

    return processed_tokens


def rank(
    cur,
    tokens: list[str],
):
    doc_ranking = {}
    rank_details = []

    cur.execute(
        """
        SELECT COUNT(*)
        FROM documents
        """
    )
    total_docs = cur.fetchone()[0]

    for token in tokens:
        cur.execute(
            """
            SELECT *
            FROM document_tokens
            WHERE token_id = (
            SELECT token_id
            FROM tokens
            WHERE token = %s
            )
            """,
            (token,),
        )

        details = cur.fetchall()

        if len(details) != 0:
            for detail in details:
                score = (detail[3] / detail[2]) * (
                    math.log10(total_docs / len(details))
                )
                if detail[1] not in doc_ranking:
                    doc_ranking[detail[1]] = score
                else:
                    doc_ranking[detail[1]] += score

    for key, value in doc_ranking.items():
        token_detail = {"document_id": key, "score": value}
        rank_details.append(token_detail)

    rank_details.sort(key=lambda x: x["score"], reverse=True)

    return rank_details


def extract_ranked_documents(cur, ranked_docs: list[dict]):
    """
    (list[dict]) => list[dict]

    Extracts the document details from the ranked documents

    """
    doc_details = []
    for doc in ranked_docs:
        cur.execute(
            """
            SELECT *
            FROM documents
            WHERE document_id = %s
            """,
            (doc["document_id"],),
        )
        details = cur.fetchone()
        doc_detail = {
            "document_id": details[0],
            "title": details[1],
            "preview": details[2],
            "url": details[3],
        }
        doc_details.append(doc_detail)

    return doc_details
