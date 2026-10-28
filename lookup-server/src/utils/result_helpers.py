import math


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
    con,
    tokens: list[str],
):
    doc_ranking = {}
    rank_details = []

    try:
        total_docs = con.run(
            """
                SELECT COUNT(*)
                FROM documents
                """
        )[0][0]
    except Exception as e:
        print(f"Error occurred while querying the database: {e}")
        return rank_details

    
    for token in tokens:
        try:
            rows = con.run(
                """
                SELECT *
                FROM document_tokens
                WHERE token_id = (
                SELECT token_id
                FROM tokens
                WHERE token = :token
                )
                """,
                token=token
            )
        except Exception as e:
            print(f"Error occurred while querying the database for token '{token}': {e}")
            continue

        details = [row for row in rows]

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


def extract_ranked_documents(con, ranked_docs: list[dict]):
    """
    (list[dict]) => list[dict]

    Extracts the document details from the ranked documents

    """
    doc_details = []
    for doc in ranked_docs:
        try:
            details = con.run(
                """
                    SELECT *
                    FROM documents
                    WHERE document_id = :id
                    """,
                id=doc["document_id"]
            )[0]
        except Exception as e:
            print(f"Error occurred while querying the database for document '{doc['document_id']}': {e}")
            continue

        print(details)
        doc_detail = {
            "document_id": details[0],
            "title": details[1],
            "preview": details[2],
            "url": details[3],
        }
        doc_details.append(doc_detail)

    return doc_details
