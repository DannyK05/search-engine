import os

import pg8000.native
from dotenv import load_dotenv
from utils.result_helpers import extract_ranked_documents, rank, tokenize

load_dotenv()   

def query_db(query):
    # start db connection
    print(os.getenv("DB_NAME"))
    con = pg8000.native.Connection(
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )
   

    try:
        # check db for token results
        tokens: list[str] = tokenize(query)

        if not tokens:
            return [] # guard against empty query
        
        rank_details = rank(con, tokens)
        results = extract_ranked_documents(con, rank_details)
    except Exception as e:
        print(f"Error occurred while querying the database: {e}")
        return []
    finally:
        con.close()

    return results
