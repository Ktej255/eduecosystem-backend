from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from app.api.api_v1.endpoints.planner import RAS_SUBJECTS

router = APIRouter()

@router.get("/syllabus-graph")
async def get_syllabus_graph():
    """
    Return syllabus data structured for a graph visualization.
    Uses the RAS_SUBJECTS data from the planner.
    """
    nodes = []
    edges = []
    
    # Root node
    nodes.append({
        "id": "syllabus_root",
        "type": "root",
        "data": { "label": "RAS Syllabus" },
        "position": { "x": 0, "y": 0 }
    })
    
    y_offset = 150
    subject_x = 0
    
    for subject_key, subject_data in RAS_SUBJECTS.items():
        subject_id = f"subject_{subject_key}"
        
        # Subject Node
        nodes.append({
            "id": subject_id,
            "type": "subject",
            "data": {
                "label": subject_data["name"],
                "priority": subject_data.get("priority", "medium"),
                "topic_count": len(subject_data.get("topics", []))
            },
            "position": { "x": subject_x, "y": y_offset }
        })
        
        # Edge: Root -> Subject
        edges.append({
            "id": f"e_root_{subject_id}",
            "source": "syllabus_root",
            "target": subject_id,
            "animated": True
        })
        
        topic_y = y_offset + 150
        topic_x_offset = subject_x - 200
        
        for i, topic in enumerate(subject_data.get("topics", [])[:5]): # Limit for performance
            topic_id = topic.get("id", f"topic_{i}")
            
            nodes.append({
                "id": topic_id,
                "type": "topic",
                "data": {
                    "label": topic["name"],
                    "subtopics": topic.get("subtopics", []),
                    "note": topic.get("note")
                },
                "position": { "x": topic_x_offset + (i * 180), "y": topic_y }
            })
            
            edges.append({
                "id": f"e_{subject_id}_{topic_id}",
                "source": subject_id,
                "target": topic_id
            })
        
        subject_x += 400
        
    return {
        "nodes": nodes,
        "edges": edges,
        "meta": {
            "total_subjects": len(RAS_SUBJECTS),
            "timestamp": "Generated"
        }
    }
