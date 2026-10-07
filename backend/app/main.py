from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from routers.upload_router import router as upload_router
from routers.query_router import router as query_router
from routers.eval_router import router as eval_router

from utils.logger import setup_logging
from utils.evaluator import evaluator


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    evaluator.load_from_disk()
    yield


app = FastAPI(
    title="Financial Report Analyst API",
    description="RAG + CRAG + Self-RAG pipeline for financial document analysis",
    version="1.0.0",
    lifespan=lifespan,
)
 

app.add_middleware(
    CORSMiddleware,
    allow_origins=[                
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,       
    allow_methods=["*"],          
    allow_headers=["*"],           
)

app.include_router(upload_router)
app.include_router(query_router)
app.include_router(eval_router)


@app.get("/health")
def health():
    return {"status": "ok"}


