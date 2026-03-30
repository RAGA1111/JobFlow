"""Database models and operations for job application tracking."""
from datetime import datetime
from typing import Optional, List
import uuid

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from config import settings

Base = declarative_base()


class User(Base):
    """User model storing profile and resume information."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    phone = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    resume_text = Column(Text, nullable=True)
    role = Column(String, nullable=True)
    location = Column(String, nullable=True)
    years_experience = Column(Integer, nullable=True)
    skills = Column(Text, nullable=True)  # Comma-separated skills
    salary_range = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Job(Base):
    """Job model storing scraped job listings."""
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    location = Column(String, nullable=True)
    salary = Column(String, nullable=True)
    skills_required = Column(Text, nullable=True)
    experience_required = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    apply_url = Column(String, nullable=False)
    source = Column(String, nullable=False)  # naukri, indeed, etc.
    scraped_at = Column(DateTime, default=datetime.utcnow)


class Application(Base):
    """Application model tracking job applications."""
    __tablename__ = "applications"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_phone = Column(String, nullable=False, index=True)
    job_title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    location = Column(String, nullable=True)
    salary = Column(String, nullable=True)
    apply_url = Column(String, nullable=False)
    fit_score = Column(Integer, nullable=True)
    status = Column(String, nullable=False, default="pending")  # applied, skipped, failed, captcha_blocked
    cover_letter = Column(Text, nullable=True)
    applied_at = Column(DateTime, default=datetime.utcnow)
    session_id = Column(String, nullable=True, index=True)
    error_message = Column(Text, nullable=True)


# Database engine and session
engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()


# User operations
def create_user(phone: str, name: Optional[str] = None, email: Optional[str] = None) -> User:
    """Create a new user."""
    db = get_db()
    user = User(phone=phone, name=name, email=email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_phone(phone: str) -> Optional[User]:
    """Get user by phone number."""
    db = get_db()
    return db.query(User).filter(User.phone == phone).first()


def update_user_profile(
    phone: str,
    name: Optional[str] = None,
    email: Optional[str] = None,
    resume_text: Optional[str] = None,
    role: Optional[str] = None,
    location: Optional[str] = None,
    years_experience: Optional[int] = None,
    skills: Optional[str] = None,
    salary_range: Optional[str] = None
) -> Optional[User]:
    """Update user profile."""
    db = get_db()
    user = db.query(User).filter(User.phone == phone).first()
    if not user:
        return None
    
    if name:
        user.name = name
    if email:
        user.email = email
    if resume_text:
        user.resume_text = resume_text
    if role:
        user.role = role
    if location:
        user.location = location
    if years_experience is not None:
        user.years_experience = years_experience
    if skills:
        user.skills = skills
    if salary_range:
        user.salary_range = salary_range
    
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user


# Job operations
def store_job(
    title: str,
    company: str,
    location: Optional[str],
    salary: Optional[str],
    skills_required: Optional[str],
    experience_required: Optional[str],
    description: Optional[str],
    apply_url: str,
    source: str
) -> Job:
    """Store a scraped job."""
    db = get_db()
    job = Job(
        title=title,
        company=company,
        location=location,
        salary=salary,
        skills_required=skills_required,
        experience_required=experience_required,
        description=description,
        apply_url=apply_url,
        source=source
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_job_by_url(apply_url: str) -> Optional[Job]:
    """Get job by apply URL."""
    db = get_db()
    return db.query(Job).filter(Job.apply_url == apply_url).first()


# Application operations
def store_application(
    user_phone: str,
    job_title: str,
    company: str,
    location: Optional[str],
    salary: Optional[str],
    apply_url: str,
    fit_score: Optional[int],
    status: str,
    cover_letter: Optional[str] = None,
    session_id: Optional[str] = None,
    error_message: Optional[str] = None
) -> Application:
    """Store an application attempt."""
    db = get_db()
    application = Application(
        user_phone=user_phone,
        job_title=job_title,
        company=company,
        location=location,
        salary=salary,
        apply_url=apply_url,
        fit_score=fit_score,
        status=status,
        cover_letter=cover_letter,
        session_id=session_id or str(uuid.uuid4()),
        error_message=error_message
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


def get_applications_by_user(phone: str, limit: int = 50) -> List[Application]:
    """Get applications for a user."""
    db = get_db()
    return db.query(Application).filter(
        Application.user_phone == phone
    ).order_by(Application.applied_at.desc()).limit(limit).all()


def get_application_status_summary(phone: str) -> dict:
    """Get application status summary for a user."""
    db = get_db()
    applications = db.query(Application).filter(Application.user_phone == phone).all()
    
    summary = {
        "total": len(applications),
        "applied": len([a for a in applications if a.status == "applied"]),
        "failed": len([a for a in applications if a.status == "failed"]),
        "skipped": len([a for a in applications if a.status == "skipped"]),
        "captcha_blocked": len([a for a in applications if a.status == "captcha_blocked"]),
        "recent": applications[:10]  # Last 10 applications
    }
    return summary


def has_applied_to_company(phone: str, company: str, session_id: Optional[str] = None) -> bool:
    """Check if user has already applied to a company in current session."""
    db = get_db()
    query = db.query(Application).filter(
        Application.user_phone == phone,
        Application.company.ilike(f"%{company}%")
    )
    if session_id:
        query = query.filter(Application.session_id == session_id)
    return query.first() is not None


# Initialize database on module import
init_db()
