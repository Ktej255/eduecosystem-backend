"""Block model for local blockchain ledger"""

from sqlalchemy import Column, Integer, String, DateTime, JSON
from datetime import datetime
import hashlib
import json

from app.db.session import Base


class Block(Base):
    """Model for a block in the blockchain"""

    __tablename__ = "blockchain_blocks"

    id = Column(Integer, primary_key=True, index=True)
    index = Column(Integer, nullable=False, unique=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    data = Column(JSON, nullable=False)
    previous_hash = Column(String, nullable=False)
    hash = Column(String, nullable=False, unique=True, index=True)
    nonce = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<Block {self.index} - {self.hash[:10]}...>"

    def calculate_hash(self) -> str:
        """Calculate SHA-256 hash of the block"""
        block_string = json.dumps(
            {
                "index": self.index,
                "timestamp": str(self.timestamp),
                "data": self.data,
                "previous_hash": self.previous_hash,
                "nonce": self.nonce,
            },
            sort_keys=True,
        )

        return hashlib.sha256(block_string.encode()).hexdigest()
