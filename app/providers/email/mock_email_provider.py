import uuid
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession


from app.models import MockEmail as Email
from .base_email_provider import IEmailProvider


class MockEmailProvider(IEmailProvider):
    """
    Abstracts the email data source.
    """

    async def fetch_client_emails(
        self, *, session: AsyncSession, client_email: str
    ) -> Sequence[Email]:
        base_time = datetime.now(timezone.utc)

        return [
            Email(
                id=uuid.uuid4(),
                subject="Invoice #1023 Payment Reminder",
                sender="billing@vendor.com",
                recipient=client_email,
                body="Dear Customer, This is a reminder that invoice #1023 is due tomorrow. Please arrange payment.",
                received_at=base_time - timedelta(days=1),
                is_read=True,
            ),
            Email(
                id=uuid.uuid4(),
                subject="Quarterly Financial Report Q3",
                sender="cfo@client-corp.com",
                recipient=client_email,
                body="Attached is the preliminary financial report for Q3. Please review and provide feedback.",
                received_at=base_time - timedelta(hours=4),
                is_read=False,
            ),
            Email(
                id=uuid.uuid4(),
                subject="Meeting Request: Tax Audit Prep",
                sender="auditor@irs-proxy.com",
                recipient=client_email,
                body="We would like to schedule a meeting next Tuesday to discuss the upcoming tax audit preparation.",
                received_at=base_time - timedelta(minutes=30),
                is_read=False,
            ),
            Email(
                id=uuid.uuid4(),
                subject="Receipt for your recent purchase",
                sender="no-reply@amazon-clone.com",
                recipient=client_email,
                body="Thank you for your order. Your order #123-456-789 has been shipped.",
                received_at=base_time - timedelta(days=2),
                is_read=True,
            ),
            Email(
                id=uuid.uuid4(),
                subject="Urgent: Bank Reconciliation Discrepancy",
                sender="controller@firm.com",
                recipient=client_email,
                body="I noticed a discrepancy in the bank reconciliation for last month. Can you investigate?",
                received_at=base_time - timedelta(hours=1),
                is_read=False,
            ),
        ]

