import os

# import time
import psycopg
from index import init_crawl

while True:
    print("Polling......")
    print("DB_HOST configured:", bool(os.getenv("DB_HOST")))
    print("DB_PORT configured:", bool(os.getenv("DB_PORT")))
    print("DB_NAME configured:", bool(os.getenv("DB_NAME")))
    print("DB_USER configured:", bool(os.getenv("DB_USER")))
    print("DB_PASSWORD configured:", bool(os.getenv("DB_PASSWORD")))

    # start db connection
    conn = psycopg.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
    )

    cur = conn.cursor()

    # check for pending crawl jobs id
    cur.execute(
        """
        SELECT id
        FROM crawl_jobs
        WHERE status = 'pending'
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

                try:
                    init_crawl(conn)
                except Exception as e:
                    conn.rollback()
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
            elif status == "completed":
                cur.execute(
                    """
                    DELETE FROM crawl_jobs
                    WHERE id = %s;
                    """,
                    (id,),
                )

    cur.close()
    conn.close()
    # print("Sleeping......")
    # time.sleep(10)
    break

print("Polling stopped.")
