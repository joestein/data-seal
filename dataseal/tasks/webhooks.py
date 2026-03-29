"""Webhook delivery tasks."""

import hashlib
import hmac
import json
import uuid
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from dataseal.config import settings
from dataseal.models.envelope import Envelope
from dataseal.models.recipient import Recipient
from dataseal.models.webhook import WebhookDelivery, WebhookEndpoint
from dataseal.security.encryption import decrypt_value
from dataseal.security.url_validation import SSRFError, validate_webhook_url
from dataseal.tasks.celery_app import celery_app


def _get_sync_session() -> Session:
    engine = create_engine(settings.database_url_sync, pool_pre_ping=True)
    return Session(engine)


def _compute_signature(secret: str, payload: str) -> str:
    """Compute HMAC-SHA256 signature for webhook payload."""
    return hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


@celery_app.task(bind=True, max_retries=5)
def deliver_webhook(self, delivery_id: str) -> None:
    """Deliver a single webhook."""
    session = _get_sync_session()
    try:
        delivery = session.get(WebhookDelivery, delivery_id)
        if not delivery:
            return

        endpoint = session.get(WebhookEndpoint, str(delivery.webhook_endpoint_id))
        if not endpoint or not endpoint.is_active:
            delivery.status = "failed"
            session.commit()
            return

        payload_str = json.dumps(delivery.payload, default=str)
        # Decrypt the webhook secret before computing the HMAC signature
        try:
            decrypted_secret = decrypt_value(endpoint.secret)
        except ValueError:
            # Fallback for legacy plaintext secrets (pre-encryption migration)
            decrypted_secret = endpoint.secret
        signature = _compute_signature(decrypted_secret, payload_str)

        try:
            # Validate URL against SSRF before making the request
            try:
                validate_webhook_url(endpoint.url)
            except SSRFError:
                delivery.status = "failed"
                delivery.response_body = "Webhook URL failed SSRF validation"
                session.commit()
                return

            response = httpx.post(
                endpoint.url,
                content=payload_str,
                headers={
                    "Content-Type": "application/json",
                    "X-DataSeal-Signature-256": f"sha256={signature}",
                    "X-DataSeal-Event": delivery.event_type,
                },
                timeout=10.0,
            )

            delivery.response_status = response.status_code
            delivery.response_body = response.text[:5000]
            delivery.attempt_count += 1

            if response.is_success:
                delivery.status = "delivered"
            else:
                raise Exception(f"Webhook delivery failed: HTTP {response.status_code}")

        except Exception as exc:
            delivery.attempt_count += 1
            if delivery.attempt_count >= delivery.max_attempts:
                delivery.status = "failed"
            else:
                backoff = 2 ** (delivery.attempt_count - 1)
                delivery.next_retry_at = datetime.now(UTC) + timedelta(seconds=backoff)
                session.commit()
                raise self.retry(exc=exc, countdown=backoff)

        session.commit()

    except self.MaxRetriesExceededError:
        delivery.status = "failed"
        session.commit()
    finally:
        session.close()


@celery_app.task
def dispatch_webhook_event(envelope_id: str, event_type: str) -> None:
    """Dispatch a webhook event to all matching endpoints for the envelope owner."""
    session = _get_sync_session()
    try:
        envelope = session.get(Envelope, envelope_id)
        if not envelope:
            return

        endpoints = (
            session.execute(
                select(WebhookEndpoint)
                .where(WebhookEndpoint.user_id == envelope.user_id)
                .where(WebhookEndpoint.is_active.is_(True))
            )
            .scalars()
            .all()
        )

        # Build payload
        recipients = (
            session.execute(
                select(Recipient).where(Recipient.envelope_id == envelope_id)
            )
            .scalars()
            .all()
        )

        payload = {
            "event": event_type,
            "timestamp": datetime.now(UTC).isoformat(),
            "envelope_id": str(envelope.id),
            "data": {
                "envelope": {
                    "id": str(envelope.id),
                    "title": envelope.title,
                    "status": envelope.status,
                    "completed_at": envelope.completed_at.isoformat() if envelope.completed_at else None,
                    "recipients": [
                        {
                            "email": r.email,
                            "name": r.name,
                            "status": r.status,
                            "signed_at": r.signed_at.isoformat() if r.signed_at else None,
                        }
                        for r in recipients
                    ],
                }
            },
        }

        for endpoint in endpoints:
            # Check if the endpoint subscribes to this event type
            if event_type not in endpoint.events and "*" not in endpoint.events:
                continue

            delivery = WebhookDelivery(
                webhook_endpoint_id=endpoint.id,
                envelope_id=uuid.UUID(envelope_id),
                event_type=event_type,
                payload=payload,
            )
            session.add(delivery)
            session.flush()

            # Enqueue delivery
            deliver_webhook.delay(str(delivery.id))

        session.commit()

    finally:
        session.close()


@celery_app.task
def retry_pending_webhooks() -> None:
    """Retry pending webhook deliveries that are past their retry time."""
    session = _get_sync_session()
    try:
        now = datetime.now(UTC)
        pending = (
            session.execute(
                select(WebhookDelivery)
                .where(WebhookDelivery.status == "pending")
                .where(WebhookDelivery.next_retry_at <= now)
                .where(WebhookDelivery.attempt_count < WebhookDelivery.max_attempts)
            )
            .scalars()
            .all()
        )

        for delivery in pending:
            deliver_webhook.delay(str(delivery.id))

    finally:
        session.close()
