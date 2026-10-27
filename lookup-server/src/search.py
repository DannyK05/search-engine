import pg8000.native
from utils.result_helpers import extract_ranked_documents, rank, tokenize


def query_db(query, hyperdrive):
    # start db connection
    con = pg8000.native.Connection(
        user=hyperdrive.user,
        password=hyperdrive.password,
        database=hyperdrive.database,
    )

    try:
        # check db for token results
        tokens: list[str] = tokenize(query)

        if not tokens:
            return []  # guard against empty query

        rank_details = rank(con, tokens)
        results = extract_ranked_documents(con, rank_details)
    except Exception as e:
        print(f"Error occurred while querying the database: {e}")
        return []
    finally:
        con.close()

    return results
