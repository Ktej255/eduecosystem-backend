import subprocess
import os
import re
from datetime import datetime
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.models.development_history import DevelopmentLog

class GitSyncService:
    """
    Synchronizes Git commit history into the DevelopmentLog database.
    Useful for automating development tracking.
    """
    
    def __init__(self, repo_path: str = None):
        # Default to the parent directory of backend (the root of Eduecosystem)
        if repo_path is None:
            # backend/app/services/git_sync_service.py -> backend -> root
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.repo_path = os.path.abspath(os.path.join(current_dir, "../../../"))
        else:
            self.repo_path = repo_path

    def fetch_recent_commits(self, limit: int = 50) -> List[Dict[str, str]]:
        """
        Fetches the recent commits using `git log`.
        """
        try:
            # We use a custom format to easily parse: Hash|Date|Subject|Body|Author
            # %H = commit hash, %cd = commit date (short), %s = subject, %b = body, %an = author name
            git_format = "%H|%cd|%s|%b|%an"
            cmd = [
                "git",
                "log",
                f"-n {limit}",
                f"--date=short",
                f"--pretty=format:{git_format}",
                "--no-merges"
            ]
            
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            commits = []
            # Git log separates entries with double newlines if body exists, but we can split by lines
            # Actually --pretty=format puts each commit on one logical line unless body has newlines.
            # To handle body newlines safely, let's use a unique delimiter.
            
            delim = "||_SYNC_DELIM_||"
            cmd_safe = [
                "git",
                "log",
                f"-n {limit}",
                f"--date=short",
                f"--pretty=format:%H|%cd|%s|%an{delim}%b",
                "--no-merges"
            ]
            
            result_safe = subprocess.run(
                cmd_safe,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            raw_commits = result_safe.stdout.strip().split("\n\n")
            
            for raw in result_safe.stdout.split(f"\n"):
                if not raw.strip():
                    continue
                # Split the line
                parts = raw.split(delim)
                if len(parts) != 2: continue
                
                header = parts[0]
                body = parts[1].strip()
                
                header_parts = header.split("|")
                if len(header_parts) != 4: continue
                
                commit_hash, date_str, subject, author = header_parts
                
                commits.append({
                    "hash": commit_hash,
                    "date": date_str,
                    "subject": subject.strip(),
                    "body": body,
                    "author": author.strip()
                })
                
            return commits
            
        except subprocess.CalledProcessError as e:
            print(f"GitSyncService Error: Subprocess failed. {e.stderr}")
            return []
        except Exception as e:
            print(f"GitSyncService Error: {e}")
            return []

    def parse_commit_to_log_data(self, commit: Dict[str, str]) -> Dict[str, Any]:
        """
        Parses a commit message to extract structured info for DevelopmentLog.
        Focuses on Conventional Commits format (feat, fix, docs, refactor, etc.)
        """
        subject = commit["subject"]
        body = commit["body"]
        date_str = commit["date"]
        
        # Determine Batch / Area
        batch = "General"
        
        # Match conventional commits: feat(admin): added new thing
        match = re.match(r"(?P<type>feat|fix|refactor|docs|perf|style|test|chore)(?:\((?P<scope>[^)]+)\))?:\s*(?P<desc>.*)", subject, re.IGNORECASE)
        
        title = subject
        features = []
        challenges = []
        
        if match:
            c_type = match.group("type").lower()
            scope = match.group("scope")
            desc = match.group("desc")
            
            if scope:
                # Capitalize scope for batch: "admin" -> "Admin"
                batch = scope.title()
                
            title = f"{desc.capitalize()} ({c_type})"
            
            if c_type == "feat":
                features.append(desc.capitalize())
            elif c_type == "fix":
                challenges.append(f"Fixed: {desc}")
                
        # Look for bullet points in the body for more features
        body_lines = [line.strip() for line in body.split('\n') if line.strip()]
        for line in body_lines:
            if line.startswith("- ") or line.startswith("* "):
                clean_line = line[2:].strip()
                # Simple heuristic: if it mentions 'fix' or 'issue', it's a challenge, else feature
                if "fix" in clean_line.lower() or "error" in clean_line.lower():
                    challenges.append(clean_line)
                else:
                    features.append(clean_line)
                    
        return {
            "date": datetime.strptime(date_str, "%Y-%m-%d").date(),
            "title": f"[{commit['hash'][:7]}] {title}",
            "description": body if body else f"Commit by {commit['author']}",
            "batch": batch,
            "features": features,
            "challenges": challenges
        }

    def sync_to_db(self, db: Session, limit: int = 50) -> Tuple[int, int]:
        """
        Fetches recent commits and saves them to the DB if they don't already exist.
        Returns (new_records_added, total_processed)
        """
        commits = self.fetch_recent_commits(limit=limit)
        if not commits:
            return 0, 0
            
        added_count = 0
        total_processed = len(commits)
        
        for commit in commits:
            log_data = self.parse_commit_to_log_data(commit)
            
            # Check if this precise commit was already logged (we put the hash in the title)
            hash_short = commit['hash'][:7]
            existing = db.query(DevelopmentLog).filter(
                DevelopmentLog.title.like(f"[{hash_short}]%")
            ).first()
            
            if not existing:
                new_log = DevelopmentLog(
                    date=log_data["date"],
                    title=log_data["title"],
                    description=log_data["description"],
                    batch=log_data["batch"],
                    features=log_data["features"],
                    challenges=log_data["challenges"]
                )
                db.add(new_log)
                added_count += 1
                
        db.commit()
        return added_count, total_processed

git_sync_service = GitSyncService()
