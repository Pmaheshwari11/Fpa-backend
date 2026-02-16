from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

# Import from your local files
import models
import crud
from database import engine, SessionLocal

# Create tables on startup
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://fpa-frontend-gold.vercel.app"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to handle the session lifecycle
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def health_check():
    return {"status": "healthy"}


@app.get("/")
def root():

    return {"status": "running"}


@app.post("/contacts")
def create_contact(data: dict, db: Session = Depends(get_db)):

    return crud.create_contact(db, data)


@app.get("/contacts")
def contacts(db: Session = Depends(get_db)):

    return crud.get_contacts(db)


@app.delete("/contacts/{id}")
def delete(id: int, db: Session = Depends(get_db)):

    crud.delete_contact(db, id)

    return {"deleted": True}


@app.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):

    return crud.get_dashboard(db)

@app.get("/followups")
def get_followups(include_completed: bool = False, db: Session = Depends(get_db)):
    print("followups")
    # Use the logic from crud.py that joins with the Contacts table
    return crud.get_followups(db, include_completed=include_completed)

@app.post("/followups")
def create_followup(data: dict, db: Session = Depends(get_db)):
    # Expects {"contact_id": 1, "followup_date": "2026-02-18"}
    from datetime import datetime
    f_date = datetime.strptime(data["followup_date"], "%Y-%m-%d").date()
    return crud.create_followup(db, data["contact_id"], f_date)

@app.patch("/followups/{id}/complete")
def complete_followup(id: int, db: Session = Depends(get_db)):
    return crud.update_followup_status(db, id, "COMPLETED")
