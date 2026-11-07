import pg8000.native
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from search import query_db
from utils.database_helper import create_new_job, init_job_db
from workers import WorkerEntrypoint, asgi

app = FastAPI()

origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Hello from FastAPI on Cloudflare Workers!"}


@app.get("/query")
async def query(q: str, request: Request):
    hyperdrive = request.app.state.hyperdrive
    # start db connection
    con = pg8000.native.Connection(
        user=hyperdrive.user,
        password=hyperdrive.password,
        database=hyperdrive.database,
    )

    init_job_db(con)
    #TODO make creating a new job only when the results are insufficient
    create_new_job(con)
    results = query_db(q, con)
    con.close()
    return {"results": results}


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        app.state.hyperdrive = self.env.HYPERDRIVE
        return await asgi.fetch(app, request, self.env)
