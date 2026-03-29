import apiClient from './client';
import type {
  Envelope,
  EnvelopeCreate,
  EnvelopeUpdate,
  EnvelopeListParams,
  EnvelopeListResponse,
  SendResponse,
  VoidRequest,
  AuditEvent,
} from './types';

export const listEnvelopes = (params: EnvelopeListParams): Promise<EnvelopeListResponse> =>
  apiClient.get('/envelopes', { params }).then((r) => r.data);

export const getEnvelope = (id: string): Promise<Envelope> =>
  apiClient.get(`/envelopes/${id}`).then((r) => r.data);

export const createEnvelope = (data: EnvelopeCreate): Promise<Envelope> =>
  apiClient.post('/envelopes', data).then((r) => r.data);

export const updateEnvelope = (id: string, data: EnvelopeUpdate): Promise<Envelope> =>
  apiClient.put(`/envelopes/${id}`, data).then((r) => r.data);

export const deleteEnvelope = (id: string): Promise<void> =>
  apiClient.delete(`/envelopes/${id}`);

export const sendEnvelope = (id: string): Promise<SendResponse> =>
  apiClient.post(`/envelopes/${id}/send`).then((r) => r.data);

export const voidEnvelope = (id: string, data: VoidRequest): Promise<Envelope> =>
  apiClient.post(`/envelopes/${id}/void`, data).then((r) => r.data);

export const resendEnvelope = (id: string): Promise<{ message: string }> =>
  apiClient.post(`/envelopes/${id}/resend`).then((r) => r.data);

export const getAuditTrail = (id: string): Promise<AuditEvent[]> =>
  apiClient.get(`/envelopes/${id}/audit-trail`).then((r) => r.data);

export const downloadCompleted = (id: string): Promise<Blob> =>
  apiClient.get(`/envelopes/${id}/download`, { responseType: 'blob' }).then((r) => r.data);

export const downloadCertificate = (id: string): Promise<Blob> =>
  apiClient.get(`/envelopes/${id}/certificate`, { responseType: 'blob' }).then((r) => r.data);
