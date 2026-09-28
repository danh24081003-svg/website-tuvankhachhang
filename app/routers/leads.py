from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Customer, Lead
from app.schemas import LeadCreate, LeadOut


router = APIRouter(prefix="/api/leads", tags=["leads"])


@router.post("", response_model=LeadOut)
def create_lead(payload: LeadCreate, db: Session = Depends(get_db)):
    customer = db.scalars(select(Customer).where(Customer.phone == payload.phone)).first()
    if customer:
        customer.name = payload.name
        customer.address = payload.address
    else:
        customer = Customer(name=payload.name, phone=payload.phone, address=payload.address)
        db.add(customer)
        db.flush()

    lead = Lead(
        customer_id=customer.id,
        service=payload.service,
        message=payload.message,
        status="new",
        source="FORM",
        location=payload.address,
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return {
        "id": lead.id,
        "status": lead.status,
        "message": "Dạ bên em đã tiếp nhận thông tin. Nhân viên tư vấn sẽ liên hệ với anh/chị sớm nhất ạ.",
    }
