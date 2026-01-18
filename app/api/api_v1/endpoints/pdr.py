from fastapi import APIRouter, Depends
from app.api.deps import get_current_user
from app.models.user import User
from app.services.portal_map_service import portal_map_service

router = APIRouter()

@router.get("/pdr/graph")
def get_pdr_graph(
    current_user: User = Depends(get_current_user)
):
    """
    Get the full Page Dependency Representation (PDR) graph.
    Returns nodes and links for visualization.
    """
    return portal_map_service.get_full_graph()
