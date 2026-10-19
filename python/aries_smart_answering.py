"""ARIES Smart Answering API prototype.

This endpoint demonstrates request routing and telemetry only. It is not an LLM,
does not invoke the C++ executable, and does not prove or solve named open problems.
"""
from time import perf_counter
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="ARIES Smart Answering Prototype", version="0.1.0")


class QueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    mode: str = "deterministic_reasoning"


class QueryResponse(BaseModel):
    status: str
    reasoning_output: str
    execution_metrics: dict


@app.get("/health")
def health():
    return {"status": "ok", "backend": "prototype", "llm_connected": False}


@app.post("/v1/aries/query", response_model=QueryResponse)
def process_smart_query(req: QueryRequest):
    start = perf_counter()
    q = req.query.strip()
    lower = q.lower()

    if any(term in lower for term in ("riemann", "yang-mills", "navier-stokes")):
        response = (
            "This prototype recognized a mathematical-topic keyword. "
            "No theorem solver or mathematical proof was run. "
            "Provide a precise problem statement to evaluate with appropriate tests."
        )
    else:
        response = (
            "ARIES Smart Answering prototype received your query. "
            "This endpoint currently uses a deterministic template, not a trained language model."
        )

    elapsed_ms = (perf_counter() - start) * 1000
    return QueryResponse(
        status="OK",
        reasoning_output=response,
        execution_metrics={
            "latency_ms": round(elapsed_ms, 4),
            "backend": "template-prototype",
            "cpp_core_invoked": False,
            "llm_invoked": False,
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
