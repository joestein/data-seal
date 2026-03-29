# DataSeal API Reference

Base URL: `http://localhost:8000/api/v1`

Interactive docs: `/docs` (Swagger UI) | `/redoc` (ReDoc)

---

## Authentication

All endpoints except the public signing and PowerForm endpoints require authentication.

### Methods

**JWT Bearer token**
```
Authorization: Bearer <access_token>
```

**API key**
```
Authorization: Bearer ds_key_<key>
```

---

## Auth

### POST /auth/register

Register a new user account.

**Request body**
```json
{
  "email": "you@example.com",
  "password": "s3curePass!",
  "full_name": "Jane Smith",
  "company": "Acme Corp"
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `email` | string | Yes | Must be unique |
| `password` | string | Yes | 8–128 characters |
| `full_name` | string | Yes | |
| `company` | string | No | |

**Response** `201 Created`
```json
{
  "id": "01926...",
  "email": "you@example.com",
  "full_name": "Jane Smith",
  "company": "Acme Corp",
  "is_active": true,
  "is_verified": false,
  "created_at": "2026-03-28T12:00:00Z",
  "updated_at": "2026-03-28T12:00:00Z"
}
```

**Errors**: `409 Conflict` — email already registered.

---

### POST /auth/login

Obtain JWT access and refresh tokens.

**Request body**
```json
{
  "email": "you@example.com",
  "password": "s3curePass!"
}
```

**Response** `200 OK`
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 900
}
```

`expires_in` is in seconds. Access tokens expire after `ACCESS_TOKEN_EXPIRY_MINUTES` (default 15 min).

**Errors**: `401 Unauthorized` — invalid credentials. `403 Forbidden` — account deactivated.

---

### POST /auth/refresh

Exchange a refresh token for a new access/refresh token pair.

**Request body**
```json
{
  "refresh_token": "eyJ..."
}
```

**Response** `200 OK` — same schema as `/auth/login`.

**Errors**: `401 Unauthorized` — invalid or expired refresh token.

---

### POST /auth/logout

Revoke the current access token. Adds the token JTI to the Valkey blocklist.

**Auth**: Bearer token required.

**Response** `204 No Content`

---

### GET /auth/me

Get the authenticated user's profile.

**Auth**: Bearer token or API key.

**Response** `200 OK` — same schema as `/auth/register` response.

---

### PUT /auth/me

Update the authenticated user's profile.

**Request body** (all fields optional)
```json
{
  "full_name": "Jane Doe",
  "company": "New Corp"
}
```

**Response** `200 OK` — updated user profile.

---

### POST /auth/api-keys

Create an API key. The raw key is only returned once.

**Auth**: Bearer token.

