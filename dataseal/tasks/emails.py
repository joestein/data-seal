"""Email sending tasks."""

# Jinja2 environment for email templates
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from dataseal.config import settings
from dataseal.models.envelope import Envelope
from dataseal.models.recipient import Recipient
from dataseal.tasks.celery_app import celery_app

_template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "email_templates")
_jinja_env = Environment(
    loader=FileSystemLoader(_template_dir),
    autoescape=select_autoescape(["html"]),
)


def _get_sync_session() -> Session:
    """Get a synchronous DB session for Celery tasks."""
    engine = create_engine(settings.database_url_sync, pool_pre_ping=True)
    return Session(engine)


def _send_email(to_email: str, subject: str, html_body: str) -> None:
    """Send an email via SMTP."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_address}>"
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        if settings.smtp_use_tls:
            server.starttls()
        if settings.smtp_user:
            server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def send_signing_emails(self, envelope_id: str) -> None:
    """Send signing invitation emails to recipients in the current routing group."""
    session = _get_sync_session()
    try:
        envelope = session.get(Envelope, envelope_id)
        if not envelope:
            return

        recipients = (
            session.execute(
                select(Recipient)
                .where(Recipient.envelope_id == envelope_id)
                .where(Recipient.status == "sent")
                .where(Recipient.signing_token.isnot(None))
            )
            .scalars()
            .all()
        )

        template = _jinja_env.get_template("signing_invite.html")

        for recipient in recipients:
            if recipient.role == "cc":
                continue

            signing_url = f"{settings.app_url}/sign/{recipient.signing_token}"
            html = template.render(
                recipient_name=recipient.name,
                sender_name=envelope.user.full_name if hasattr(envelope, "user") and envelope.user else "DataSeal User",
                envelope_title=envelope.title,
                message=envelope.message,
                signing_url=signing_url,
                app_url=settings.app_url,
            )

            try:
                _send_email(
                    recipient.email,
                    f"Please sign: {envelope.title}",
                    html,
                )
            except Exception as exc:
                raise self.retry(exc=exc)

    finally:
        session.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def send_completion_emails(self, envelope_id: str) -> None:
    """Send completion notification emails to all parties."""
    session = _get_sync_session()
    try:
        envelope = session.get(Envelope, envelope_id)
        if not envelope:
            return

        template = _jinja_env.get_template("completed.html")
        download_url = f"{settings.app_url}/api/v1/envelopes/{envelope_id}/combined"

        recipients = (
            session.execute(
                select(Recipient).where(Recipient.envelope_id == envelope_id)
            )
            .scalars()
            .all()
        )

        for recipient in recipients:
            html = template.render(
                recipient_name=recipient.name,
                envelope_title=envelope.title,
                download_url=download_url,
                app_url=settings.app_url,
            )
            try:
                _send_email(
                    recipient.email,
                    f"Completed: {envelope.title}",
                    html,
                )
            except Exception as exc:
                raise self.retry(exc=exc)

    finally:
        session.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def send_void_notification(self, envelope_id: str) -> None:
    """Send voided notification to all recipients."""
    session = _get_sync_session()
    try:
        envelope = session.get(Envelope, envelope_id)
        if not envelope:
            return

        template = _jinja_env.get_template("voided.html")

        recipients = (
            session.execute(
                select(Recipient).where(Recipient.envelope_id == envelope_id)
            )
            .scalars()
            .all()
        )

        for recipient in recipients:
            html = template.render(
                recipient_name=recipient.name,
                envelope_title=envelope.title,
                voided_reason=envelope.voided_reason,
                app_url=settings.app_url,
            )
            try:
                _send_email(
                    recipient.email,
                    f"Voided: {envelope.title}",
                    html,
                )
            except Exception as exc:
                raise self.retry(exc=exc)

    finally:
        session.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def send_decline_notification(self, envelope_id: str, recipient_id: str) -> None:
    """Notify the sender that a recipient declined."""
    session = _get_sync_session()
    try:
        envelope = session.get(Envelope, envelope_id)
        recipient = session.get(Recipient, recipient_id)
        if not envelope or not recipient:
            return

        template = _jinja_env.get_template("declined.html")
        html = template.render(
            recipient_name=recipient.name,
            envelope_title=envelope.title,
            declined_reason=recipient.declined_reason,
            app_url=settings.app_url,
        )

        # Get the sender's email from the user
        from dataseal.models.user import User

        user = session.get(User, str(envelope.user_id))
        if user:
            _send_email(
                user.email,
                f"{recipient.name} declined: {envelope.title}",
                html,
            )

    except Exception as exc:
        raise self.retry(exc=exc)
    finally:
        session.close()
