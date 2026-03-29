import apiClient from './client';
import type { DocumentField, FieldCreate, FieldUpdate } from './types';

export const listFields = (envelopeId: string, docId: string): Promise<DocumentField[]> =>
  apiClient.get(`/envelopes/${envelopeId}/documents/${docId}/fields`).then((r) => r.data);

export const createField = (
  envelopeId: string,
  docId: string,
  data: FieldCreate,
): Promise<DocumentField> =>
  apiClient.post(`/envelopes/${envelopeId}/documents/${docId}/fields`, data).then((r) => r.data);

export const updateField = (
  envelopeId: string,
  docId: string,
  fieldId: string,
  data: FieldUpdate,
): Promise<DocumentField> =>
  apiClient
    .put(`/envelopes/${envelopeId}/documents/${docId}/fields/${fieldId}`, data)
    .then((r) => r.data);

export const deleteField = (
  envelopeId: string,
  docId: string,
  fieldId: string,
): Promise<void> =>
  apiClient.delete(`/envelopes/${envelopeId}/documents/${docId}/fields/${fieldId}`);
