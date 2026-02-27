from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import extract
from app.models.lead import Lead
from app.core.email import send_email

# Email templates for the 5-day drip sequence
DRIP_EMAILS = {
    1: {
        "subject": "Day 1: Welcome to Eduecosystem",
        "template": "drip_template.html",
        "body": "Thank you for showing interest in Eduecosystem. We are excited to guide you on a holistic journey.",
    },
    2: {
        "subject": "Day 2: Mastering Your Potential",
        "template": "drip_template.html",
        "body": "Did you know that scientific meditation combined with Vedic knowledge can increase your focus by 40%?",
    },
    3: {
        "subject": "Day 3: The Power of Graphotherapy",
        "template": "drip_template.html",
        "body": "Reprogram your subconscious mind. Change your handwriting, change your life with Graphotherapy.",
    },
    4: {
        "subject": "Day 4: Ancient Wisdom Meets Modern Tech",
        "template": "drip_template.html",
        "body": "Explore Upanishads, Sanskrit, and Vedic Math through our interactive self-learning modules.",
    },
    5: {
        "subject": "Day 5: Your Next Steps",
        "template": "drip_template.html",
        "body": "Ready to dive in? Enroll today and unlock unlimited access to the holistic learning ecosystem.",
    }
}

async def process_email_drips(db: Session):
    """
    Scans the leads database and dispatches emails based on the gap between
    the lead's creation time and the current time.
    """
    now = datetime.now(timezone.utc)
    
    # We want to process leads who haven't received all 5 emails.
    eligible_leads = db.query(Lead).filter(Lead.drip_day_sent < 5).all()
    
    processed_count = 0
    
    for lead in eligible_leads:
        # Calculate how many full days have passed since creation
        if not lead.created_at:
            continue
            
        # Ensure timezone awareness for comparison
        created_at = lead.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
            
        delta = now - created_at
        days_passed = delta.days
        
        # If the number of days passed is greater than the last email sent,
        # we can send the next email in sequence. 
        # e.g., days_passed = 1, drip_day_sent = 0 -> send Day 1 email
        # To avoid bombarding, we only send ONE email per cron execution per lead,
        # incrementing carefully.
        
        target_email_day = lead.drip_day_sent + 1
        
        # We only send if enough days have actually passed
        if days_passed >= target_email_day and target_email_day <= 5:
            email_data = DRIP_EMAILS.get(target_email_day)
            
            if email_data and lead.email:
                try:
                    await send_email(
                        email_to=lead.email,
                        subject=email_data["subject"],
                        template_name=email_data["template"], # FastMail looks for this in templates folder
                        template_body={"name": lead.name, "body": email_data["body"]}
                    )
                    
                    # Success: increment the tracking
                    lead.drip_day_sent = target_email_day
                    db.add(lead)
                    processed_count += 1
                except Exception as e:
                    print(f"Failed to send drip email day {target_email_day} to {lead.email}: {e}")
                    
    db.commit()
    return {"status": "success", "emails_dispatched": processed_count}
