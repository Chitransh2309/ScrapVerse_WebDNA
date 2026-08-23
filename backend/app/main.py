import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import companies, sequencing, genome, mutations, evidence, scrapers, agent
from app.db.session import engine, Base

app = FastAPI(
    title="Web DNA API",
    description="Agentic company-intelligence platform",
    version="1.0.0"
)

frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app.include_router(companies.router, prefix="/api/companies", tags=["companies"])
app.include_router(sequencing.router, prefix="/api/companies/{company_id}/sequence", tags=["sequencing"])
app.include_router(evidence.router, prefix="/api/companies/{company_id}/evidence", tags=["evidence"])
app.include_router(genome.router, prefix="/api/companies/{company_id}/genome", tags=["genome"])
app.include_router(mutations.router, prefix="/api/companies/{company_id}/mutations", tags=["mutations"])
app.include_router(agent.router, prefix="/api", tags=["agent"])
app.include_router(scrapers.router, prefix="/api", tags=["scrapers"])
