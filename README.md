# Search Engine

An experimental search engine built from the ground up, exploring web crawling, information retrieval, document indexing, and search ranking.

This personal project aims to provide a foundation for searching content collected from multiple sources, with an initial focus on crawling and indexing web pages.

## Overview

This project combines a Python-based web crawler, a PostgreSQL-backed indexing system, and a FastAPI search service.

Rather than relying on an external search API, it implements the core components of a search engine:

- Discovering and crawling web pages.
- Extracting and processing page content.
- Tokenizing and indexing documents.
- Retrieving relevant documents using an inverted index.
- Ranking search results using a TF-IDF-style approach.
- Processing crawl requests asynchronously through a database-backed job queue.

The project is a work in progress, with the current implementation serving as an MVP.

## Architecture

The system is divided into a few major components:

### 1. Web Crawler

The crawler is responsible for discovering and collecting web pages.

It uses Python's `requests` library to retrieve pages and BeautifulSoup to parse HTML content.

Its responsibilities include:

- Fetching web pages.
- Extracting page content and links.
- Discovering additional URLs.
- Filtering unsupported or invalid URLs.
- Preparing extracted content for indexing.

### 2. Indexing and Information Retrieval

Extracted documents are processed and stored in PostgreSQL.

The indexing system uses:

- **Tokenization** to break document content into searchable terms.
- **Inverted indexing** to map tokens to the documents containing them.
- **Document statistics** to track token frequencies and document sizes.
- **TF-IDF-style ranking** to estimate the relevance of documents to a search query.

### 3. Search API

The search service is built with FastAPI and deployed on Cloudflare Workers.

It receives search queries, retrieves matching documents from PostgreSQL, and returns ranked results.

Cloudflare Hyperdrive is used to manage database connectivity between the Worker and PostgreSQL.

### 4. Background Crawl Processing

Crawling is separated from the search request lifecycle so that users do not have to wait for additional pages to be discovered and indexed.

The search service can enqueue crawl jobs in PostgreSQL, while a separate worker polls the database for pending jobs and processes them.

This approach allows the search service to return available results while additional content is being collected and indexed.

## Technology Stack

| Area | Technologies |
|---|---|
| Language | Python |
| Web crawling | Requests, BeautifulSoup |
| Search API | FastAPI |
| Database | PostgreSQL |
| Database driver | psycopg, pg8000 |
| Deployment | Cloudflare Workers |
| Database connectivity | Cloudflare Hyperdrive |
| Dependency management | uv |

## Project Structure

```text
search-engine/
├── crawler/
│   ├── utils/
│   │   └── database_helpers.py
│   │   └── helpers.py
│   ├── index.py
│   ├── polling.py
│   ├── crawler_types.py
│   ├── requirements.txt
│   └── .gitignore
├── lookup-server/
│   ├── src/
│   │    ├── utils/
│   │    │   └── database_helpers.py
│   │    │   └── result_helpers.py
│   │    └── entry.py
│   │    └── search.py
│   ├── .gitignore
│   ├── .python-version
│   ├── package-lock.json
│   ├── package.json
│   ├── pylock.toml
│   ├── pyproject.toml
│   ├── uv.lock
│   └── wrangler.jsonc
└── README.md
```

*The structure above is a simplified representation and may change as the project evolves.*

## Getting Started

### Prerequisites

- Python 3.13 or later
- PostgreSQL
- [uv](https://docs.astral.sh/uv/)
- Node.js and npm (for Wrangler and Cloudflare Workers tooling)

### Installation

Clone the repository:

```bash
git clone https://github.com/DannyK05/web-crawler.git
cd search-engine
cd lookup-server
uv sync
```

Install the lookup server dependencies:

```bash
cd lookup-server
uv sync
```

### Environment Variables

Configure the database connection details using environment variables.

```env
DB_NAME=
DB_USER=
DB_PASSWORD=
```

Additional configuration may be required depending on whether you're running the application locally or deploying it to Cloudflare Workers.

**Never commit credentials or environment files containing secrets.**

### Running the Project

The crawler and search service are separate components and should be configured and started independently.

Refer to the configuration files and individual component instructions as the project continues to develop.

*Local execution and deployment instructions will be expanded as the development workflow stabilizes.*

## Current Status

The project is actively under development.

The current MVP focuses on establishing the core search pipeline:

- [x] Basic web crawling and HTML parsing.
- [x] URL discovery and filtering.
- [x] PostgreSQL-backed document and token storage.
- [x] Token-based document indexing.
- [x] Inverted-index-based document retrieval.
- [x] Initial relevance ranking.
- [x] FastAPI search service.
- [x] Cloudflare Workers deployment and Hyperdrive integration.
- [x] Complete and validate background crawl-job processing.
- [ ] Improve error handling and worker recovery.
- [ ] Expand automated test coverage.
- [ ] Improve documentation and local setup instructions.


## Future Development

The long-term goal is to expand the search engine beyond its initial web-page crawling implementation.

Potential areas of development include:

- Supporting additional content sources such as Wikipedia and YouTube.
- Improving document extraction and content processing.
- Exploring more advanced ranking and relevance algorithms.
- Improving crawling efficiency and URL discovery.
- Introducing more robust background job processing.
- Improving search performance and database query efficiency.
- Expanding support for different content types, including images and videos.

## Motivation

This project is an opportunity to explore the engineering behind search systems, from collecting and processing web data to indexing, retrieval, and ranking.

It is also a practical learning project for understanding backend systems, databases, information retrieval, and distributed processing through implementation.

## Contributing

This is currently a personal learning and development project. Suggestions, feedback, and discussions are welcome.

## License
This project is currently not distributed under an open-source license. All rights are reserved by the author.
```
