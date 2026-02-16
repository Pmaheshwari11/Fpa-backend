from datetime import date
from database import SessionLocal
from models import Followup

def run():
    db = SessionLocal()
    today = date.today()

    # Only update followups that are still PENDING
    active_followups = db.query(Followup).filter(Followup.status == "PENDING").all()

    for f in active_followups:
        days = (f.followup_date - today).days
        f.days_remaining = days

        if days < 0:
            f.urgency = "OVERDUE"
        elif days <= 2:
            f.urgency = "HIGH"
        elif days <= 7:
            f.urgency = "MEDIUM"
        else:
            f.urgency = "LOW"

    db.commit()
    db.close()
    print(f"Updated {len(active_followups)} active follow-ups.")