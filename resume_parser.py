"""Resume parsing module for extracting text and structured data from PDFs."""
import json
from typing import Optional, Dict, Any
from pathlib import Path

import pdfplumber
from groq import Groq

from config import settings, GROQ_MODELS


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF using pdfplumber."""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error extracting PDF text: {e}")
        return ""
    
    return text.strip()


def parse_resume_with_groq(resume_text: str) -> Dict[str, Any]:
    """Parse resume text using Groq to extract structured information."""
    client = Groq(api_key=settings.GROQ_API_KEY)
    
    prompt = f"""Parse the following resume and extract structured information.
Return ONLY a valid JSON object with these fields:
- name: Full name of the candidate
- email: Email address
- phone: Phone number
- location: Current location/city
- skills: List of technical skills (programming languages, frameworks, tools, etc.)
- experience_years: Total years of experience (integer)
- education: Highest education level
- current_role: Current job title or "Fresher" if no experience
- summary: Brief professional summary

Resume text:
{resume_text}

Respond with ONLY the JSON object, no additional text."""

    try:
        response = client.chat.completions.create(
            model=GROQ_MODELS["profile_parsing"],
            messages=[
                {"role": "system", "content": "You are a resume parser. Extract structured data from resumes and return valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1000
        )
        
        content = response.choices[0].message.content.strip()
        
        # Clean up JSON if wrapped in markdown code blocks
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        content = content.strip()
        parsed = json.loads(content)
        return parsed
        
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print(f"Raw content: {content}")
        return {
            "name": None,
            "email": None,
            "phone": None,
            "location": None,
            "skills": [],
            "experience_years": 0,
            "education": None,
            "current_role": None,
            "summary": resume_text[:500] if resume_text else None
        }
    except Exception as e:
        print(f"Error parsing resume with Groq: {e}")
        return {
            "name": None,
            "email": None,
            "phone": None,
            "location": None,
            "skills": [],
            "experience_years": 0,
            "education": None,
            "current_role": None,
            "summary": resume_text[:500] if resume_text else None
        }


def parse_user_preferences(message: str, resume_skills: Optional[list] = None) -> Dict[str, Any]:
    """Parse user preferences from WhatsApp message using Groq."""
    client = Groq(api_key=settings.GROQ_API_KEY)
    
    skills_context = f"\nSkills from resume: {', '.join(resume_skills)}" if resume_skills else ""
    
    prompt = f"""Parse the following job preference message and extract structured information.
Return ONLY a valid JSON object with these fields:
- role: Target job role/title (e.g., "ML Engineer", "Full Stack Developer")
- location: Preferred job location (e.g., "Chennai", "Bangalore", "Remote")
- years_experience: Years of experience (integer)
- skills: List of key skills mentioned (array of strings)
- salary_range: Expected salary range (e.g., "10-15 LPA", "5-8 LPA")
- job_type: Type of job (Full-time, Part-time, Internship, Contract)

User message:
{message}
{skills_context}

Respond with ONLY the JSON object, no additional text."""

    try:
        response = client.chat.completions.create(
            model=GROQ_MODELS["intent_parsing"],
            messages=[
                {"role": "system", "content": "You are a job preference parser. Extract structured data from user messages and return valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=500
        )
        
        content = response.choices[0].message.content.strip()
        
        # Clean up JSON if wrapped in markdown code blocks
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        content = content.strip()
        parsed = json.loads(content)
        return parsed
        
    except Exception as e:
        print(f"Error parsing preferences: {e}")
        # Fallback: return basic structure
        return {
            "role": None,
            "location": None,
            "years_experience": None,
            "skills": resume_skills or [],
            "salary_range": None,
            "job_type": "Full-time"
        }


def parse_job_suggestion_query(message: str) -> Dict[str, Any]:
    """Parse a job suggestion query from user message."""
    client = Groq(api_key=settings.GROQ_API_KEY)
    
    prompt = f"""Parse the following job search query and extract structured information.
Return ONLY a valid JSON object with these fields:
- query_type: "job_suggestion" (always)
- role: Target job role/title
- location: Job location
- salary_range: Expected salary range
- experience: Years of experience mentioned
- skills: List of specific skills mentioned
- additional_filters: Any other filters (remote, immediate joining, etc.)

User message:
{message}

Respond with ONLY the JSON object, no additional text."""

    try:
        response = client.chat.completions.create(
            model=GROQ_MODELS["intent_parsing"],
            messages=[
                {"role": "system", "content": "You are a query parser. Extract job search parameters from user messages and return valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=500
        )
        
        content = response.choices[0].message.content.strip()
        
        # Clean up JSON
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        content = content.strip()
        parsed = json.loads(content)
        return parsed
        
    except Exception as e:
        print(f"Error parsing job suggestion query: {e}")
        return {
            "query_type": "job_suggestion",
            "role": None,
            "location": None,
            "salary_range": None,
            "experience": None,
            "skills": [],
            "additional_filters": {}
        }


def process_resume(pdf_path: str) -> Dict[str, Any]:
    """Full resume processing pipeline."""
    # Extract text from PDF
    resume_text = extract_text_from_pdf(pdf_path)
    
    if not resume_text:
        return {
            "success": False,
            "error": "Could not extract text from PDF",
            "data": None
        }
    
    # Parse with Groq
    parsed_data = parse_resume_with_groq(resume_text)
    parsed_data["raw_text"] = resume_text
    
    return {
        "success": True,
        "error": None,
        "data": parsed_data
    }
