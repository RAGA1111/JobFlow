import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Check if GROQ_API_KEY is present
if not os.environ.get("GROQ_API_KEY"):
    print("WARNING: GROQ_API_KEY not found in environment variables. Please add it to your .env file.")

# Time Block 1 (0:00-0:15) - Initialize Groq client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Time Block 2 (0:15-1:00) - Profile Parser
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

# Time Block 3 (1:00-1:40) - Job Scorer
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

# Time Block 4 (1:40-2:10) - Cover Letter Generator
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

if __name__ == "__main__":
    # Test Block 1 API call
    print("Testing basic Groq inference...")
    try:
        test_resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "Hello, simply reply 'API OK'"}]
        )
        print("Response:", test_resp.choices[0].message.content)
    except Exception as e:
        print("Groq API error:", e)
