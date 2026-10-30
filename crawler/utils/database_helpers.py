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

            CREATE TABLE IF NOT EXISTS crawled_urls(
                url_id SERIAL PRIMARY KEY,
                url TEXT UNIQUE
            );

            CREATE TABLE IF NOT EXISTS failed_urls(
                url_id SERIAL PRIMARY KEY,
                url TEXT UNIQUE
            );

            CREATE TABLE IF NOT EXISTS frontier_urls(
                url_id SERIAL PRIMARY KEY,
                url TEXT UNIQUE
            );
        """
    )
    cur.commit()


def add_failed_url(cur, url):
    cur.execute(
        """
            INSERT INTO failed_urls (url)
            VALUES (%s)
            ON CONFLICT (url) DO NOTHING
        """,
        (url,),
    )
    cur.commit()


def add_crawled_url(cur,url):
    cur.execute(
        """
            INSERT INTO crawled_urls (url)
            VALUES (%s)
            ON CONFLICT (url) DO NOTHING
        """,
        (url,),
    )
    cur.commit()

def add_known_url(cur,url):
    cur.execute(
        """
            INSERT INTO known_urls (url)
            VALUES (%s)
            ON CONFLICT (url) DO NOTHING
        """,
        (url,),
    )
    cur.commit()