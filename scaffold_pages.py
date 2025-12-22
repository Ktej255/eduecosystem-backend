import os

# Base path for frontend app directory
BASE_PATH = r"d:\Graphology\Master Software\Eduecosystem\frontend\src\app\(dashboard)"

# List of routes to scaffold based on sidebar.tsx
# Format: (path, title, description)
ROUTES = [
    # AI Avatars
    ("ai-avatars", "AI Avatars", "Create and manage your AI avatars"),
    
    # Products
    ("lms/webinars", "Webinars", "Host and manage your webinars"),
    ("lms/digital-products", "Digital Products", "Manage your digital downloads and assets"),
    ("lms/telegram", "Telegram Communities", "Manage your Telegram community integrations"),
    
    # Manage
    ("manage/assets", "Asset Library", "Manage your media assets and files"),
    ("lms/discussions", "Discussions", "Moderate and participate in course discussions"),
    ("lms/questions", "Question Bank", "Create and manage quiz questions"),
    ("lms/quiz-reviews", "Quiz Reviews", "Review student quiz submissions"),
    ("lms/assignments", "Assignments", "Manage and grade student assignments"),
    ("lms/live-tests", "Live Tests", "Schedule and manage live tests"),
    ("lms/live-classes", "Live Classes", "Schedule and manage live sessions"),
    ("lms/reviews", "Ratings & Reviews", "View and respond to course reviews"),
    
    # Community
    ("community", "Community", "Engage with your student community"),
    
    # Users
    ("users/learners", "Learners", "Manage your student base"),
    ("users/admins", "Admins", "Manage administrative access"),
    ("users/instructors", "Instructors", "Manage course instructors"),
    ("users/affiliates", "Affiliates", "Manage your affiliate program"),
    ("users/enquiries", "Enquiries", "View and respond to user enquiries"),
    
    # Reports
    ("reports/overview", "Reports Overview", "View key performance metrics"),
    ("reports/transactions", "Transactions", "View financial transactions"),
    ("reports/settlements", "Settlements", "Manage payouts and settlements"),
    ("reports/webinars", "Webinar Reports", "View webinar attendance and analytics"),
    ("reports/traffic", "Traffic Analytics", "Analyze visitor traffic and sources"),
    
    # Website
    ("website/pages", "Website Pages", "Manage your website content pages"),
    ("website/builder", "Website Builder", "Customize your website appearance"),
    
    # Mobile App
    ("mobile-app/builder", "App Builder", "Customize your mobile app"),
    ("mobile-app/config", "App Configuration", "Configure mobile app settings"),
    ("mobile-app/history", "Build History", "View app build history"),
    
    # Marketing
    ("marketing/campaigns", "Campaigns", "Manage marketing campaigns"),
    ("marketing/messenger", "Messenger", "Manage direct messages"),
    ("marketing/blogs", "Blogs", "Manage your blog posts"),
    ("marketing/announcements", "Announcements", "Create and manage announcements"),
    ("marketing/wallet", "Wallet", "Manage marketing budget and wallet"),
    ("marketing/promo-codes", "Promo Codes", "Create and manage discount codes"),
    ("marketing/referrals", "Referrals", "Manage referral program settings"),
    ("marketing/affiliates", "Affiliate Marketing", "Manage affiliate marketing campaigns"),
    
    # AI Social Media
    ("social-media/linkedin", "LinkedIn", "Manage LinkedIn integration"),
    ("social-media/telegram", "Telegram Social", "Manage Telegram social features"),
    ("social-media/facebook", "Facebook", "Manage Facebook integration"),
    ("social-media/instagram", "Instagram", "Manage Instagram integration"),
    ("social-media/youtube", "YouTube", "Manage YouTube integration"),
    ("social-media/twitter", "X (Twitter)", "Manage X (Twitter) integration"),
    
    # Integrations
    ("integrations/third-party", "Third Party Integrations", "Manage external tool integrations"),
    ("integrations/apis", "API Access", "Manage API keys and access"),
    ("integrations/webhooks", "Webhooks", "Configure and manage webhooks"),
    ("integrations/logs", "Integration Logs", "View integration activity logs"),
    
    # Settings
    ("settings/domain", "Domain Management", "Configure your custom domain"),
    ("settings/payments", "Payment Settings", "Configure payment gateways"),
    ("settings/tax", "Tax & Invoicing", "Manage tax settings and invoices"),
    ("settings/security", "Security Settings", "Configure security preferences"),
    ("settings/communications", "Communications", "Manage email and notification settings"),
    ("settings/custom-fields", "Custom Fields", "Manage custom user fields"),
    ("settings/ux", "User Experience", "Customize the user interface"),
    ("settings/auth", "Signup & Login", "Configure authentication settings"),
]

def create_page(path, title, description):
    full_dir_path = os.path.join(BASE_PATH, path.replace("/", os.sep))
    os.makedirs(full_dir_path, exist_ok=True)
    
    file_path = os.path.join(full_dir_path, "page.tsx")
    
    # Don't overwrite existing files (rudimentary check)
    if os.path.exists(file_path):
        print(f"Skipping existing file: {file_path}")
        return

    content = f"""import GenericPage from "@/components/scaffold/GenericPage";

export default function Page() {{
  return (
    <GenericPage 
      title="{title}" 
      description="{description}" 
    />
  );
}}
"""
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"Created: {file_path}")

def main():
    print(f"Scaffolding pages in {BASE_PATH}...")
    for path, title, description in ROUTES:
        create_page(path, title, description)
    print("Done!")

if __name__ == "__main__":
    main()
