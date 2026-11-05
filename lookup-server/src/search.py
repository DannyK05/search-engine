from utils.result_helpers import extract_ranked_documents, rank, tokenize


def query_db(query, con):

    # check db for token results
    tokens: list[str] = tokenize(query)

    if not tokens:
        return []  # guard against empty query

    rank_details = rank(con, tokens)

    results = extract_ranked_documents(con, rank_details)

    return results
