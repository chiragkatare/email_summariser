import httpx

from app.providers.email import IEmailProvider
from app.schema.email import EmailMessage


class MicrosoftGraphProvider(IEmailProvider):
    def __init__(self, access_token: str):
        self.base_url = "https://graph.microsoft.com/v1.0"
        self.headers = {"Authorization": f"Bearer {access_token}"}

    async def fetch_client_emails(self, client_email: str) -> list[EmailMessage]:
        # In a real scenario, you'd use a $filter query to find emails 
        # involving this client across the firm's shared mailboxes.
        async with httpx.AsyncClient() as client:
            # Example endpoint logic
            # response = await client.get(f"{self.base_url}/users/...", headers=self.headers)
            return [] # Placeholder for future implementation