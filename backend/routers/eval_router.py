from fastapi import APIRouter, HTTPException
from utils.evaluator import evaluator
router = APIRouter(prefix="/api/eval", tags=["evaluation"])



@router.get("/stats")
def get_stats(oc_id: str = ""):
    return evaluator.get_stats(doc_id or None)



@router.get("/recent")
def get_recent(n: int = 20, doc_id: str = ""):
    return {"records": evaluator.get_recent(n, doc_id or None)}



@router.get("/run/{run_id}")
def get_run(run_id: str):
    rec = evaluator.get_run(run_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Run not found")
    return rec
