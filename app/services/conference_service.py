import os
import httpx
from typing import Optional, Dict, Any


class ConferenceService:
    """
    Service for managing video conference rooms via Daily.co
    """

    def __init__(self):
        self.api_key = os.getenv("DAILY_API_KEY")
        self.base_url = "https://api.daily.co/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def create_room(
        self,
        name: Optional[str] = None,
        privacy: str = "public",
        properties: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new video room
        """
        if not self.api_key:
            # Return mock data for development if no API key
            return {
                "id": "mock-room-id",
                "name": name or "test-room",
                "url": "https://your-domain.daily.co/test-room",
                "privacy": privacy,
            }

        payload = {
            "properties": {
                "enable_chat": True,
                "enable_screenshare": True,
                "start_video_off": False,
                "start_audio_off": False,
                **(properties or {}),
            }
        }

        if name:
            payload["name"] = name
        if privacy:
            payload["privacy"] = privacy

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/rooms", headers=self.headers, json=payload
            )
            response.raise_for_status()
            return response.json()

    async def get_room(self, name: str) -> Dict[str, Any]:
        """Get room details"""
        if not self.api_key:
            return {"name": name, "url": f"https://mock.daily.co/{name}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/rooms/{name}", headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def delete_room(self, name: str):
        """Delete a room"""
        if not self.api_key:
            return

        async with httpx.AsyncClient() as client:
            await client.delete(f"{self.base_url}/rooms/{name}", headers=self.headers)

    # --- Agora Support ---

    def generate_agora_token(self, channel_name: str, uid: int) -> str:
        """
        Generate Agora RTC token
        Requires AGORA_APP_ID and AGORA_APP_CERTIFICATE env vars
        """
        app_id = os.getenv("AGORA_APP_ID")
        app_certificate = os.getenv("AGORA_APP_CERTIFICATE")

        if not app_id or not app_certificate:
            return "mock-agora-token-for-development"

        # In a real implementation, we would use agora_token_builder
        # from agora_token_builder import RtcTokenBuilder, Role_Attendee
        # expiration_time_in_seconds = 3600
        # current_timestamp = int(time.time())
        # privilege_expired_ts = current_timestamp + expiration_time_in_seconds
        # return RtcTokenBuilder.buildTokenWithUid(
        #     app_id, app_certificate, channel_name, uid, Role_Attendee, privilege_expired_ts
        # )

        return "mock-agora-token-requires-package"


conference_service = ConferenceService()
