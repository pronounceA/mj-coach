from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import analysis, rules

app = FastAPI(title="mj-coach API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
app.include_router(rules.router, prefix="/api/rules", tags=["rules"])


@app.get("/health")
async def health():
    return {"status": "ok"}
