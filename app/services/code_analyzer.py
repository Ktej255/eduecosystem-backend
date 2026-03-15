import os
from pathlib import Path
from typing import Dict, Any, Tuple

class CodeAnalyzerService:
    """
    Service to analyze the repository and compute real-time code metrics
    like Total Lines of Code (LOC), File Breakdown, and Component Counts.
    """
    
    def __init__(self):
        # Resolve path relative to backend/app/services/code_analyzer.py
        # 0:services, 1:app, 2:backend, 3:Eduecosystem (Root)
        self.root_dir = Path(__file__).resolve().parents[3]
        
    def _is_ignored_dir(self, dir_name: str) -> bool:
        """Check if a directory should be completely ignored."""
        ignores = {'node_modules', '.git', '.next', 'dist', 'build', '__pycache__', '.venv', 'venv'}
        return dir_name in ignores

    def analyze_repository(self) -> Dict[str, Any]:
        """
        Walks through the frontend and backend directories and computes statistics.
        Returns a dictionary formatted for the CodeMetricsDashboard.
        """
        frontend_dir = self.root_dir / "frontend"
        backend_dir = self.root_dir / "backend"
        
        total_loc = 0
        component_count = 0
        
        # Track by extension
        extension_counts = {
            ".ts": 0,
            ".tsx": 0,
            ".css": 0,
            ".py": 0
        }
        
        # Track by Feature area (LOC heuristic based on paths)
        feature_locs = {
            "Admin & Dashboard Architecture": 0,
            "History Module": 0,
            "Polity Module": 0,
            "UPSC Store": 0,
            "Core Framework (FE)": 0,
            "Core Framework (BE)": 0,
            "Other": 0
        }
        
        # Scan Frontend
        if frontend_dir.exists():
            for root, dirs, files in os.walk(str(frontend_dir)):
                # Prevent os.walk from entering ignored directories by modifying dirs in place
                dirs[:] = [d for d in dirs if not self._is_ignored_dir(d)]
                    
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in extension_counts:
                        filepath = os.path.join(root, file)
                        try:
                            # Skip files > 1MB to avoid hanging on massive data dumps
                            if os.path.getsize(filepath) > 1_000_000:
                                continue
                            with open(filepath, 'r', encoding='utf-8') as f:
                                loc = f.read().count('\n') + 1
                                total_loc += loc
                                
                                val = extension_counts.get(ext, 0)
                                extension_counts[ext] = val + loc
                                
                                # Heuristics for Features
                                if "admin-portal" in root or "admin" in root.split(os.sep):
                                    feature_locs["Admin & Dashboard Architecture"] += loc
                                elif "history" in root.lower() or "ancient" in root.lower() or "medieval" in root.lower() or "modern" in root.lower():
                                    feature_locs["History Module"] += loc
                                elif "polity" in root.lower():
                                    feature_locs["Polity Module"] += loc
                                elif "store" in root.lower() or "payment" in root.lower():
                                    feature_locs["UPSC Store"] += loc
                                else:
                                    feature_locs["Core Framework (FE)"] += loc
                                    
                                # Count components (heuristic: PascalCase files or under components dir)
                                if ext == ".tsx" or "components" in root.split(os.sep):
                                    component_count += 1
                                    
                        except Exception:
                            pass # Skip files that can't be read (e.g. binary/images with wrong ext)

        # Scan Backend
        if backend_dir.exists():
            for root, dirs, files in os.walk(str(backend_dir)):
                # Prevent os.walk from entering ignored directories
                dirs[:] = [d for d in dirs if not self._is_ignored_dir(d)]
                    
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in extension_counts:
                        filepath = os.path.join(root, file)
                        try:
                            if os.path.getsize(filepath) > 1_000_000:
                                continue
                            with open(filepath, 'r', encoding='utf-8') as f:
                                loc = f.read().count('\n') + 1
                                total_loc += loc
                                
                                val = extension_counts.get(ext, 0)
                                extension_counts[ext] = val + loc
                                
                                # Identify backend domains
                                if "admin" in root or file.startswith("admin"):
                                    feature_locs["Admin & Dashboard Architecture"] += loc
                                elif "payment" in root or "store" in root:
                                    feature_locs["UPSC Store"] += loc
                                else:
                                    feature_locs["Core Framework (BE)"] += loc
                        except Exception:
                            pass

        return {
            "totalLOC": total_loc,
            "components": component_count,
            "features": [
                {"label": "History Module", "value": feature_locs["History Module"], "color": "bg-blue-500"},
                {"label": "Polity Module", "value": feature_locs["Polity Module"], "color": "bg-purple-500"},
                {"label": "Admin & Dashboard Architecture", "value": feature_locs["Admin & Dashboard Architecture"], "color": "bg-emerald-500"},
                {"label": "UPSC Store", "value": feature_locs["UPSC Store"], "color": "bg-amber-500"},
                {"label": "Core Framework (Frontend)", "value": feature_locs["Core Framework (FE)"], "color": "bg-indigo-500"},
                {"label": "Core Framework (Backend)", "value": feature_locs["Core Framework (BE)"], "color": "bg-slate-500"}
            ],
            "files": [
                {"label": "TypeScript (Logic)", "value": extension_counts[".ts"], "ext": ".ts", "color": "text-blue-400"},
                {"label": "React (UI)", "value": extension_counts[".tsx"], "ext": ".tsx", "color": "text-cyan-400"},
                {"label": "Styling (CSS)", "value": extension_counts[".css"], "ext": ".css", "color": "text-pink-400"},
                {"label": "Python (Backend)", "value": extension_counts[".py"], "ext": ".py", "color": "text-emerald-400"}
            ]
        }

code_analyzer_service = CodeAnalyzerService()
