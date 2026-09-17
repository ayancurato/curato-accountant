from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional

from app.core.database import get_db
from app.models import User
from app.api.deps import get_current_user
from app.schemas.reports import TransactionReport
from app.services.report_service import get_reports

router = APIRouter()

@router.get("", response_model=TransactionReport)
def read_reports(
    preset: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    return get_reports(
        db, 
        current_user.company_id,
        preset=preset,
        date_from=date_from,
        date_to=date_to
    )