**Request body**
```json
{
  "name": "CI Pipeline",
  "scopes": ["envelopes:write", "envelopes:send"],
  "expires_at": "2027-01-01T00:00:00Z"
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | Yes | Label for the key |
| `scopes` | array | No | Defaults to `["*"]` (all scopes) |
| `expires_at` | datetime | No | ISO 8601 UTC; null = never expires |

**Response** `201 Created`
```json
{
  "id": "01926...",
  "name": "CI Pipeline",
  "key": "ds_key_Abc123...",
  "key_prefix": "ds_key_A",
  "scopes": ["envelopes:write", "envelopes:send"],
  "is_active": true,
  "last_used_at": null,
  "expires_at": "2027-01-01T00:00:00Z",
  "created_at": "2026-03-28T12:00:00Z"
}
```

The `key` field is only present on the creation response and cannot be retrieved again.

---

### GET /auth/api-keys

List the authenticated user's API keys. Does not return key values.

**Response** `200 OK` — array of key objects (same as above, without `key`).

---

### DELETE /auth/api-keys/{key_id}

Revoke an API key by setting `is_active = false`.

**Response** `204 No Content`

**Errors**: `404 Not Found`

---

## Envelopes

### POST /envelopes

Create a new envelope. Envelopes start in `created` status.

**Auth**: Bearer token or API key with `write` or `envelopes:write` scope.

**Request body**
```json
{
  "title": "Service Agreement",
  "message": "Please review and sign at your earliest convenience.",
  "expires_at": "2026-04-30T00:00:00Z"
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `title` | string | Yes | Max 500 characters |
| `message` | string | No | Shown to all recipients |
| `expires_at` | datetime | No | Envelope-level expiry |

**Response** `201 Created`
```json
{
  "id": "01926...",
  "user_id": "01925...",
  "title": "Service Agreement",
  "message": "Please review and sign at your earliest convenience.",
  "status": "created",
  "voided_reason": null,
  "expires_at": "2026-04-30T00:00:00Z",
  "completed_at": null,
  "created_at": "2026-03-28T12:00:00Z",
  "updated_at": "2026-03-28T12:00:00Z"
}
```

---

### GET /envelopes

List the authenticated user's envelopes. Supports filtering, search, and pagination.

**Query parameters**

| Parameter | Type | Notes |
|-----------|------|-------|
| `status` | string | Filter by envelope status |
| `search` | string | Case-insensitive title search |
| `page` | integer | Page number (default 1) |
| `page_size` | integer | Results per page (1–100, default 20) |

**Response** `200 OK`
```json
{
  "items": [ /* array of envelope objects */ ],
  "total": 42,
  "page": 1,
  "page_size": 20
}
```

---

### GET /envelopes/{envelope_id}

Get a single envelope.

**Response** `200 OK` — envelope object.

**Errors**: `404 Not Found`

---

### PUT /envelopes/{envelope_id}

Update an envelope. Only allowed when `status = created`.

**Request body** (all fields optional)
```json
{
  "title": "Updated Title",
  "message": "New message",
  "expires_at": "2026-05-01T00:00:00Z"
}
```

**Response** `200 OK` — updated envelope.

**Errors**: `400 Bad Request` — envelope already sent.

---

### DELETE /envelopes/{envelope_id}

Delete an envelope. Only allowed when `status = created`.

**Auth**: API key requires `write` or `envelopes:delete` scope.

**Response** `204 No Content`

**Errors**: `400 Bad Request` — envelope already sent.

---

### POST /envelopes/{envelope_id}/send

Send an envelope to all recipients. Validates that the envelope has at least one document, one signer recipient, and all required fields are placed.

**Auth**: API key requires `write` or `envelopes:send` scope.

**Response** `200 OK`
```json
{
  "id": "01926...",
  "status": "sent",
  "message": "Envelope sent successfully"
}
```

**Errors**: `400 Bad Request`
```json
{
  "detail": {
    "errors": [
      "Envelope must have at least one document",
      "Envelope must have at least one signer recipient"
    ]
  }
}
```

---

### POST /envelopes/{envelope_id}/void

Void an envelope. Allowed from `sent`, `delivered`, or `signed` status.

**Auth**: API key requires `write` or `envelopes:void` scope.

**Request body**
```json
{
  "reason": "Contract terms changed"
}
```

**Response** `200 OK` — updated envelope with `status = voided` and `voided_reason` set.

---

### POST /envelopes/{envelope_id}/resend

Regenerate signing tokens and resend invitation emails to recipients who have not yet signed. Allowed from `sent` or `delivered` status.

**Response** `200 OK`
```json
{
  "id": "01926...",
  "status": "sent",
  "message": "Signing emails resent"
}
```

---

### GET /envelopes/{envelope_id}/audit-trail

Retrieve the append-only audit trail for an envelope.

**Response** `200 OK`
```json
[
  {
    "id": "01926...",
    "event_type": "envelope.created",
    "description": "Envelope 'Service Agreement' created",
    "ip_address": "203.0.113.5",
    "user_agent": "curl/8.1.0",
    "metadata": null,
    "created_at": "2026-03-28T12:00:00Z"
  }
]
```

**Event types**: `envelope.created`, `envelope.sent`, `envelope.voided`, `envelope.completed`, `recipient.email_sent`, `recipient.document_viewed`, `recipient.field_completed`, `recipient.signed`, `recipient.declined`

---

### GET /envelopes/{envelope_id}/certificate

Download the certificate of completion PDF. Only available when `status = completed`.

**Response** `200 OK` — PDF file download (`application/pdf`)

---

### GET /envelopes/{envelope_id}/combined

Download the completed document with embedded signatures. Only available when `status = completed`.

**Response** `200 OK` — PDF file download (`application/pdf`)

---

## Documents

### POST /envelopes/{envelope_id}/documents

Upload a PDF document to an envelope. Only allowed when `status = created`.

**Content-Type**: `multipart/form-data`

| Field | Type | Notes |
|-------|------|-------|
| `file` | file | PDF only (magic bytes validated). Max `MAX_DOCUMENT_SIZE_MB` MB (default 25 MB). |

Page rendering (PDF to PNG) is enqueued as a Celery task and runs asynchronously. The `page_count` will be 0 until rendering completes.

**Response** `201 Created`
```json
{
  "id": "01926...",
  "envelope_id": "01925...",
  "filename": "contract.pdf",
  "content_type": "application/pdf",
  "size_bytes": 102400,
  "page_count": 0,
  "display_order": 0,
  "created_at": "2026-03-28T12:00:00Z"
}
```

**Errors**: `400 Bad Request` — non-PDF file, file too large, or max documents exceeded.

---

### GET /envelopes/{envelope_id}/documents

List all documents in an envelope, ordered by `display_order`.

**Response** `200 OK` — array of document objects.

---

### GET /envelopes/{envelope_id}/documents/{doc_id}

Get a single document.

**Response** `200 OK` — document object.

---

### GET /envelopes/{envelope_id}/documents/{doc_id}/download

Download the original PDF.

**Response** `200 OK` — PDF file download.

---

### DELETE /envelopes/{envelope_id}/documents/{doc_id}

Delete a document. Only allowed when `status = created`.

**Response** `204 No Content`

---

### GET /envelopes/{envelope_id}/documents/{doc_id}/pages

List rendered page image URLs for a document. `page_count` must be greater than 0.

**Response** `200 OK`
```json
[
  {
    "page_number": 1,
    "image_url": "/api/v1/envelopes/{id}/documents/{doc_id}/pages/1"
  }
]
```

---

### GET /envelopes/{envelope_id}/documents/{doc_id}/pages/{page_number}

Get a rendered page image.

**Response** `200 OK` — PNG image (`image/png`)

---

## Recipients

### POST /envelopes/{envelope_id}/recipients

Add one or more recipients to an envelope. Accepts a single object or an array. Only allowed when `status = created`.

**Request body** (single or array)
```json
{
  "name": "Bob Jones",
  "email": "bob@example.com",
  "role": "signer",
  "routing_order": 1
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | Yes | |
| `email` | string | Yes | Valid email address |
| `role` | string | No | `signer` (default), `cc`, `in_person_signer` |
| `routing_order` | integer | No | Default 1. Recipients with the same order sign in parallel; lower numbers sign first. |

**Response** `201 Created` — array of recipient objects
```json
[
  {
    "id": "01926...",
    "envelope_id": "01925...",
    "name": "Bob Jones",
    "email": "bob@example.com",
    "role": "signer",
    "routing_order": 1,
    "status": "created",
    "signed_at": null,
    "declined_at": null,
    "created_at": "2026-03-28T12:00:00Z"
  }
]
```

---

### GET /envelopes/{envelope_id}/recipients

List all recipients, ordered by `routing_order` then `created_at`.

**Response** `200 OK` — array of recipient objects.

---

### PUT /envelopes/{envelope_id}/recipients/{recipient_id}

Update a recipient. Only allowed when `status = created`.

**Request body** (all optional)
```json
{
  "name": "Robert Jones",
  "email": "robert@example.com",
  "role": "signer",
  "routing_order": 2
}
```

**Response** `200 OK` — updated recipient.

---

### DELETE /envelopes/{envelope_id}/recipients/{recipient_id}

Remove a recipient. Only allowed when `status = created`.

**Response** `204 No Content`

---

## Fields

Fields use percentage-based coordinates (0–100) relative to page dimensions.

### POST /envelopes/{envelope_id}/documents/{doc_id}/fields

Add one or more fields to a document. Accepts a single object or an array. Only allowed when `status = created`.

**Request body** (single or array)
```json
{
  "recipient_id": "01926...",
  "type": "signature",
  "page_number": 1,
  "x_position": 60.0,
  "y_position": 85.0,
  "width": 25.0,
  "height": 5.0,
  "is_required": true,
  "placeholder": null,
  "validation_rule": null,
  "dropdown_options": null
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `recipient_id` | UUID | Yes | Must belong to this envelope |
| `type` | string | Yes | `signature`, `initials`, `date_signed`, `text`, `checkbox`, `dropdown` |
| `page_number` | integer | Yes | 1-based |
| `x_position` | float | Yes | 0–100 (% from left) |
| `y_position` | float | Yes | 0–100 (% from top) |
| `width` | float | Yes | 0–100 (% of page width) |
| `height` | float | Yes | 0–100 (% of page height) |
| `is_required` | boolean | No | Default `true` |
| `placeholder` | string | No | Hint text shown to signer |
| `validation_rule` | string | No | Regex pattern for `text` fields |
| `dropdown_options` | array | No | String options for `dropdown` fields |

**Response** `201 Created` — array of field objects.

---

### GET /envelopes/{envelope_id}/documents/{doc_id}/fields

List all fields on a document, ordered by `page_number` then `y_position`.

**Response** `200 OK` — array of field objects.

---

### PUT /envelopes/{envelope_id}/documents/{doc_id}/fields/{field_id}

Update a field's position, size, or properties. Only allowed when `status = created`.

**Response** `200 OK` — updated field.

---

### DELETE /envelopes/{envelope_id}/documents/{doc_id}/fields/{field_id}

Remove a field. Only allowed when `status = created`.

**Response** `204 No Content`

---

## Signing (Recipient-Facing)

These endpoints use a signing token in the URL path rather than a `Authorization` header. The token is delivered via email and is valid for `SIGNING_TOKEN_EXPIRY_HOURS` (default 72 hours).

### GET /signing/{token}

Get the signing session. Marks the recipient as `delivered` on first call.

**Response** `200 OK`
```json
{
  "envelope": {
    "id": "01925...",
    "title": "Service Agreement",
    "message": "Please review and sign.",
    "status": "delivered"
  },
  "recipient": {
    "id": "01926...",
    "name": "Bob Jones",
    "email": "bob@example.com",
    "status": "delivered"
  },
  "documents": [
    {
      "id": "01927...",
      "filename": "contract.pdf",
      "page_count": 3,
      "pages": [
        {
          "page_number": 1,
          "image_url": "/api/v1/signing/{token}/documents/{doc_id}/pages/1"
        }
      ],
      "fields": [
        {
          "id": "01928...",
          "type": "signature",
          "page_number": 1,
          "x_position": 60.0,
          "y_position": 85.0,
          "width": 25.0,
          "height": 5.0,
          "is_required": true,
          "placeholder": null,
          "dropdown_options": null,
          "value": null,
          "completed_at": null
        }
      ]
    }
  ]
}
```

**Errors**: `404 Not Found` — invalid token. `403 Forbidden` — token expired, already used, or recipient has declined/voided.

---

### GET /signing/{token}/documents/{doc_id}/pages

List page image URLs for a document within a signing session.

**Response** `200 OK` — array of page objects (same as document pages endpoint).

---

### GET /signing/{token}/documents/{doc_id}/pages/{page_number}

Get a page image within a signing session.

**Response** `200 OK` — PNG image.

---

### PUT /signing/{token}/fields/{field_id}

Submit a value for a field.

**Request body**
```json
{
  "value": "Bob Jones"
}
```

For `signature` and `initials` fields, `value` is the typed name (stored as text) or a base64-encoded image data URI.
For `date_signed`, the server fills the value automatically.
For `checkbox`, `value` is `"true"` or `"false"`.
For `dropdown`, `value` must be one of `dropdown_options`.

**Response** `200 OK` — updated field object with `value` and `completed_at` set.

**Errors**: `400 Bad Request` — value fails `validation_rule` or is not in `dropdown_options`. `404 Not Found` — field not assigned to this recipient.

---

### POST /signing/{token}/complete

Complete signing. Validates all required fields have values.

**Response** `200 OK`
```json
{
  "status": "signed",
  "message": "Thank you for signing!",
  "envelope_complete": false
}
```

`envelope_complete` is `true` when all signers have signed, which triggers the finalization Celery task (PDF overlay + certificate generation).

The signing token is invalidated after this call.

**Errors**: `400 Bad Request`
```json
{
  "detail": {
    "errors": ["Required field 'signature' on page 1 is not completed"]
  }
}
```

---

### POST /signing/{token}/decline

Decline to sign. Sets recipient status to `declined` and notifies the sender.

**Query parameters**

| Parameter | Type | Notes |
|-----------|------|-------|
| `reason` | string | Optional decline reason |

**Response** `200 OK`
```json
{
  "status": "declined",
  "message": "You have declined to sign this document."
}
```

---

## Templates

Templates store reusable envelope configurations. Recipients are defined as role placeholders (e.g., "Signer 1") rather than specific people.

### POST /templates

Create a template.

**Request body**
```json
{
  "name": "Standard NDA",
  "description": "Non-disclosure agreement for new vendors"
}
```

**Response** `201 Created`
```json
{
  "id": "01926...",
  "user_id": "01925...",
  "name": "Standard NDA",
  "description": "Non-disclosure agreement for new vendors",
  "is_active": true,
  "created_at": "2026-03-28T12:00:00Z",
  "updated_at": "2026-03-28T12:00:00Z"
}
```

---

### GET /templates

List all templates owned by the authenticated user.

**Response** `200 OK` — array of template objects.

---

### GET /templates/{template_id}

Get a template with its documents, recipients, and fields.

**Response** `200 OK` — template object with nested `documents`, `recipients`, `fields`.

---

### PUT /templates/{template_id}

Update template name or description.

**Response** `200 OK` — updated template.

---

### DELETE /templates/{template_id}

Delete a template.

**Response** `204 No Content`

---

### POST /templates/{template_id}/documents

Upload a PDF document to a template.

**Content-Type**: `multipart/form-data`

Same validation as envelope document upload.

**Response** `201 Created` — template document object.

---

### POST /templates/{template_id}/recipients

Add a recipient role placeholder.

**Request body**
```json
{
  "role_name": "Signer 1",
  "role": "signer",
  "routing_order": 1
}
```

**Response** `201 Created` — template recipient object.

---

### POST /templates/{template_id}/documents/{doc_id}/fields

Add fields to a template document.

Same schema as envelope fields, but `recipient_id` refers to a `TemplateRecipient` ID.

**Response** `201 Created` — array of template field objects.

---

### POST /templates/{template_id}/create-envelope

Instantiate an envelope from a template. Copies documents, recipient placeholders, and fields. The returned envelope is in `created` status and requires real recipient details to be provided.

**Request body**
```json
{
  "title": "NDA for Acme Corp",
  "message": "Please sign the NDA before our kickoff call.",
  "recipients": [
    {
      "role_name": "Signer 1",
      "name": "Alice Chen",
      "email": "alice@acme.com"
    }
  ]
}
```

**Response** `201 Created` — envelope object.

**Errors**: `400 Bad Request` — missing recipient mapping for a defined role, template has no documents.

---

## PowerForms

PowerForms are publicly accessible signing links backed by a template. Anyone with the link can fill in their details and trigger envelope creation.

### POST /powerforms

Create a PowerForm.

**Request body**
```json
{
  "name": "Vendor NDA",
  "template_id": "01926...",
  "slug": "vendor-nda",
  "is_active": true,
  "max_uses": 100
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | Yes | Display name |
| `template_id` | UUID | Yes | Must be owned by the authenticated user |
| `slug` | string | Yes | URL-safe identifier; must be globally unique |
| `is_active` | boolean | No | Default `true` |
| `max_uses` | integer | No | null = unlimited |

**Response** `201 Created` — PowerForm object including `public_url`.

**Errors**: `409 Conflict` — slug already in use.

---

### GET /powerforms

List the authenticated user's PowerForms.

**Response** `200 OK` — array of PowerForm objects.

---

### GET /powerforms/{id} / PUT /powerforms/{id} / DELETE /powerforms/{id}

Standard CRUD. `DELETE` returns `204 No Content`.

---

### GET /p/{slug}

Public endpoint. Returns a server-rendered HTML form for the signer to fill in their name and email.

**Response** `200 OK` — HTML page

**Errors**: `404 Not Found` — slug not found or PowerForm inactive. `410 Gone` — max_uses reached.

---

### POST /p/{slug}

Public endpoint. Submit the PowerForm signer details. Creates an envelope from the linked template and redirects the browser to the signing experience.

**Request body** (form-encoded or JSON)
```json
{
  "signers": [
    {
      "role_name": "Signer 1",
      "name": "Bob Jones",
      "email": "bob@example.com"
    }
  ]
}
```

**Response** `302 Redirect` — redirects to `/sign/{token}` for the first signer.

---

## Webhooks

Webhooks deliver real-time event notifications to your server via HTTP POST. Payloads are signed with HMAC-SHA256.

### POST /webhooks

Register a webhook endpoint.

**Auth**: API key requires `write` or `webhooks:write` scope.

**Request body**
```json
{
  "url": "https://your-server.com/hooks/dataseal",
  "events": ["envelope.completed", "envelope.voided"],
  "is_active": true
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `url` | string | Yes | Must be a public HTTPS or HTTP URL. Private/internal IPs are blocked. |
| `events` | array | Yes | Event types to subscribe to. Use `["*"]` for all events. |
| `is_active` | boolean | No | Default `true` |

**Valid event types**: `envelope.created`, `envelope.sent`, `envelope.delivered`, `envelope.signed`, `envelope.completed`, `envelope.voided`, `envelope.declined`, `recipient.sent`, `recipient.delivered`, `recipient.signed`, `recipient.declined`, `*`

**Response** `201 Created`
```json
{
  "id": "01926...",
  "url": "https://your-server.com/hooks/dataseal",
  "events": ["envelope.completed", "envelope.voided"],
  "is_active": true,
  "created_at": "2026-03-28T12:00:00Z",
  "updated_at": "2026-03-28T12:00:00Z"
}
```

The webhook secret (used for HMAC signing) is generated automatically and is not returned in the response. Use the signature header to verify deliveries.

---

### GET /webhooks

List all webhook endpoints.

**Response** `200 OK` — array of webhook objects.

---

### GET /webhooks/{webhook_id}

Get a single webhook endpoint.

**Response** `200 OK` — webhook object.

---

### PUT /webhooks/{webhook_id}

Update a webhook endpoint.

**Auth**: API key requires `write` or `webhooks:write` scope.

**Request body** (all optional)
```json
{
  "url": "https://new-server.com/hooks/dataseal",
  "events": ["*"],
  "is_active": false
}
```

**Response** `200 OK` — updated webhook.

---

### DELETE /webhooks/{webhook_id}

Delete a webhook endpoint.

**Auth**: API key requires `write` or `webhooks:delete` scope.

**Response** `204 No Content`

---

### GET /webhooks/{webhook_id}/deliveries

List delivery attempts for a webhook endpoint, newest first.

**Query parameters**: `page` (default 1), `page_size` (1–100, default 20)

**Response** `200 OK`
```json
[
  {
    "id": "01926...",
    "webhook_endpoint_id": "01925...",
    "envelope_id": "01924...",
    "event_type": "envelope.completed",
    "payload": { "event": "envelope.completed", "..." },
    "response_status": 200,
    "response_body": "OK",
    "attempt_count": 1,
    "status": "delivered",
    "next_retry_at": null,
    "created_at": "2026-03-28T12:00:00Z"
  }
]
```

**Delivery statuses**: `pending`, `delivered`, `failed`

---

### POST /webhooks/{webhook_id}/test

Send a test delivery to verify connectivity.

**Response** `200 OK`
```json
{
  "message": "Test webhook delivery enqueued",
  "delivery_id": "01926..."
}
```

---

### Webhook payload format

```json
{
  "event": "envelope.completed",
  "timestamp": "2026-03-28T12:00:00Z",
  "envelope_id": "01926...",
  "data": {
    "envelope": { /* envelope object */ },
    "recipient": { /* recipient object, if applicable */ }
  }
}
```

### Verifying webhook signatures

DataSeal signs every delivery with HMAC-SHA256. Verify the signature header:

```python
import hashlib
import hmac

def verify_signature(payload: bytes, signature_header: str, secret: str) -> bool:
    expected = "sha256=" + hmac.new(
        secret.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)
```

The signature is in the `X-DataSeal-Signature` request header.

Deliveries are retried up to 5 times with exponential backoff (1 s, 2 s, 4 s, 8 s, 16 s) on non-2xx responses or network errors.

---

## OAuth 2.0

DataSeal supports OAuth 2.0 Authorization Code Grant and JWT Bearer Grant.

### POST /oauth/apps

Register an OAuth application.

**Request body**
```json
{
  "name": "My Integration",
  "redirect_uris": ["https://myapp.com/callback"],
  "scopes": ["envelopes:read", "envelopes:write"]
}
```

**Response** `201 Created`
```json
{
  "id": "01926...",
  "name": "My Integration",
  "client_id": "abc123...",
  "client_secret": "xyz789...",
  "redirect_uris": ["https://myapp.com/callback"],
  "scopes": ["envelopes:read", "envelopes:write"],
  "is_active": true,
  "created_at": "2026-03-28T12:00:00Z"
}
```

`client_secret` is shown once and cannot be retrieved again.

---

### GET /oauth/apps

List the authenticated user's OAuth applications.

---

### GET /oauth/apps/{app_id}

Get an OAuth application.

---

### DELETE /oauth/apps/{app_id}

Delete an OAuth application.

**Response** `204 No Content`

---

### GET /oauth/authorize

Authorization endpoint. Renders a consent page for the Authorization Code Grant flow.

**Query parameters**

| Parameter | Required | Notes |
|-----------|----------|-------|
| `client_id` | Yes | |
| `redirect_uri` | Yes | Must match a registered redirect URI |
| `scope` | Yes | Space-separated list of requested scopes |
| `response_type` | Yes | Must be `code` |
| `state` | No | Recommended for CSRF protection |

**Response** `200 OK` — HTML consent page

On user approval: redirects to `redirect_uri?code=<auth_code>&state=<state>`
On denial: redirects to `redirect_uri?error=access_denied&state=<state>`

---

### POST /oauth/token

Exchange an authorization code or JWT assertion for tokens.

**Content-Type**: `application/x-www-form-urlencoded`

**Authorization Code Grant**
```
grant_type=authorization_code
&code=<auth_code>
&redirect_uri=https://myapp.com/callback
&client_id=abc123
&client_secret=xyz789
```

**JWT Bearer Grant**
```
grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer
&assertion=<signed_jwt>
&client_id=abc123
```

**Response** `200 OK`
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 900,
  "scope": "envelopes:read envelopes:write"
}
```

---

### POST /oauth/revoke

Revoke a token (RFC 7009). Always returns 200 regardless of token validity.

**Content-Type**: `application/x-www-form-urlencoded`

```
token=<access_or_refresh_token>
```

**Response** `200 OK`

---

## Health Check

### GET /health

Check service health. Does not require authentication.

**Response** `200 OK` (all healthy)
```json
{
  "status": "ok",
  "db": "ok",
  "valkey": "ok"
}
```

**Response** `503 Service Unavailable` (degraded)
```json
{
  "status": "degraded",
  "db": "error",
  "valkey": "ok"
}
```

---

## Common Error Responses

| Status | Meaning |
|--------|---------|
| `400 Bad Request` | Invalid request body, validation failure, or illegal state transition |
| `401 Unauthorized` | Missing or invalid authentication token |
| `403 Forbidden` | Authenticated but insufficient permissions or account deactivated |
| `404 Not Found` | Resource does not exist or does not belong to the authenticated user |
| `409 Conflict` | Unique constraint violation (duplicate email, slug, etc.) |
| `422 Unprocessable Entity` | Pydantic validation error (schema mismatch) |

All error responses include a `detail` field:
```json
{
  "detail": "Email already registered"
}
```

Or with multiple errors:
```json
{
  "detail": {
    "errors": [
      "Envelope must have at least one document",
      "Envelope must have at least one signer recipient"
    ]
  }
}
```
