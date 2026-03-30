"""FastAPI server for WhatsApp Job Agent."""
import os
import uuid
from typing import Optional
from pathlib import Path

from fastapi import FastAPI, Form, Request, BackgroundTasks
from fastapi.responses import PlainTextResponse
import uvicorn

from config import settings, DATA_DIR
from tracker import (
    create_user, get_user_by_phone, update_user_profile,
    store_application, get_application_status_summary
)
from whatsapp import (
    send_message, download_media, format_welcome_message,
    format_resume_received, format_job_summary, format_application_summary,
    format_auto_apply_start, format_auto_apply_complete
)
from resume_parser import process_resume, parse_user_preferences, parse_job_suggestion_query

# Initialize FastAPI app
app = FastAPI(title="WhatsApp Job Agent", version="1.0.0")

# Store for pending operations (in production, use Redis)
pending_operations = {}


@app.get("/health")
async def health_check():
    """Health check endpoint for Railway."""
    return {"status": "healthy", "version": "1.0.0"}


@app.post("/webhook")
async def webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    From: str = Form(...),
    Body: str = Form(default=""),
    NumMedia: int = Form(default=0),
    MediaUrl0: Optional[str] = Form(default=None),
    MediaContentType0: Optional[str] = Form(default=None)
):
    """
    Handle incoming WhatsApp messages from Twilio.
    
    Supports:
    - Resume PDF upload (first interaction)
    - Job preferences text (triggers auto-apply)
    - Job suggestion queries (e.g., "jobs in Chennai for Python developer")
    - STATUS command (check application status)
    """
    phone = From
    message = Body.strip()
    
    print(f"Received message from {phone}: {message[:100]}...")
    
    # Check if user exists
    user = get_user_by_phone(phone)
    
    # Handle media upload (resume PDF)
    if NumMedia > 0 and MediaUrl0 and MediaContentType0 == "application/pdf":
        return await handle_resume_upload(phone, MediaUrl0)
    
    # Handle text messages
    if not user:
        # New user - ask for resume
        welcome_msg = format_welcome_message()
        send_message(phone, welcome_msg)
        return PlainTextResponse("")
    
    # Check for specific commands
    message_upper = message.upper()
    
    if message_upper == "STATUS":
        return await handle_status_check(phone)
    
    if message_upper in ["HI", "HELLO", "START", "HELP"]:
        welcome_msg = format_welcome_message()
        send_message(phone, welcome_msg)
        return PlainTextResponse("")
    
    # Check if this is a job suggestion query
    if is_job_suggestion_query(message):
        return await handle_job_suggestions(phone, message)
    
    # Check if user has resume
    if not user.resume_text:
        # Ask for resume first
        msg = "Please send your resume PDF first so I can understand your profile better."
        send_message(phone, msg)
        return PlainTextResponse("")
    
    # Check if user has preferences set
    if not user.role:
        # This is likely a preferences message
        return await handle_preferences(phone, message, user.resume_text)
    
    # User has resume and preferences - trigger auto-apply
    return await handle_auto_apply(phone, user)


async def handle_resume_upload(phone: str, media_url: str) -> PlainTextResponse:
    """Handle resume PDF upload."""
    print(f"Processing resume upload from {phone}")
    
    # Download PDF
    resume_path = DATA_DIR / f"resume_{phone.replace('+', '')}.pdf"
    
    if not download_media(media_url, str(resume_path)):
        send_message(phone, "Sorry, I couldn't download your resume. Please try again.")
        return PlainTextResponse("")
    
    # Process resume
    result = process_resume(str(resume_path))
    
    if not result["success"]:
        send_message(phone, f"Error processing resume: {result['error']}")
        return PlainTextResponse("")
    
    # Extract data
    resume_data = result["data"]
    
    # Create or update user
    user = get_user_by_phone(phone)
    if not user:
        create_user(
            phone=phone,
            name=resume_data.get("name"),
            email=resume_data.get("email")
        )
    
    # Update with resume info
    update_user_profile(
        phone=phone,
        resume_text=resume_data.get("raw_text", ""),
        skills=", ".join(resume_data.get("skills", [])) if resume_data.get("skills") else None,
        years_experience=resume_data.get("experience_years")
    )
    
    # Send confirmation
    msg = format_resume_received()
    if resume_data.get("name"):
        msg = f"Hello {resume_data['name']}!\n\n" + msg
    
    send_message(phone, msg)
    return PlainTextResponse("")


