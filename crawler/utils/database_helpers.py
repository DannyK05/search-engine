def create_db_tables(cur):
    cur.execute(
            """
                CREATE TABLE IF NOT EXISTS documents(
                    document_id SERIAL PRIMARY KEY,
                    title TEXT,
                    preview TEXT,
                    url TEXT UNIQUE
                );
    
                CREATE TABLE IF NOT EXISTS tokens(
                    token_id SERIAL PRIMARY KEY,
                    token TEXT UNIQUE
                );
    
                CREATE TABLE IF NOT EXISTS document_tokens(
                    token_id INT REFERENCES tokens(token_id),
                    document_id INT REFERENCES documents(document_id),
                    document_size INT,
                    token_count INT,
                    PRIMARY KEY (token_id, document_id)
                );
                
                CREATE TABLE IF NOT EXISTS known_urls(
                    url_id SERIAL PRIMARY KEY,
                    url TEXT UNIQUE
                );
    
                CREATE TABLE IF NOT EXISTS frontier_urls(
                    url_id SERIAL PRIMARY KEY,
                    url TEXT UNIQUE
                );
            """
        )