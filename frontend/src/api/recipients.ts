import apiClient from './client';
import type { Recipient, RecipientCreate, RecipientUpdate } from './types';

export const listRecipients = (envelopeId: string): Promise<Recipient[]> =>
  apiClient.get(`/envelopes/${envelopeId}/recipients`).then((r) => r.data);

export const addRecipient = (envelopeId: string, data: RecipientCreate): Promise<Recipient> =>
  apiClient.post(`/envelopes/${envelopeId}/recipients`, data).then((r) => r.data);

export const updateRecipient = (
  envelopeId: string,
  recipientId: string,
  data: RecipientUpdate,
): Promise<Recipient> =>
  apiClient.put(`/envelopes/${envelopeId}/recipients/${recipientId}`, data).then((r) => r.data);

export const deleteRecipient = (envelopeId: string, recipientId: string): Promise<void> =>
  apiClient.delete(`/envelopes/${envelopeId}/recipients/${recipientId}`);
