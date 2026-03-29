/** Mirrors backend Pydantic schemas exactly. */

// ── Auth ──

export interface UserRegister {
  email: string;
  password: string;
  full_name: string;
  company?: string | null;
}

export interface UserLogin {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface RefreshRequest {
  refresh_token: string;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  company: string | null;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface UserUpdate {
  full_name?: string | null;
  company?: string | null;
}

export interface ApiKeyCreate {
  name: string;
  scopes?: string[];
  expires_at?: string | null;
}

export interface ApiKeyResponse {
  id: string;
  name: string;
  key_prefix: string;
  scopes: string[];
  is_active: boolean;
  last_used_at: string | null;
  expires_at: string | null;
  created_at: string;
}

export interface ApiKeyCreatedResponse extends ApiKeyResponse {
  key: string;
}

// ── Envelope ──

export type EnvelopeStatus =
  | 'created'
  | 'sent'
  | 'delivered'
  | 'signed'
  | 'completed'
  | 'voided'
  | 'declined';

export interface EnvelopeCreate {
  title: string;
  message?: string | null;
  expires_at?: string | null;
}

export interface EnvelopeUpdate {
  title?: string | null;
  message?: string | null;
  expires_at?: string | null;
}

export interface Envelope {
  id: string;
  user_id: string;
  template_id: string | null;
  powerform_id: string | null;
  title: string;
  message: string | null;
  status: EnvelopeStatus;
  voided_reason: string | null;
  expires_at: string | null;
  completed_at: string | null;
  completed_hash: string | null;
  created_at: string;
  updated_at: string;
}

export interface EnvelopeListResponse {
  items: Envelope[];
  total: number;
  page: number;
  page_size: number;
}

export interface VoidRequest {
  reason: string;
}

export interface SendResponse {
  id: string;
  status: string;
  message: string;
}

// ── Document ──

export interface Document {
  id: string;
  envelope_id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  page_count: number;
  display_order: number;
  created_at: string;
}

export interface PageResponse {
  page_number: number;
  image_url: string;
}

// ── Recipient ──

export type RecipientRole = 'signer' | 'cc' | 'in_person_signer';
export type RecipientStatus = 'created' | 'sent' | 'delivered' | 'signed' | 'declined';

export interface RecipientCreate {
  name: string;
  email: string;
  role?: RecipientRole;
  routing_order?: number;
}

export interface RecipientUpdate {
  name?: string | null;
  email?: string | null;
  role?: RecipientRole | null;
  routing_order?: number | null;
}

export interface Recipient {
  id: string;
  envelope_id: string;
  name: string;
  email: string;
  role: RecipientRole;
  routing_order: number;
  status: RecipientStatus;
  signed_at: string | null;
  declined_at: string | null;
  declined_reason: string | null;
  created_at: string;
  updated_at: string;
}

// ── Document Field ──

export type FieldType =
  | 'signature'
  | 'initials'
  | 'date_signed'
  | 'text'
  | 'checkbox'
  | 'dropdown';

export interface FieldCreate {
  recipient_id: string;
  type: FieldType;
  page_number: number;
  x_position: number;
  y_position: number;
  width: number;
  height: number;
  is_required?: boolean;
  placeholder?: string | null;
  validation_rule?: string | null;
  dropdown_options?: string[] | null;
}

export interface FieldUpdate {
  page_number?: number | null;
  x_position?: number | null;
  y_position?: number | null;
  width?: number | null;
  height?: number | null;
  is_required?: boolean | null;
  placeholder?: string | null;
  validation_rule?: string | null;
  dropdown_options?: string[] | null;
}

export interface DocumentField {
  id: string;
  document_id: string;
  recipient_id: string;
  type: FieldType;
  page_number: number;
  x_position: number;
  y_position: number;
  width: number;
  height: number;
  is_required: boolean;
  placeholder: string | null;
  validation_rule: string | null;
  dropdown_options: string[] | null;
  value: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface FieldValueUpdate {
  value: string;
}

// ── Audit ──

export interface AuditEvent {
  id: string;
  event_type: string;
  description: string;
  ip_address: string | null;
  user_agent: string | null;
  metadata: Record<string, unknown> | null;
  created_at: string;
}

// ── Template ──

export interface TemplateCreate {
  name: string;
  description?: string | null;
}

export interface TemplateUpdate {
  name?: string | null;
  description?: string | null;
  is_active?: boolean | null;
}

export interface Template {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TemplateRecipientCreate {
  role_name: string;
  role?: RecipientRole;
  routing_order?: number;
}

export interface TemplateRecipient {
  id: string;
  template_id: string;
  role_name: string;
  role: RecipientRole;
  routing_order: number;
  created_at: string;
}

export interface TemplateFieldCreate {
  template_recipient_id: string;
  type: FieldType;
  page_number: number;
  x_position: number;
  y_position: number;
  width: number;
  height: number;
  is_required?: boolean;
  placeholder?: string | null;
  validation_rule?: string | null;
  dropdown_options?: string[] | null;
}

export interface TemplateField {
  id: string;
  template_document_id: string;
  template_recipient_id: string;
  type: FieldType;
  page_number: number;
  x_position: number;
  y_position: number;
  width: number;
  height: number;
  is_required: boolean;
  placeholder: string | null;
  validation_rule: string | null;
  dropdown_options: string[] | null;
  created_at: string;
}

export interface TemplateDocument {
  id: string;
  template_id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  page_count: number;
  display_order: number;
  created_at: string;
}

export interface CreateEnvelopeFromTemplate {
  recipients: Record<string, { name: string; email: string }>;
  title: string;
  message?: string | null;
}

// ── Webhook ──

export interface WebhookCreate {
  url: string;
  events: string[];
  is_active?: boolean;
}

export interface WebhookUpdate {
  url?: string | null;
  events?: string[] | null;
  is_active?: boolean | null;
}

export interface WebhookEndpoint {
  id: string;
  user_id: string;
  url: string;
  events: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface WebhookDelivery {
  id: string;
  webhook_endpoint_id: string;
  envelope_id: string;
  event_type: string;
  payload: Record<string, unknown>;
  response_status: number | null;
  response_body: string | null;
  attempt_count: number;
  max_attempts: number;
  status: string;
  created_at: string;
  updated_at: string;
}

// ── PowerForm ──

export interface PowerFormCreate {
  template_id: string;
  name: string;
  slug: string;
  is_active?: boolean;
  max_uses?: number | null;
}

export interface PowerFormUpdate {
  name?: string | null;
  is_active?: boolean | null;
  max_uses?: number | null;
}

export interface PowerForm {
  id: string;
  user_id: string;
  template_id: string;
  name: string;
  slug: string;
  is_active: boolean;
  max_uses: number | null;
  use_count: number;
  created_at: string;
  updated_at: string;
}

// ── OAuth ──

export interface OAuthAppCreate {
  name: string;
  redirect_uris: string[];
  scopes: string[];
}

export interface OAuthApp {
  id: string;
  user_id: string;
  name: string;
  client_id: string;
  redirect_uris: string[];
  scopes: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface OAuthAppCreated extends OAuthApp {
  client_secret: string;
}

// ── Signing Session ──

export interface SigningSessionDocument {
  id: string;
  filename: string;
  page_count: number;
  pages: PageResponse[];
  fields: SigningField[];
}

export interface SigningField {
  id: string;
  type: FieldType;
  page_number: number;
  x_position: number;
  y_position: number;
  width: number;
  height: number;
  is_required: boolean;
  placeholder: string | null;
  dropdown_options: string[] | null;
  value: string | null;
  completed_at: string | null;
}

export interface SigningSession {
  envelope: {
    id: string;
    title: string;
    message: string | null;
    status: string;
  };
  recipient: {
    id: string;
    name: string;
    email: string;
    status: string;
  };
  documents: SigningSessionDocument[];
}

// ── Generic ──

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface EnvelopeListParams {
  page?: number;
  page_size?: number;
  status?: EnvelopeStatus;
  search?: string;
}