async def handle_preferences(phone: str, message: str, resume_text: str) -> PlainTextResponse:
    """Handle user preferences message."""
    print(f"Processing preferences from {phone}")
    
    # Parse preferences
    user = get_user_by_phone(phone)
    resume_skills = user.skills.split(", ") if user and user.skills else []
    
    preferences = parse_user_preferences(message, resume_skills)
    
    # Update user profile
    update_user_profile(
        phone=phone,
        role=preferences.get("role"),
        location=preferences.get("location"),
        years_experience=preferences.get("years_experience"),
        skills=", ".join(preferences.get("skills", [])) if preferences.get("skills") else None,
        salary_range=preferences.get("salary_range")
    )
    
    # Confirm and trigger auto-apply
    role = preferences.get("role", "your target role")
    location = preferences.get("location", "your preferred location")
    
    confirm_msg = (
        f"Got it! I'll search for *{role}* roles in *{location}*\n\n"
        f"I'll apply to the best matches and update you shortly..."
    )
    send_message(phone, confirm_msg)
    
    # Trigger auto-apply in background
    # This will call the agent module (implemented by Member 2)
    try:
        from agent import run_auto_apply
        user = get_user_by_phone(phone)
        result = await run_auto_apply(phone, user)
        
        # Send completion message
        completion_msg = format_auto_apply_complete(result)
        send_message(phone, completion_msg)
        
    except ImportError:
        # Agent module not yet implemented
        send_message(phone, "Auto-apply feature coming soon! Your preferences have been saved.")
    except Exception as e:
        print(f"Error in auto-apply: {e}")
        send_message(phone, "Sorry, there was an error processing your request. Please try again.")
    
    return PlainTextResponse("")


async def handle_auto_apply(phone: str, user) -> PlainTextResponse:
    """Handle auto-apply workflow."""
    print(f"Triggering auto-apply for {phone}")
    
    # Send starting message
    profile = {
        "role": user.role,
        "location": user.location
    }
    start_msg = format_auto_apply_start(profile)
    send_message(phone, start_msg)
    
    # Run auto-apply
    try:
        from agent import run_auto_apply
        result = await run_auto_apply(phone, user)
        
        # Send completion message
        completion_msg = format_auto_apply_complete(result)
        send_message(phone, completion_msg)
        
    except ImportError:
        send_message(phone, "Auto-apply feature coming soon!")
    except Exception as e:
        print(f"Error in auto-apply: {e}")
        send_message(phone, "Sorry, there was an error. Please try again later.")
    
    return PlainTextResponse("")


async def handle_job_suggestions(phone: str, message: str) -> PlainTextResponse:
    """Handle job suggestion query."""
    print(f"Processing job suggestion query from {phone}: {message}")
    
    # Parse query
    query_data = parse_job_suggestion_query(message)
    
    role = query_data.get("role")
    location = query_data.get("location")
    
    if not role or not location:
        send_message(phone, "Please specify both role and location. Example: 'Find jobs in Chennai for Python developer'")
        return PlainTextResponse("")
    
    # Send searching message
    send_message(phone, f"Searching for *{role}* jobs in *{location}*...")
    
    # Search jobs
    try:
        from agent import get_job_suggestions
        jobs = await get_job_suggestions(role, location, limit=10)
        
        # Format and send results
        if jobs:
            msg = format_job_summary(jobs)
        else:
            msg = f"Sorry, no jobs found for *{role}* in *{location}*. Try different keywords."
        
        send_message(phone, msg)
        
    except ImportError:
        send_message(phone, "Job search feature coming soon!")
    except Exception as e:
        print(f"Error in job suggestions: {e}")
        send_message(phone, "Sorry, there was an error searching for jobs. Please try again.")
    
    return PlainTextResponse("")


async def handle_status_check(phone: str) -> PlainTextResponse:
    """Handle STATUS command."""
    print(f"Processing status check for {phone}")
    
    summary = get_application_status_summary(phone)
    
    if summary["total"] == 0:
        msg = "You haven't applied to any jobs yet. Send your resume and preferences to get started!"
    else:
        msg = format_application_summary(summary["recent"])
    
    send_message(phone, msg)
    return PlainTextResponse("")


def is_job_suggestion_query(message: str) -> bool:
    """Check if message is a job suggestion query."""
    message_lower = message.lower()
    
    # Keywords that indicate a job suggestion query
    suggestion_keywords = [
        "find jobs", "search jobs", "show jobs", "send jobs",
        "job in", "jobs in", "looking for", "suggest jobs",
        "recommend jobs", "any jobs", "available jobs"
    ]
    
    return any(keyword in message_lower for keyword in suggestion_keywords)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "WhatsApp Job Agent API",
        "version": "1.0.0",
        "endpoints": {
            "webhook": "/webhook (POST)",
            "health": "/health (GET)"
        }
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
