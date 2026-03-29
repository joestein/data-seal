"""API tests for document upload and management."""

import io
from unittest.mock import patch

import pytest

# Minimal valid PDF bytes (magic bytes + minimal structure)
MINIMAL_PDF = (
    b"%PDF-1.4\n1 0 obj\n<</Type /Catalog>>\nendobj\n"
    b"xref\n0 1\n0000000000 65535 f \ntrailer\n<</Size 1>>\nstartxref\n9\n%%EOF"
)

FAKE_NON_PDF = b"This is not a PDF file, just plain text."


@pytest.fixture
def envelope(client, registered_user, auth_headers):
    """Create a test envelope."""
    response = client.post("/api/v1/envelopes", json={"title": "Document Test Envelope"}, headers=auth_headers)
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def uploaded_document(client, registered_user, auth_headers, envelope):
    """Upload a PDF document to the envelope (with storage mocked)."""
    with patch("dataseal.api.documents.storage.save") as mock_save:
        mock_save.return_value = None
        with patch("dataseal.tasks.documents.render_document_pages.delay", return_value=None):
            response = client.post(
                f"/api/v1/envelopes/{envelope['id']}/documents",
                files={"file": ("contract.pdf", io.BytesIO(MINIMAL_PDF), "application/pdf")},
                headers=auth_headers,
            )
    assert response.status_code == 201
    return response.json()


class TestDocumentUpload:
    def test_upload_valid_pdf(self, client, registered_user, auth_headers, envelope):
        with patch("dataseal.api.documents.storage.save") as mock_save:
            mock_save.return_value = None
            with patch("dataseal.tasks.documents.render_document_pages.delay", return_value=None):
                response = client.post(
                    f"/api/v1/envelopes/{envelope['id']}/documents",
                    files={"file": ("test.pdf", io.BytesIO(MINIMAL_PDF), "application/pdf")},
                    headers=auth_headers,
                )
        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "test.pdf"
        assert data["content_type"] == "application/pdf"
        assert data["size_bytes"] == len(MINIMAL_PDF)

    def test_upload_non_pdf_returns_400(self, client, registered_user, auth_headers, envelope):
        response = client.post(
            f"/api/v1/envelopes/{envelope['id']}/documents",
            files={"file": ("not_pdf.txt", io.BytesIO(FAKE_NON_PDF), "text/plain")},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_upload_wrong_mime_type_returns_400(self, client, registered_user, auth_headers, envelope):
        # PDF magic bytes but wrong MIME type
        response = client.post(
            f"/api/v1/envelopes/{envelope['id']}/documents",
            files={"file": ("doc.pdf", io.BytesIO(MINIMAL_PDF), "text/html")},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_upload_unauthenticated_returns_401(self, client, envelope):
        response = client.post(
            f"/api/v1/envelopes/{envelope['id']}/documents",
            files={"file": ("test.pdf", io.BytesIO(MINIMAL_PDF), "application/pdf")},
        )
        assert response.status_code == 401

    def test_upload_to_nonexistent_envelope_returns_404(self, client, registered_user, auth_headers):
        with patch("dataseal.api.documents.storage.save"):
            response = client.post(
                "/api/v1/envelopes/00000000-0000-0000-0000-000000000000/documents",
                files={"file": ("test.pdf", io.BytesIO(MINIMAL_PDF), "application/pdf")},
                headers=auth_headers,
            )
        assert response.status_code == 404

    def test_upload_to_other_users_envelope_returns_404(
        self,
        client,
        registered_user,
        auth_headers,
        envelope,
        second_user_auth,
    ):
        response = client.post(
            f"/api/v1/envelopes/{envelope['id']}/documents",
            files={"file": ("test.pdf", io.BytesIO(MINIMAL_PDF), "application/pdf")},
            headers=second_user_auth,
        )
        assert response.status_code == 404


class TestDocumentList:
    def test_list_documents_empty(self, client, registered_user, auth_headers, envelope):
        response = client.get(
            f"/api/v1/envelopes/{envelope['id']}/documents",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json() == []

    def test_list_documents_after_upload(self, client, registered_user, auth_headers, envelope, uploaded_document):
        response = client.get(
            f"/api/v1/envelopes/{envelope['id']}/documents",
            headers=auth_headers,
        )
        assert response.status_code == 200
        docs = response.json()
        assert len(docs) == 1
        assert docs[0]["id"] == uploaded_document["id"]


class TestDocumentGet:
    def test_get_document_success(self, client, registered_user, auth_headers, envelope, uploaded_document):
        response = client.get(
            f"/api/v1/envelopes/{envelope['id']}/documents/{uploaded_document['id']}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["id"] == uploaded_document["id"]

    def test_get_nonexistent_document_returns_404(self, client, registered_user, auth_headers, envelope):
        response = client.get(
            f"/api/v1/envelopes/{envelope['id']}/documents/00000000-0000-0000-0000-000000000000",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestDocumentDelete:
    def test_delete_document_success(self, client, registered_user, auth_headers, envelope, uploaded_document):
        with patch("dataseal.api.documents.storage.delete") as mock_delete:
            mock_delete.return_value = None
            response = client.delete(
                f"/api/v1/envelopes/{envelope['id']}/documents/{uploaded_document['id']}",
                headers=auth_headers,
            )
        assert response.status_code == 204

    def test_delete_nonexistent_document_returns_404(self, client, registered_user, auth_headers, envelope):
        response = client.delete(
            f"/api/v1/envelopes/{envelope['id']}/documents/00000000-0000-0000-0000-000000000000",
            headers=auth_headers,
        )
        assert response.status_code == 404
