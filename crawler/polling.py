import os
import time

import psycopg
from index import init_crawl

while True:
    # start db connection
    conn = psycopg.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )
    cur = conn.cursor()

    # check for pending crawl jobs id
    cur.execute(
        """
        SELECT id
        FROM crawl_jobs
        WHERE status = "pending"
        """
    )  # (id)

    pending_jobs_id = cur.fetchall()  # [(id1),(id2)]

    if len(pending_jobs_id) > 0:
        for job_id in pending_jobs_id:
            id = job_id[0]

            cur.execute(
                """
                    SELECT status
                    FROM crawl_jobs
                    WHERE id = %s
                    FOR UPDATE                  
                """,
                (id,),
            )
            if cur.rowcount > 0:
                status = cur.fetchone()[0]

            if status == "pending":
                print(f"Starting crawl job {id}")
                cur.execute(
                    """
                    UPDATE crawl_jobs
                    SET status = 'running'
                    WHERE id = %s;
                    """,
                    (id,),
                )
                conn.commit()

                try:
                    init_crawl(conn)
                except Exception as e:
                    print(f"Error occurred while running a job with id {id}: {e}")
                    cur.execute(
                        """
                        UPDATE crawl_jobs
                        SET status = 'pending'
                        WHERE id = %s;
                        """,
                        (id,),
                    )
                    continue

                cur.execute(
                    """
                    UPDATE crawl_jobs
                    SET status = 'completed'
                    WHERE id = %s;
                    """,
                    (id,),
                )
                conn.commit()
            elif status == "completed":
                cur.execute(
                    """
                    DELETE FROM crawl_jobs
                    WHERE id = %s;
                    """,
                    (id,),
                )
                conn.commit()

    cur.close()
    conn.close()
    time.sleep(10)
