from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, datetime, timedelta
import calendar
import re
from fastapi import HTTPException

# Import the classes directly to match your function logic
from models import Contact, Followup, Metric
from forecast import calculate_expected_value

# --- CONTACTS ---

def create_contact(db: Session, data):
    # 1. Type and Presence Validations
    company = data.get("company")
    contact_name = data.get("contact_name")
    email = data.get("email")
    
    # Check for empty strings or None
    if not isinstance(company, str) or not company.strip():
        raise HTTPException(status_code=400, detail="Company name must be a non-empty string.")
    
    if not isinstance(contact_name, str) or not contact_name.strip():
        raise HTTPException(status_code=400, detail="Contact name must be a non-empty string.")

    # 2. Email Format Validation (@ check)
    if email:
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            raise HTTPException(status_code=400, detail="Invalid email format.")

    # 3. Probability & Value Validations
    try:
        prob = float(data.get("probability", 0))
        value = float(data.get("opportunity_value", 0))
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Probability and Value must be numbers.")

    if not (0 <= prob <= 1):
        raise HTTPException(status_code=400, detail="Probability must be between 0 and 1.")
    
    if value < 0:
        raise HTTPException(status_code=400, detail="Opportunity value cannot be negative.")

    # --- If all checks pass, proceed to creation ---
    
    expected_value = calculate_expected_value(prob, value)

    contact = Contact(
        company=company.strip(),
        contact_name=contact_name.strip(),
        email=email.strip() if email else None,
        probability=prob,
        opportunity_value=value,
        expected_value=expected_value,
        status=data.get("status", "New Lead"),
        date_contacted=date.today() 
    )

    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact

def get_contacts(db: Session):
    return db.query(Contact).all()

def delete_contact(db: Session, id: int):
    obj = db.query(Contact).filter(Contact.id == id).first()
    if obj:
        db.delete(obj)
        db.commit()

# --- DASHBOARD (Real Data) ---

def get_dashboard(db: Session):
    contacts = db.query(Contact).all()
    total_contacts = len(contacts)
    expected_value = sum(c.expected_value for c in contacts)
    total_pipeline = sum(c.opportunity_value for c in contacts)

    # Real Revenue Projection: Grouping by month of 'date_contacted'
    monthly_stats = db.query(
        func.extract('month', Contact.date_contacted).label('month'),
        func.sum(Contact.expected_value).label('value')
    ).group_by('month').order_by('month').all()

    projection_data = []
    for row in monthly_stats:
        if row.month:
            month_name = calendar.month_name[int(row.month)][:3]
            projection_data.append({"name": month_name, "value": float(row.value or 0)})

    if not projection_data:
        projection_data = [{"name": "No Data", "value": 0}]

    # Real Lead Distribution by probability
    high = db.query(Contact).filter(Contact.probability >= 0.7).count()
    med = db.query(Contact).filter(Contact.probability >= 0.4, Contact.probability < 0.7).count()
    low = db.query(Contact).filter(Contact.probability < 0.4).count()

    distribution_data = [
        {"name": "High (>70%)", "value": high},
        {"name": "Medium (40-70%)", "value": med},
        {"name": "Low (<40%)", "value": low},
    ]

    return {
        "contacts": total_contacts,
        "expected_value": expected_value,
        "total_pipeline": total_pipeline,
        "projection_data": projection_data,
        "distribution_data": distribution_data
    }

# --- FOLLOW-UPS ---

def create_followup(db: Session, contact_id: int, followup_date: date):
    today = date.today()
    days = (followup_date - today).days
    
    if days < 0: urgency = "OVERDUE"
    elif days <= 2: urgency = "HIGH"
    elif days <= 7: urgency = "MEDIUM"
    else: urgency = "LOW"

    db_followup = Followup(
        contact_id=contact_id,
        followup_date=followup_date,
        days_remaining=days,
        urgency=urgency,
        status="PENDING"
    )
    db.add(db_followup)

    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if contact:
        contact.next_followup = db.query(func.min(Followup.followup_date)).filter(
            Followup.contact_id == contact_id, 
            Followup.status == "PENDING"
        ).scalar()

    db.commit()
    db.refresh(db_followup)
    return db_followup

def get_followups(db: Session, include_completed: bool = False):
    # Joining Followup and Contact to get Company names for the UI
    query = db.query(
        Followup.id,
        Followup.followup_date,
        Followup.days_remaining,
        Followup.urgency,
        Followup.status,
        Followup.contact_id,
        Contact.company,
        Contact.contact_name
    ).join(Contact, Followup.contact_id == Contact.id)
    
    if not include_completed:
        query = query.filter(Followup.status == "PENDING")
        
    results = query.order_by(Followup.followup_date.asc()).all()

    return [
        {
            "id": r.id,
            "contact_id": r.contact_id,
            "followup_date": str(r.followup_date),
            "days_remaining": r.days_remaining,
            "urgency": r.urgency,
            "status": r.status,
            "company": r.company,
            "contact_name": r.contact_name
        } for r in results
    ]

def update_followup_status(db: Session, followup_id: int, new_status: str):
    db_followup = db.query(Followup).filter(Followup.id == followup_id).first()
    
    if db_followup:
        db_followup.status = new_status
        contact_id = db_followup.contact_id
        
        # After marking as COMPLETED, we need to find the NEXT pending followup for this contact
        # If no other pending followups exist, this will return None
        next_date = db.query(func.min(Followup.followup_date)).filter(
            Followup.contact_id == contact_id,
            Followup.status == "PENDING",
            Followup.id != followup_id # Don't count the one we just finished
        ).scalar()

        # Update the parent contact
        contact = db.query(Contact).filter(Contact.id == contact_id).first()
        if contact:
            contact.next_followup = next_date

        db.commit()
        db.refresh(db_followup)
    return db_followup


def delete_followup(db: Session, followup_id: int):
    db_followup = db.query(Followup).filter(Followup.id == followup_id).first()
    
    if db_followup:
        contact_id = db_followup.contact_id
        db.delete(db_followup)
        
        # Find the next available date after deletion
        next_date = db.query(func.min(Followup.followup_date)).filter(
            Followup.contact_id == contact_id,
            Followup.status == "PENDING",
            Followup.id != followup_id
        ).scalar()

        contact = db.query(Contact).filter(Contact.id == contact_id).first()
        if contact:
            contact.next_followup = next_date
            
        db.commit()
    return True