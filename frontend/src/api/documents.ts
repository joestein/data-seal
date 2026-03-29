import apiClient from './client';
import type { Document, PageResponse } from './types';

export const uploadDocument = (envelopeId: string, file: File): Promise<Document> => {
  const form = new FormData();
  form.append('file', file);
  return apiClient
    .post(`/envelopes/${envelopeId}/documents`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    .then((r) => r.data);
};

export const listDocuments = (envelopeId: string): Promise<Document[]> =>
  apiClient.get(`/envelopes/${envelopeId}/documents`).then((r) => r.data);

export const getDocument = (envelopeId: string, docId: string): Promise<Document> =>
  apiClient.get(`/envelopes/${envelopeId}/documents/${docId}`).then((r) => r.data);

export const deleteDocument = (envelopeId: string, docId: string): Promise<void> =>
  apiClient.delete(`/envelopes/${envelopeId}/documents/${docId}`);

export const getDocumentPages = (envelopeId: string, docId: string): Promise<PageResponse[]> =>
  apiClient.get(`/envelopes/${envelopeId}/documents/${docId}/pages`).then((r) => r.data);

export const getPageImageUrl = (envelopeId: string, docId: string, pageNum: number): string =>
  `/api/v1/envelopes/${envelopeId}/documents/${docId}/pages/${pageNum}`;
