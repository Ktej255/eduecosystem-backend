"""
Seed 5 Organization Domains for Multi-Tenancy Testing
Run with: python scripts/seed_organizations.py
"""

import sys
import os

# Add backend root to path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

from dotenv import load_dotenv
load_dotenv()

from app.db.session import SessionLocal
from app.models.sso import Organization

ORGANIZATIONS = [
    {
        "name": "Graphology India",
        "domain": "graphologyindia.com",
        "slug": "graphology-india",
        "logo_url": "https://example.com/logo1.png",
        "theme_config": {"primary_color": "#FF5722", "font": "Poppins"},
        "hero_text": "Master Your Mind Through Handwriting"
    },
    {
        "name": "RAS Academy",
        "domain": "rasacademy.in",
        "slug": "ras-academy",
        "logo_url": "https://example.com/logo2.png",
        "theme_config": {"primary_color": "#2196F3", "font": "Inter"},
        "hero_text": "Your Gateway to RAS Success"
    },
    {
        "name": "UPSC Mastery",
        "domain": "upscmastery.com",
        "slug": "upsc-mastery",
        "logo_url": "https://example.com/logo3.png",
        "theme_config": {"primary_color": "#4CAF50", "font": "Roboto"},
        "hero_text": "Crack UPSC with AI-Powered Learning"
    },
    {
        "name": "Wellness Hub",
        "domain": "wellnesshub.in",
        "slug": "wellness-hub",
        "logo_url": "https://example.com/logo4.png",
        "theme_config": {"primary_color": "#9C27B0", "font": "DM Sans"},
        "hero_text": "Holistic Wellness for Modern Life"
    },
    {
        "name": "Mind Transform",
        "domain": "mindtransform.co",
        "slug": "mind-transform",
        "logo_url": "https://example.com/logo5.png",
        "theme_config": {"primary_color": "#673AB7", "font": "Outfit"},
        "hero_text": "Rewire Your Brain, Transform Your Life"
    }
]

def seed():
    db = SessionLocal()
    try:
        for org_data in ORGANIZATIONS:
            existing = db.query(Organization).filter(Organization.slug == org_data["slug"]).first()
            if existing:
                print(f"Skipping {org_data['name']} (already exists)")
                continue
            
            org = Organization(
                name=org_data["name"],
                domain=org_data["domain"],
                slug=org_data["slug"],
                logo_url=org_data["logo_url"],
                theme_config=org_data["theme_config"],
                hero_text=org_data["hero_text"],
                is_active=True
            )
            db.add(org)
            print(f"Added: {org_data['name']}")
        
        db.commit()
        print("\n✅ Done! 5 organizations seeded.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
