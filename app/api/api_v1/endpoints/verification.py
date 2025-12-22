"""API endpoints for certificate verification"""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.services.blockchain_service import blockchain_service

router = APIRouter()


@router.get("/verify/{certificate_hash}")
def verify_certificate(
    certificate_hash: str,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Verify a certificate against the blockchain ledger.
    Public endpoint, no auth required.
    """
    service = blockchain_service(db)

    # Find block by hash
    block = service.get_block_by_hash(certificate_hash)
    if not block:
        raise HTTPException(
            status_code=404, detail="Certificate hash not found in blockchain"
        )

    # Validate chain integrity (optional, but good for demo)
    # In production, we might cache this or run periodically
    is_valid = service.is_chain_valid()

    return {
        "verified": True,
        "chain_valid": is_valid,
        "block_index": block.index,
        "timestamp": block.timestamp,
        "certificate_data": block.data,
        "hash": block.hash,
        "previous_hash": block.previous_hash,
    }
