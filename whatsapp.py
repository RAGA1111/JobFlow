"""WhatsApp integration using Twilio."""
import os
from typing import Optional
from pathlib import Path

import httpx
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from config import settings

# Initialize Twilio client
twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


def send_message(to_phone: str, message: str) -> bool:
    """Send WhatsApp message via Twilio."""
    try:
        # Ensure phone number is in E.164 format with whatsapp: prefix
        if not to_phone.startswith("whatsapp:"):
            to_phone = f"whatsapp:{to_phone}"
        
        message = twilio_client.messages.create(
            from_=settings.TWILIO_WHATSAPP_NUMBER,
            body=message,
            to=to_phone
        )
        
        print(f"Message sent: {message.sid}")
        return True
        
    except TwilioRestException as e:
        print(f"Twilio error sending message: {e}")
        return False
    except Exception as e:
        print(f"Error sending message: {e}")
        return False


def download_media(media_url: str, save_path: str) -> bool:
    """Download media from Twilio URL."""
    try:
        # Twilio media URLs require authentication
        response = httpx.get(
            media_url,
            auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN),
            follow_redirects=True,
            timeout=30.0
        )
        
        if response.status_code == 200:
            # Ensure directory exists
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(save_path, "wb") as f:
                f.write(response.content)
            
            print(f"Media downloaded to: {save_path}")
            return True
        else:
            print(f"Failed to download media: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Error downloading media: {e}")
        return False


def format_job_summary(jobs: list) -> str:
    """Format job list for WhatsApp message."""
    if not jobs:
        return "No jobs found matching your criteria."
    
    message = f"Found {len(jobs)} jobs for you:\n\n"
    
    for i, job in enumerate(jobs[:10], 1):  # Limit to 10 jobs
        title = job.get("title", "Unknown Title")
        company = job.get("company", "Unknown Company")
        location = job.get("location", "Not specified")
        salary = job.get("salary", "Not disclosed")
        url = job.get("apply_url", "")
        
        message += f"*{i}. {title}*\n"
        message += f"Company: {company}\n"
        message += f"Location: {location}\n"
        if salary and salary != "Not disclosed":
            message += f"Salary: {salary}\n"
        if url:
            message += f"Apply: {url}\n"
        message += "\n"
    
    if len(jobs) > 10:
        message += f"... and {len(jobs) - 10} more jobs.\n"
    
    return message


def format_application_summary(applications: list) -> str:
    """Format application status for WhatsApp message."""
    if not applications:
        return "You haven't applied to any jobs yet."
    
    message = f"Your application status ({len(applications)} total):\n\n"
    
    # Group by status
    status_counts = {}
    for app in applications:
        status = app.get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
    
    message += "Summary:\n"
    for status, count in status_counts.items():
        emoji = {
            "applied": "✅",
            "failed": "❌",
            "skipped": "⏭️",
            "captcha_blocked": "🤖"
        }.get(status, "❓")
        message += f"{emoji} {status.replace('_', ' ').title()}: {count}\n"
    
    message += "\nRecent applications:\n"
    for i, app in enumerate(applications[:5], 1):
        company = app.get("company", "Unknown")
        title = app.get("job_title", "Unknown")
        status = app.get("status", "unknown")
        score = app.get("fit_score", "N/A")
        
        emoji = {
            "applied": "✅",
            "failed": "❌",
            "skipped": "⏭️",
            "captcha_blocked": "🤖"
        }.get(status, "❓")
        
        message += f"{i}. {emoji} {company} - {title} (Score: {score})\n"
    
    return message


def format_auto_apply_start(profile: dict) -> str:
    """Format message for auto-apply start."""
    role = profile.get("role", "your target role")
    location = profile.get("location", "your preferred location")
    
    return (
        f"🚀 Starting auto-apply process!\n\n"
        f"Looking for: *{role}* in *{location}*\n"
        f"I'll search job boards, score matches, and apply to the best fits.\n\n"
        f"This may take a few minutes. I'll update you when complete!"
    )


def format_auto_apply_complete(results: dict) -> str:
    """Format message for auto-apply completion."""
    total = results.get("total", 0)
    applied = results.get("applied", 0)
    failed = results.get("failed", 0)
    skipped = results.get("skipped", 0)
    captcha = results.get("captcha_blocked", 0)
    
    message = (
        f"✅ Auto-apply complete!\n\n"
        f"Results:\n"
        f"✅ Applied: {applied}\n"
        f"❌ Failed: {failed}\n"
        f"⏭️ Skipped: {skipped}\n"
        f"🤖 CAPTCHA blocked: {captcha}\n"
        f"Total processed: {total}\n\n"
    )
    
    applications = results.get("applications", [])
    if applications:
        message += "Applied to:\n"
        for app in applications[:5]:
            company = app.get("company", "Unknown")
            title = app.get("job_title", "Unknown")
            score = app.get("fit_score", "N/A")
            message += f"• {company} - {title} (Score: {score})\n"
        
        if len(applications) > 5:
            message += f"... and {len(applications) - 5} more\n"
    
    message += "\nReply STATUS anytime to check your application status."
    
    return message


def format_welcome_message() -> str:
    """Format welcome message for new users."""
    return (
        "👋 Welcome to AI Job Agent!\n\n"
        "I can help you:\n"
        "1️⃣ *Auto-apply* to jobs - Send your resume and preferences\n"
        "2️⃣ *Get job suggestions* - Ask 'Find jobs in [location] for [role]'\n"
        "3️⃣ *Track applications* - Reply STATUS anytime\n\n"
        "To get started, please send your resume PDF."
    )


def format_resume_received() -> str:
    """Format message after receiving resume."""
    return (
        "📄 Resume received!\n\n"
        "Now tell me your job preferences:\n"
        "• Target role (e.g., ML Engineer)\n"
        "• Preferred location (e.g., Chennai)\n"
        "• Years of experience\n"
        "• Key skills\n"
        "• Expected salary range (e.g., 10-15 LPA)\n\n"
        "Or simply ask for job suggestions like:\n"
        "'Send jobs in Coimbatore for full stack developer 10-15 LPA'"
    )
