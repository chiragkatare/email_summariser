from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import crud_email_summary
from app.services.mock_email_service import MockEmailService
from app.services.summarization_service import SummarizationService
from app.services.encryption_service import EncryptionService
from app.services.cache_service import CacheService


class EmailContextService:
    """
    Core business service for Email Context.
    """

    def __init__(
        self,
        cache: CacheService,
    ):
        self.cache = cache
        self.email_service = MockEmailService()
        self.summarizer = SummarizationService()
        self.encryption = EncryptionService()

    async def get_summary(
        self,
        session: AsyncSession,
        *,
        client_id,
        force_refresh: bool = False,
    ) -> dict:
        cache_key = f"email-summary:{client_id}"

        if not force_refresh:
            cached = await self.cache.get(cache_key)
            if cached:
                return cached

        emails = await self.email_service.list_emails_for_client(
            session,
            client_id=client_id,
        )

        existing = await crud_email_summary.get_by_client(
            session,
            client_id=client_id,
        )

        email_hash = self.summarizer.hash_emails(emails)

        if existing and not force_refresh:
            if existing.summary_hash == email_hash:
                decrypted = self.encryption.decrypt(
                    existing.encrypted_summary
                )
                await self.cache.set(cache_key, decrypted)
                return decrypted

        summary = await self.summarizer.summarize(emails)
        encrypted = self.encryption.encrypt(summary)
        now = self.summarizer.now()

        if existing:
            existing.encrypted_summary = encrypted
            existing.email_count = len(emails)
            existing.summary_hash = email_hash
            existing.last_refreshed = now
            record = existing
        else:
            record = crud_email_summary.model(
                client_id=client_id,
                encrypted_summary=encrypted,
                email_count=len(emails),
                summary_hash=email_hash,
                last_refreshed=now,
            )

        await crud_email_summary.upsert(session, record)
        await self.cache.set(cache_key, summary)

        return summary
