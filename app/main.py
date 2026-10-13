from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, company, documents, expenses, income, categories, vendors, reports, audit, ca, settings as settings_api
from app.core.config import settings
from app.core.database import Base, engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="Curato AI Expense & Finance",
    description="Internal Curato AI application for expense management.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
origins = [origin.strip() for origin in settings.FRONTEND_URL.split(",") if origin.strip()]
if "*" in origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_origin_regex=r"https://.*\.vercel\.app",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include Routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(company.router, prefix="/api/v1/company", tags=["Company"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])
app.include_router(expenses.router, prefix="/api/v1/expenses", tags=["Expenses"])
app.include_router(income.router, prefix="/api/v1/income", tags=["Income"])
app.include_router(ca.router, prefix="/api/v1/ca", tags=["CA Export"])
app.include_router(categories.router, prefix="/api/v1/categories", tags=["Categories"])
app.include_router(vendors.router, prefix="/api/v1/vendors", tags=["Vendors"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])
app.include_router(audit.router, prefix="/api/v1/audit", tags=["Audit"])
app.include_router(settings_api.router, prefix="/api/v1/settings", tags=["Settings"])

@app.get("/")
def read_root():
    return {"message": "Curato AI Expense API"}
