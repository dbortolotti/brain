from __future__ import annotations

from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import parsedate_to_datetime

from memory_stack.models import MemoryItem


def memory_item_from_email(
    message: EmailMessage,
    *,
    origin_id: str,
    dataset_name: str,
    thread_id: str | None = None,
    tags: list[str] | None = None,
) -> MemoryItem:
    sent_at = parse_email_date(message.get("date"))
    body = extract_text_body(message)
    return MemoryItem(
        origin_id=origin_id,
        source_type="email",
        source_sent_at=sent_at,
        source_from=message.get("from"),
        thread_id=thread_id or message.get("thread-id") or message.get("message-id") or origin_id,
        dataset_name=dataset_name,
        title=message.get("subject"),
        body=body,
        tags=tags or [],
    )


def parse_email_date(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    parsed = parsedate_to_datetime(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def extract_text_body(message: EmailMessage) -> str:
    if message.is_multipart():
        for part in message.walk():
            content_type = part.get_content_type()
            disposition = part.get_content_disposition()
            if content_type == "text/plain" and disposition != "attachment":
                return part.get_content().strip()
        return ""
    if message.get_content_type() == "text/plain":
        return message.get_content().strip()
    return ""

