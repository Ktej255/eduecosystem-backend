from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class PortalMapService:
    """
    Service to generate the Page Dependency Representation (PDR) graph.
    In a full implementation, this would scan frontend routes/code.
    For now, it provides a centralized definition of the portal structure.
    """
    
    def get_full_graph(self) -> Dict[str, Any]:
        """
        Returns nodes and links for the entire platform PDR.
        """
        nodes = []
        links = []
        
        # 1. Admin Portal
        self._add_cluster(nodes, links, "admin", "Admin Portal", "admin", [
            ("dashboard", "Dashboard", "/admin"),
            ("strategic", "Strategic Overview", "/admin/executive"),
            ("cohort", "Cohort Intelligence", "/admin/cohort-intelligence"),
            ("revenue", "Revenue Analysis", "/admin/analytics"),
            ("at_risk", "At-Risk Monitor", "/admin/performance"),
            ("journey", "Student Journeys", "/admin/student-journey"),
            ("teachers", "Teacher Management", "/admin/teachers"),
            ("content_health", "Content Health", "/admin/content-system"),
            ("upsc", "UPSC Registry", "/admin/upsc-content"),
            ("drills", "Assessment Drills", "/admin/drill/analytics"),
            ("presence", "Attendance", "/admin/attendance"),
            ("interventions", "Intervention Engine", "/admin/interventions"),
            ("users", "User Management", "/admin/users"),
            ("pdr", "Portal Map", "/admin/pdr"),
        ])
        
        # 2. Student Portal
        self._add_cluster(nodes, links, "student", "Student Portal", "student", [
            ("dashboard", "Dashboard", "/student/dashboard"),
            ("courses", "My Courses", "/student/courses"),
            ("assignments", "Assignments", "/student/assignments"),
            ("grades", "Grades", "/student/grades"),
            ("profile", "Profile", "/student/profile"),
            ("batch1", "Batch 1 (Polity)", "/student/batch1"),
            ("batch1_1", "Batch 1.1 (Revision)", "/student/batch1-1"),
            ("batch2", "Batch 2 (Ancient Wisdom)", "/student/batch2"),
        ])
        
        # 3. Teacher Portal
        self._add_cluster(nodes, links, "teacher", "Teacher Portal", "teacher", [
            ("dashboard", "Dashboard", "/teacher/dashboard"),
            ("classes", "My Classes", "/teacher/classes"),
            ("students", "Students", "/teacher/students"),
            ("grading", "Grading", "/teacher/grading"),
            ("resources", "Resources", "/teacher/resources"),
        ])
        
        # 4. CRM Portal
        self._add_cluster(nodes, links, "crm", "CRM Portal", "crm", [
            ("dashboard", "Dashboard", "/crm/dashboard"),
            ("leads", "Leads", "/crm/leads"),
            ("customers", "Customers", "/crm/customers"),
            ("tasks", "Tasks", "/crm/tasks"),
            ("pipelines", "Pipelines", "/crm/pipelines"),
        ])
        
        # 5. Graphotherapy
        self._add_cluster(nodes, links, "grapho", "Graphotherapy", "grapho", [
            ("landing", "Landing Page", "/graphotherapy"),
            ("upload", "Upload Analysis", "/graphotherapy/upload"),
            ("analysis", "Analysis Result", "/graphotherapy/analysis"),
            ("history", "History", "/graphotherapy/history"),
        ])
        
        # Inter-portal connections
        links.append({"source": "admin_users", "target": "student_profile", "label": "Manage"})
        links.append({"source": "admin_users", "target": "teacher_students", "label": "Assign"})
        links.append({"source": "crm_customers", "target": "student_profile", "label": "Sync"})
        links.append({"source": "admin_daily_reports", "target": "admin_dev_history", "label": "Tracks"})
        
        return {"nodes": nodes, "links": links}
        
    def _add_cluster(self, nodes, links, cluster_id, cluster_label, group_type, pages):
        """Helper to add a cluster of nodes"""
        # Central Hub Node
        hub_id = f"{cluster_id}_hub"
        nodes.append({
            "id": hub_id,
            "label": cluster_label,
            "type": "portal",
            "group": group_type,
            "connections": len(pages)
        })
        
        # Page Nodes
        for page_key, label, route in pages:
            node_id = f"{cluster_id}_{page_key}"
            nodes.append({
                "id": node_id,
                "label": label,
                "type": "page",
                "group": group_type,
                "route": route,
                "connections": 1
            })
            # Link to hub
            links.append({
                "source": hub_id,
                "target": node_id,
                "label": "Contains"
            })

portal_map_service = PortalMapService()
