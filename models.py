from sqlalchemy import Column, Integer, String, Float, Date, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Contact(Base):

    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True)

    company = Column(String)

    contact_name = Column(String)

    designation = Column(String)

    department = Column(String)

    email = Column(String)

    linkedin = Column(String)

    date_contacted = Column(Date)

    next_followup = Column(Date)

    status = Column(String)

    priority_score = Column(Float, default=0)

    probability = Column(Float, default=0)

    opportunity_value = Column(Float, default=0)

    expected_value = Column(Float, default=0)

    notes = Column(Text)

    followups = relationship("Followup", back_populates="contact")


class Followup(Base):

    __tablename__ = "followups"

    id = Column(Integer, primary_key=True)

    contact_id = Column(Integer, ForeignKey("contacts.id"))

    followup_date = Column(Date)

    days_remaining = Column(Integer)

    urgency = Column(String)

    status = Column(String, default="PENDING")

    contact = relationship("Contact", back_populates="followups")


class Template(Base):

    __tablename__ = "templates"

    id = Column(Integer, primary_key=True)

    template_name = Column(String)

    template_text = Column(Text)


class Metric(Base):

    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True)

    week = Column(Date)

    contacts_added = Column(Integer)

    responses = Column(Integer)

    interviews = Column(Integer)

    offers = Column(Integer)
