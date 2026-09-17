from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from app.core.database import get_db
from app.models import User, AuditLog
from app.api.deps import get_current_user
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class AuditLogOut(BaseModel):
    id: UUID
    entity_type: str
    entity_id: UUID
    action: str
    old_value: str | None = None
    new_value: str | None = None
    user_id: UUID
    created_at: datetime
    
    model_config = {"from_attributes": True}

@router.get("/{entity_type}/{entity_id}", response_model=list[AuditLogOut])
def get_entity_audit_logs(entity_type: str, entity_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role not in ["CEO", "FINANCE"]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    logs = db.query(AuditLog).filter(
        AuditLog.company_id == current_user.company_id,
        AuditLog.entity_type == entity_type,
        AuditLog.entity_id == entity_id
    ).order_by(AuditLog.created_at.desc()).all()
    
    return logs
