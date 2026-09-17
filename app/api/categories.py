from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.core.database import get_db
from app.models import User, Category
from app.api.deps import get_current_user
from app.schemas.category import CategoryOut, CategoryCreate, CategoryUpdate

router = APIRouter()

@router.get("", response_model=List[CategoryOut])
def get_categories(
    type: str | None = None,
    include_archived: bool = False,
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    query = db.query(Category).filter(Category.company_id == current_user.company_id)
    if type:
        query = query.filter(Category.type == type)
    if not include_archived:
        query = query.filter(Category.is_archived == False)
    return query.all()

@router.post("", response_model=CategoryOut)
def create_category(category: CategoryCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role not in ["CEO", "FINANCE"]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    db_cat = Category(**category.model_dump(), company_id=current_user.company_id)
    db.add(db_cat)
    db.commit()
    db.refresh(db_cat)
    return db_cat

@router.patch("/{id}", response_model=CategoryOut)
def update_category(id: UUID, category_update: CategoryUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role not in ["CEO", "FINANCE"]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    cat = db.query(Category).filter(Category.id == id, Category.company_id == current_user.company_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
        
    update_data = category_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(cat, key, value)
        
    db.commit()
    db.refresh(cat)
    return cat

@router.delete("/{id}")
def delete_category(id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "CEO":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    cat = db.query(Category).filter(Category.id == id, Category.company_id == current_user.company_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
        
    # Soft delete (archive)
    cat.is_archived = True
    db.commit()
    return {"message": "Category archived"}
