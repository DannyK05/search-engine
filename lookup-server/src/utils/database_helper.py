def init_job_db(con):
    con.run(
    """
        CREATE TABLE IF NOT EXISTS crawl_jobs(
            id SERIAL PRIMARY KEY,
            status TEXT,
        )
    """
    )


def create_new_job(con):
    con.run(
        """
            INSERT INTO crawl_jobs(status)
            VALUES (:status)
        """,
        status="pending"
    )