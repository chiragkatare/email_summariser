from abc import ABC, abstractmethod
from app.schema.email import EmailMessage

class IEmailProvider(ABC):
    @abstractmethod
    async def fetch_client_emails(self, client_email: str,**kwargs) -> list[EmailMessage]:
        """Fetch all historical emails for a specific client across the firm."""
        pass