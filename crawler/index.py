from collections import Counter, deque
from urllib.parse import urlparse

import requests as r
from bs4 import BeautifulSoup
from crawler_types import Document
from dotenv import load_dotenv
from utils.database_helpers import (
    add_crawled_url,
    add_failed_url,
    add_known_url,
    create_db_tables,
)
from utils.helpers import (
    tokenize,
    url_parser,
)

load_dotenv()


def init_crawl(conn):
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
        "https://en.wikipedia.org/wiki/Main_Page",
        "https://github.com/explore",
        "https://developer.mozilla.org/en-US/",
        "https://docs.python.org/3/",
    ]
    # set urls that haven't been known
    seed_url: list[str] = [url for url in seed_url if url[0] not in known_urls]

    # fetch frontier from the db
    cur.execute(
        """
            SELECT url
            FROM frontier_urls
            """
    )
    frontier: deque[str] = deque(url[0] for url in cur.fetchall())
    if len(seed_url) > 0:
        for url in seed_url:
            frontier.appendleft(url)

    remaining_pages = 100

    # Crawling loop
    while len(frontier) > 0 and remaining_pages > 0:
        print(remaining_pages)
        # crawl the popped url from the frontier
        next_url = frontier.pop()
        print(f"Crawling: {next_url}")
        crawl(cur, next_url, frontier, known_urls)

        # delete the crawled url from the frontier db and add to known urls
        cur.execute(
            """
                DELETE FROM frontier_urls
                WHERE url = %s;
            """,
            (next_url,),
        )
        add_known_url(cur, next_url)
        conn.commit()

        remaining_pages -= 1

    conn.commit()


def crawl(cur, url: str, frontier: deque[str], known_urls: set[str]):

    hrefs: set[str] = (
        set()
    )  # initialize hrefs set to store the hrefs found in the crawled page
    domain = urlparse(url).netloc
    base = f"{urlparse(url).scheme}://{domain}"

    # requests and error handling
    try:
        response = r.get(url, timeout=10)
    except r.RequestException:
        # added to failed url to be reindexed later
        add_failed_url(cur, url)
        return

    html_body = response.text

    if not response.ok:
        add_failed_url(cur, url)
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

    ## persist document in the db and return its id
    cur.execute(
        """
            INSERT INTO documents (title, preview, url) 
            VALUES (%s, %s, %s)
            ON CONFLICT (url) DO NOTHING
            RETURNING document_id;
            """,
        (document["title"], document["preview"], document["url"]),
    )
    ## fetch the document id
    if cur.rowcount > 0:
        document_id = cur.fetchone()[0]
    else:
        ##TODO the if statement could always be truthy making this redundant
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
        ## persist token in tokens db and returns its id
        cur.execute(
            """
                INSERT INTO tokens (token) 
                VALUES (%s)
                ON CONFLICT (token) DO NOTHING
                RETURNING token_id;
                """,
            (word,),
        )
        ## fetch the token id
        if cur.rowcount > 0:
            token_id = cur.fetchone()[0]
        else:
            ##TODO the if statement could always be truthy making this redundant
            cur.execute(
                """
                SELECT token_id
                FROM tokens
                WHERE token = %s
                """,
                (word,),
            )
            token_id = cur.fetchone()[0]

        ## persist the document_tokens in the db
        cur.execute(
            """
                INSERT INTO document_tokens (token_id, document_id, document_size, token_count) 
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (token_id, document_id) DO NOTHING;
            """,
            (token_id, document_id, document_size, count),
        )

    # Select all anchor tags in the html document of the crawled link
    anchor_tags = soup.select("a[href]")

    # extract the href from the anchor tags
    for anchor in anchor_tags:
        hrefs.add(str(anchor["href"]))

    # parse the href to normalize it and convert them to valid hrefs
    for href in list(hrefs):
        parsed_url = url_parser(href, base)
        if parsed_url and (parsed_url not in known_urls):
            ## adds the new urls to known_url
            known_urls.add(parsed_url)
            cur.execute(
                """
                    INSERT INTO known_urls (url)
                    VALUES (%s)
                    ON CONFLICT (url) DO NOTHING
                    """,
                (parsed_url,),
            )

            ##Adds new url to frontier
            frontier.appendleft(parsed_url)
            cur.execute(
                """
                INSERT INTO frontier_urls (url)
                VALUES (%s)
                ON CONFLICT (url) DO NOTHING
                """,
                (parsed_url,),
            )
    # persist the succesfully crawled url
    add_crawled_url(cur, url)


# ## Trying out the search engine pipeline

# result = init_crawl("cook beans")
# print(result)
