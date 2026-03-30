import asyncio
import json
from scraper import search_jobs
from agent import parse_user_profile, score_job_fit, generate_cover_letter

# Time Block 6 (2:40-3:00) Connect Scraper -> Scorer -> Cover Letter Generator
async def run_pipeline():
    user_msg = "ML Engineer jobs in Chennai, 2 years experience, Python TensorFlow Scikit-learn, 14-20 LPA"
    print("--- Phase 1: Parse Profile ---")
    profile = parse_user_profile(user_msg)
    print("Parsed Profile:", json.dumps(profile, indent=2))
    
    role = profile.get("role", "ML Engineer")
    location = profile.get("location", "Chennai")
    
    print(f"\n--- Phase 2: Scrape Jobs for '{role}' in '{location}' ---")
    # For testing, we just scrape 1 page to save time
    jobs = await search_jobs(role, location, pages=1)
    print(f"Found {len(jobs)} total jobs raw.")
    
    if not jobs:
        print("Using sample jobs as fallback.")
        jobs = [
            {"title": "Machine Learning Engineer", "company": "Zoho", "salary": "15-20 LPA", "location": "Chennai", "url": "http://naukri.com/mock-1", "board": "Naukri"},
            {"title": "Data Scientist", "company": "Freshworks", "salary": "12-18 LPA", "location": "Chennai", "url": "http://naukri.com/mock-2", "board": "Naukri"},
            {"title": "AI Analyst", "company": "HDFC", "salary": "8-12 LPA", "location": "Chennai", "url": "http://naukri.com/mock-3", "board": "Naukri"}
        ]

    print("\n--- Phase 3: Score and Generate ---")
    ranked_applications = []
    
    for job in jobs[:5]: # Take top 5 to test
        print(f"\nEvaluating: {job['title']} at {job['company']}")
        fit = score_job_fit(job, profile)
        print(f"Fit Score: {fit.get('score')} | Reason: {fit.get('reason')}")
        
        if fit.get('score', 0) >= 70:
            print("Score >= 70. Generating Cover Letter...")
            cl = generate_cover_letter(job, profile)
            # Just print the first 50 chars as preview
            print(f"Cover Letter snippet: {cl[:50]}...")
            
            job_app = {**job, "score": fit.get("score"), "cover_letter": cl}
            ranked_applications.append(job_app)
        else:
            print("Score < 70. Skipping.")
            
    print(f"\nPipeline Complete. {len(ranked_applications)} applications ready to submit.")

if __name__ == "__main__":
    try:
        asyncio.run(run_pipeline())
    except Exception as e:
        print("Pipeline errored:", e)
