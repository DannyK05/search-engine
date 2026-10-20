from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from search import query_db
from workers import WorkerEntrypoint, asgi

app = FastAPI()

origins =["http://localhost:5173", ]

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
async def query(q: str):
    results = query_db(q)
    return {"results": results}


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        return await asgi.fetch(app, request, self.env)
