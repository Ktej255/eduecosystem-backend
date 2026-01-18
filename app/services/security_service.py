import math
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.activity_log import ActivityLog
from app.models.security import GhostLoginAlert
from app.models.user import User

class SecurityService:
    @staticmethod
    def check_ghost_login(db: Session, user: User, current_ip: str):
        """
        Check for 'impossible travel' - concurrent logins from distant locations.
        """
        # 1. Get recent logins for this user in the last hour
        hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_logins = db.query(ActivityLog).filter(
            ActivityLog.user_id == user.id,
            ActivityLog.action == "login",
            ActivityLog.timestamp >= hour_ago,
            ActivityLog.ip_address != current_ip
        ).order_by(ActivityLog.timestamp.desc()).all()
        
        if not recent_logins:
            return None
            
        previous_login = recent_logins[0]
        
        # 2. In a real system, we'd use a GeoIP library (e.g., GeoLite2) to get lat/long.
        # For this implementation, we'll simulate the detection logic.
        
        # Simulation: If IPs have different network prefixes, assume high risk for now
        # (This is a simplified placeholders for GeoIP distance calculation)
        ip_a_prefix = ".".join(previous_login.ip_address.split(".")[:2])
        ip_b_prefix = ".".join(current_ip.split(".")[:2])
        
        if ip_a_prefix != ip_b_prefix:
            # FLAG: Distant logins within 1 hour
            time_diff = (datetime.utcnow() - previous_login.timestamp).total_seconds() / 60
            
            alert = GhostLoginAlert(
                user_id=user.id,
                login_a_ip=previous_login.ip_address,
                login_a_time=previous_login.timestamp,
                login_b_ip=current_ip,
                login_b_time=datetime.utcnow(),
                estimated_distance_km=500.0, # Simulated
                time_difference_minutes=time_diff,
                risk_score=8
            )
            db.add(alert)
            db.commit()
            return alert
            
        return None

    @staticmethod
    def get_active_alerts(db: Session, limit: int = 50):
        return db.query(GhostLoginAlert).filter(
            GhostLoginAlert.is_resolved == False
        ).order_by(GhostLoginAlert.created_at.desc()).limit(limit).all()

security_service = SecurityService()
