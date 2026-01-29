import hashlib
import json
import uuid
from collections.abc import Sequence
from datetime import date, datetime, timedelta, timezone
from typing import Any

import pytz
from google import genai
from google.genai import types
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.constants import DATE_PROMPT, PROMPT
from app.core.config import settings
from app.llms.google_llm import GoogleLLM
from app.models import MockEmail as Email
from app.models.email_summary import (
    EmailSummaryCreate,
    EmailSummaryUpdate,
)
from app.providers.email import IEmailProvider
from app.schema.summary import EmailThreadSummary
from app.utils import ensure_aware


class SummarizationService:
    """
    Orchestrates the summarization process, including fetching emails,
    calling the summarization model, and caching the results.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.llm = GoogleLLM()

    async def get_stored_summary(
        self, client_id: uuid.UUID, stale_after: timedelta = timedelta(hours=1)
    ) -> dict[str, Any] | None:
        """
        Retrieves a summary from the database if it's not stale.
        """
        summary = await crud.email_summary.get_by_client(
            session=self.session, client_id=client_id
        )
        if summary :
            last_refreshed = ensure_aware(summary.last_refreshed)
            if (self.now() - last_refreshed) < stale_after:
                return json.loads(summary.encrypted_summary)
        return None


    async def process_and_store_summary(
        self,
        client_id: uuid.UUID,
        email_provider: IEmailProvider,
        force_refresh: bool = False,
    ) -> dict:
        """
        Fetches emails, generates a new summary, and stores it in the DB.
        - `force_refresh` will ignore any existing content hash checks.
        """
        client = await crud.client.get(session=self.session, id=client_id)
        if not client:
            # This should ideally not be reached if called from a route
            # that already validates the client
            raise ValueError("Invalid client_id")

        emails = await email_provider.fetch_client_emails(
            client_email=client.email, session=self.session
        )
        new_hash = self.hash_emails(emails)

        existing_summary = await crud.email_summary.get_by_client(
            session=self.session, client_id=client_id
        )

        # If the content hasn't changed and we're not forcing a refresh,
        # just touch the updated_at timestamp and return the existing summary.
        if (
            not force_refresh
            and existing_summary
            and existing_summary.summary_hash == new_hash
        ):
            summary_to_update = EmailSummaryUpdate(last_refreshed=self.now())
            await crud.email_summary.update(
                session=self.session,
                db_obj=existing_summary,
                obj_in=summary_to_update,
            )
            return json.loads(existing_summary.encrypted_summary)

        # Otherwise, generate a new summary
        new_summary_data = await self.summarize_emails(emails)
        new_summary_json = json.dumps(new_summary_data)

        if existing_summary:
            summary_to_update = EmailSummaryUpdate(
                encrypted_summary=new_summary_json,
                summary_hash=new_hash,
                last_refreshed=self.now(),
                email_count=len(emails),
            )
            updated_summary = await crud.email_summary.update(
                session=self.session,
                db_obj=existing_summary,
                obj_in=summary_to_update,
            )
            return json.loads(updated_summary.encrypted_summary)

        # Or create a new one if it doesn't exist
        summary_to_create = EmailSummaryCreate(
            client_id=client_id,
            last_refreshed=self.now(),
            encrypted_summary=new_summary_json,
            summary_hash=new_hash,
            email_count=len(emails),
        )
        new_summary = await crud.email_summary.create(
            session=self.session, obj_in=summary_to_create
        )
        return json.loads(new_summary.encrypted_summary)

    async def summarize_emails(
        self,
        emails: Sequence[Email],
    ) -> dict:
        if not emails:
            return {
                "actors": [],
                "concluded": [],
                "open_items": [],
            }

        email_text = "\n\n".join(
            f"From: {e.sender}\nTo: {e.recipient}\n{e.body}" for e in emails
        )
        prompt = f"{PROMPT.format(EmailThreadSummary.model_json_schema())}\n{DATE_PROMPT.format(date.today(), datetime.now().strftime('%H:%M:%S'), pytz.timezone('UTC'))}"
        messages = [{'role':'system','content':prompt},
                    {'role':'user','content':f'Summarize this email thread \n{email_text}.'}]

        return self._safe_parse(await self.llm.generate(messages,json_resp=True))

    def hash_emails(self, emails: Sequence[Email]) -> str:
        payload = "".join(e.body for e in emails)
        return hashlib.sha256(payload.encode()).hexdigest()

    def now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _safe_parse(self, text: str) -> dict:
        start = text.find("{")
        end = text.rfind("}") + 1
        return json.loads(text[start:end])
