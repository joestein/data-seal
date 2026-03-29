import apiClient from './client';
import type { SigningSession, DocumentField } from './types';

export const getSigningSession = (token: string): Promise<SigningSession> =>
  apiClient.get(`/signing/${token}`).then((r) => r.data);

export const submitFieldValue = (
  token: string,
  fieldId: string,
  value: string,
): Promise<DocumentField> =>
  apiClient.put(`/signing/${token}/fields/${fieldId}`, { value }).then((r) => r.data);

export const completeSigning = (
  token: string,
): Promise<{ status: string; message: string; envelope_complete: boolean }> =>
  apiClient.post(`/signing/${token}/complete`).then((r) => r.data);

export const declineSigning = (
  token: string,
  reason?: string,
): Promise<{ status: string; message: string }> =>
  apiClient.post(`/signing/${token}/decline`, null, { params: { reason } }).then((r) => r.data);
