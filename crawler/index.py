import os
from collections import Counter, deque
from urllib.parse import urlparse

import psycopg
import requests as r
from bs4 import BeautifulSoup
from crawler_types import Document
from dotenv import load_dotenv
from utils.database_helpers import create_db_tables
from utils.helpers import (
    extract_ranked_documents,
    rank,
    tokenize,
    url_parser,
)

load_dotenv()


def crawl(cur, url: str, frontier: deque[str], known_urls: set[str]):
    
    hrefs: set[str] = set() # initialize hrefs set to store the hrefs found in the crawled page
    domain = urlparse(url).netloc
    base = f"{urlparse(url).scheme}://{domain}"

    # requests and error handling
    try:
        response = r.get(url, timeout=10)
    except r.RequestException:
        return

    html_body = response.text

    if not response.ok:
        return
    # checks if response content is html
    if "html" not in response.headers.get("Content-Type", ""):
        return

    # parse the html_body to extract href values
    soup = BeautifulSoup(html_body, "html.parser")
    title = ""
    description = ""

    if soup.title and soup.title.string:
        title = soup.title.string
  

    description_tag = soup.select_one('meta[name="description"]')

    if description_tag:
        description = description_tag.get("content", "")
 
    document: Document = {"title": title, "preview": str(description), "url": url}

    cur.execute(
        """
            INSERT INTO documents (title, preview, url) 
            VALUES (%s, %s, %s)
            ON CONFLICT (url) DO NOTHING
            RETURNING document_id;
            """,
        (document["title"], document["preview"], document["url"]),
    )

    if cur.rowcount > 0:
        document_id = cur.fetchone()[0]
    else:
        cur.execute(
            """
            SELECT document_id
            FROM documents
            WHERE url = %s;
            """,
            (document["url"],),
        )
        document_id = cur.fetchone()[0]

    website_text = soup.get_text(" ", strip=True).lower()
    words = tokenize(website_text)
    document_size = len(words)
    word_count = Counter(words)

    for word, count in word_count.items():
        cur.execute(
            """
                INSERT INTO tokens (token) 
                VALUES (%s)
                ON CONFLICT (token) DO NOTHING
                RETURNING token_id;
                """,
            (word,),
        )

        if cur.rowcount > 0:
            token_id = cur.fetchone()[0]
        else:
            cur.execute(
                """
                SELECT token_id
                FROM tokens
                WHERE token = %s
                """,
                (word,),
            )
            token_id = cur.fetchone()[0]

        cur.execute(
            """
                INSERT INTO document_tokens (token_id, document_id, document_size, token_count) 
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (token_id, document_id) DO NOTHING;
            """,
            (token_id, document_id, document_size, count),
        )

    anchor_tags = soup.select("a[href]")

    for anchor in anchor_tags:
        hrefs.add(str(anchor["href"]))

    # parse the href to normalize it and convert them to valid hrefs
    for href in list(hrefs):
        parsed_url = url_parser(href, base)
        if (
            parsed_url
            and (parsed_url not in known_urls)
        ):
            frontier.appendleft(parsed_url)
            cur.execute(
                """
                    INSERT INTO known_urls (url)
                    VALUES (%s)
                    ON CONFLICT (url) DO NOTHING
                    """,
                (parsed_url,),
            )
            known_urls.add(parsed_url)


def search_engine(query):
    # start db connection
    conn = psycopg.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )
    cur = conn.cursor()

    # create db tables
    create_db_tables(cur)

    # fetch known urls from the db
    cur.execute(
        """
        SELECT url
        FROM known_urls
        """
    )
    known_urls: set[str] = {url[0] for url in cur.fetchall()}

    # intial seed urls
    seed_url = [
        ("https://en.wikipedia.org/wiki/Main_Page",),
        ("https://github.com/explore",),
        ("https://developer.mozilla.org/en-US/",),
        ("https://docs.python.org/3/",),
    ]
    seed_url = [url for url in seed_url if url[0] not in known_urls]

    cur.executemany(
        """
        INSERT into frontier_urls (url)
        VALUES (%s)
        ON CONFLICT (url) DO NOTHING
        """,
        seed_url,
    )

    # fetch frontier from the db
    cur.execute(
        """
            SELECT url
            FROM frontier_urls
            """
    )
    frontier: deque[str] = deque(url[0] for url in cur.fetchall())

    remaining_pages = 100

    # check db for token results
    tokens: list[str] = tokenize(query)

    if not tokens:
        return [] # guard against empty query
    
    rank_details = rank(cur, tokens)
    if len(rank_details) >= 10:
        results = extract_ranked_documents(cur, rank_details)
        conn.commit()
        cur.close()
        conn.close()

        return results

    # if the results aren't suffiecient i.e < 10, crawl
    # Crawling loop
    while len(frontier) > 0 and remaining_pages > 0:
        print(remaining_pages)
        # crawl the popped url from the frontier
        next_href = frontier.pop()
        print(f"Crawling: {next_href}")
        crawl(cur, next_href, frontier, known_urls)

        # delete the crawled url from the frontier db and add to known urls
        cur.execute(
            """
                DELETE FROM frontier_urls
                WHERE url = %s;
            """,
            (next_href,),
        )
        cur.execute(
            """
                INSERT INTO known_urls (url)
                VALUES (%s)
                ON CONFLICT (url) DO NOTHING
            """,
            (next_href,),
        )
        conn.commit()

        remaining_pages -= 1
        # check if we have enough results
        rank_details = rank(cur, tokens)
        if len(rank_details) >= 10:
            break

    # extract the url details from the ranked results
    results = extract_ranked_documents(cur, rank_details)

    # repopulate the db with the new frontier urls
    for url in frontier:
        cur.execute(
            """
            INSERT INTO frontier_urls (url)
            VALUES (%s)
            ON CONFLICT (url) DO NOTHING
            """,
            (url,),
        )
        
    conn.commit()
    cur.close()
    conn.close()

    return results


## Trying out the search engine pipeline

result = search_engine("cook beans")
print(result)
