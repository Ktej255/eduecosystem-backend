from app.db.session import engine
from sqlalchemy import text


def drop_tables():
    tables = [
        "platform_analytics",
        "subscription_coupons",
        "subscription_plans",
        "affiliate_partners",
        "instructor_payment_info",
        "instructor_payouts",
        "user_subscriptions",
        "affiliate_clicks",
        "affiliate_payouts",
        "affiliate_referrals",
        "analytics_events",
        "instructor_analytics",
        "marketplace_listings",
        "revenue_shares",
        "revenue_transactions",
        "student_analytics",
        "subscription_invoices",
        "affiliate_commissions",
    ]

    with engine.connect() as connection:
        for table in tables:
            try:
                print(f"Dropping table {table}...")
                connection.execute(text(f"DROP TABLE IF EXISTS {table}"))
                print(f"Dropped {table}")
            except Exception as e:
                print(f"Error dropping {table}: {e}")
        connection.commit()


if __name__ == "__main__":
    drop_tables()
