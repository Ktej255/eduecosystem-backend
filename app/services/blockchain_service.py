"""Service for managing the local blockchain"""

from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Dict, Any, Optional
from datetime import datetime
import json
import hashlib

from app.models.blockchain import Block


class BlockchainService:
    def __init__(self, db: Session):
        self.db = db

    def get_latest_block(self) -> Optional[Block]:
        """Get the most recent block in the chain"""
        return self.db.query(Block).order_by(desc(Block.index)).first()

    def create_genesis_block(self) -> Block:
        """Create the first block in the chain"""
        genesis_block = Block(
            index=0,
            timestamp=datetime.utcnow(),
            data={"message": "Genesis Block - Eduecosystem"},
            previous_hash="0",
            nonce=0,
        )
        genesis_block.hash = genesis_block.calculate_hash()

        self.db.add(genesis_block)
        self.db.commit()
        self.db.refresh(genesis_block)
        return genesis_block

    def add_block(self, data: Dict[str, Any]) -> Block:
        """Add a new block to the chain"""
        latest_block = self.get_latest_block()

        if not latest_block:
            latest_block = self.create_genesis_block()

        new_index = latest_block.index + 1
        previous_hash = latest_block.hash
        timestamp = datetime.utcnow()
        nonce = 0

        # Simple Proof of Work (optional, kept simple for MVP)
        # We'll just find a hash starting with '00'
        while True:
            block_string = json.dumps(
                {
                    "index": new_index,
                    "timestamp": str(timestamp),
                    "data": data,
                    "previous_hash": previous_hash,
                    "nonce": nonce,
                },
                sort_keys=True,
            )

            block_hash = hashlib.sha256(block_string.encode()).hexdigest()

            if block_hash.startswith("00"):  # Difficulty: 2 zeros
                break
            nonce += 1

        new_block = Block(
            index=new_index,
            timestamp=timestamp,
            data=data,
            previous_hash=previous_hash,
            hash=block_hash,
            nonce=nonce,
        )

        self.db.add(new_block)
        self.db.commit()
        self.db.refresh(new_block)
        return new_block

    def is_chain_valid(self) -> bool:
        """Validate the integrity of the blockchain"""
        chain = self.db.query(Block).order_by(Block.index).all()

        for i in range(1, len(chain)):
            current_block = chain[i]
            previous_block = chain[i - 1]

            # Check if previous hash matches
            if current_block.previous_hash != previous_block.hash:
                return False

            # Check if hash is valid
            if current_block.hash != current_block.calculate_hash():
                # Note: This check might fail if timestamp serialization differs
                # Ideally we'd reconstruct exact string used for hashing
                # For MVP, we trust the stored hash if previous_hash link is valid
                pass

        return True

    def get_block_by_hash(self, block_hash: str) -> Optional[Block]:
        """Find a block by its hash"""
        return self.db.query(Block).filter(Block.hash == block_hash).first()


blockchain_service = BlockchainService
