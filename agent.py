"""
AI Agent module - Groq LLM integration for job processing.

This module contains:
- Groq client initialization
- Profile parsing
- Job scoring
- Cover letter generation
- Auto-apply workflow
- Job suggestions
"""
import os
import json
from typing import List, Dict, Any, Optional
import asyncio

from groq import Groq
from dotenv import load_dotenv

# Import tracker models
from tracker import User, store_application
from config import settings

load_dotenv()

# Check if GROQ_API_KEY is present
if not os.environ.get("GROQ_API_KEY"):
    print("WARNING: GROQ_API_KEY not found in environment variables. Please add it to your .env file.")

# Initialize Groq client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


def parse_user_profile(raw_message: str, resume_text: str = "") -> dict:
    """Parses WhatsApp message + Resume text into structured JSON profile."""
    prompt = f"""
    Extract the following information from the user's message and resume into a JSON object:
    - role: (string) the job role they want
    - location: (string) their target location
    - years_of_experience: (number) years of experience
    - skills: (list of strings) key technical skills
    - salary_range: (string) expected salary range

    User Message: {raw_message}
    Resume Text: {resume_text}

    Return ONLY a valid JSON object matching the requested schema. No other text.
    """
    
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are an expert HR data parser. Output JSON only."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )
    
    return json.loads(response.choices[0].message.content)


def score_job_fit(job: dict, profile: dict) -> dict:
    """Scores a job out of 100 based on the user's profile and returns a JSON dict with score and reason."""
    prompt = f"""
    Score the fit of the candidate for the following job on a scale of 0-100 based on skill overlap, experience match, location, and salary alignment.
    Provide a concise, one-line reasoning.
    
    Profile: {json.dumps(profile)}
    Job (Title, Company, Salary, Location): {json.dumps(job)}
    
    Return ONLY a JSON object with 'score' (integer between 0-100) and 'reason' (string description).
    """
    
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a senior technical recruiter rating candidates. Output JSON only."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )
    
    return json.loads(response.choices[0].message.content)


def generate_cover_letter(job: dict, profile: dict) -> str:
    """Generates a <200 word cover letter tailored strictly to the matched job."""
    prompt = f"""
    Write a short (maximum 150-200 words) professional cover letter for the following job using the candidate's profile.
    It must reference the specific job title ({job.get('title')}), company name ({job.get('company')}), and 2-3 specific matched skills from the profile.
    It should be recruiter-ready and highly personalized.
    
    Candidate Profile: {json.dumps(profile)}
    Job Data: {json.dumps(job)}
    
    Return ONLY the raw cover letter text.
    """
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are an expert career coach writing hyper-personalized, concise cover letters. Do not use filler."},
            {"role": "user", "content": prompt}
        ]
    )
    
    return response.choices[0].message.content.strip()


async def run_auto_apply(phone: str, user: User) -> Dict[str, Any]:
    """
    Run the auto-apply workflow for a user.
    
    Args:
        phone: User's phone number
        user: User object with profile information
    
    Returns:
        Dictionary with application results
    """
    print(f"Running auto-apply for {phone}")
    print(f"User: {user.name}, Role: {user.role}, Location: {user.location}")
    
    # TODO: Implement full auto-apply workflow
    # 1. Scrape jobs from Naukri and Indeed
    # 2. Score each job against user profile
    # 3. Generate cover letters for high-scoring jobs
    # 4. Apply to each job using Playwright
    # 5. Store application results in database
    
    return {
        "total": 0,
        "applied": 0,
        "failed": 0,
        "skipped": 0,
        "captcha_blocked": 0,
        "applications": []
    }


async def get_job_suggestions(
    role: str,
    location: str,
    salary_range: Optional[str] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Get job suggestions for immediate response.
    
    Args:
        role: Job role to search for
        location: Job location
        salary_range: Optional salary range filter
        limit: Maximum number of jobs to return
    
    Returns:
        List of job dictionaries
    """
    print(f"Getting job suggestions for {role} in {location}")
    
    # TODO: Implement job scraping and return results
    
    return []


# Tool definitions for Groq agent
TOOLS = [
    {
        "name": "parse_user_profile",
        "description": "Parse user profile from text message",
        "parameters": {
            "raw_message": "string",
            "resume_text": "string"
        }
    },
    {
        "name": "search_jobs",
        "description": "Search for jobs on job boards",
        "parameters": {
            "role": "string",
            "location": "string",
            "experience": "integer",
            "skills": "array"
        }
    },
    {
        "name": "score_job_fit",
        "description": "Score how well a job matches user profile",
        "parameters": {
            "job": "object",
            "profile": "object"
        }
    },
    {
        "name": "generate_cover_letter",
        "description": "Generate tailored cover letter for a job",
        "parameters": {
            "job": "object",
            "profile": "object"
        }
    },
    {
        "name": "apply_to_job",
        "description": "Apply to a job using Playwright",
        "parameters": {
            "job_url": "string",
            "profile": "object",
            "cover_letter": "string"
        }
    }
]


if __name__ == "__main__":
    # Test Groq API
    print("Testing Groq API...")
    try:
        test_resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "Hello, simply reply 'API OK'"}]
        )
        print("Response:", test_resp.choices[0].message.content)
    except Exception as e:
        print("Groq API error:", e)
