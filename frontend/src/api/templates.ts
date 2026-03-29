import apiClient from './client';
import type {
  Template,
  TemplateCreate,
  TemplateUpdate,
  TemplateDocument,
  TemplateRecipient,
  TemplateRecipientCreate,
  TemplateField,
  TemplateFieldCreate,
  CreateEnvelopeFromTemplate,
  Envelope,
} from './types';

export const listTemplates = (): Promise<Template[]> =>
  apiClient.get('/templates').then((r) => r.data);

export const getTemplate = (id: string): Promise<Template> =>
  apiClient.get(`/templates/${id}`).then((r) => r.data);

export const createTemplate = (data: TemplateCreate): Promise<Template> =>
  apiClient.post('/templates', data).then((r) => r.data);

export const updateTemplate = (id: string, data: TemplateUpdate): Promise<Template> =>
  apiClient.put(`/templates/${id}`, data).then((r) => r.data);

export const deleteTemplate = (id: string): Promise<void> =>
  apiClient.delete(`/templates/${id}`);

// Documents
export const listTemplateDocuments = (templateId: string): Promise<TemplateDocument[]> =>
  apiClient.get(`/templates/${templateId}/documents`).then((r) => r.data);

export const uploadTemplateDocument = (templateId: string, file: File): Promise<TemplateDocument> => {
  const form = new FormData();
  form.append('file', file);
  return apiClient
    .post(`/templates/${templateId}/documents`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    .then((r) => r.data);
};

// Recipients
export const listTemplateRecipients = (templateId: string): Promise<TemplateRecipient[]> =>
  apiClient.get(`/templates/${templateId}/recipients`).then((r) => r.data);

export const addTemplateRecipient = (
  templateId: string,
  data: TemplateRecipientCreate,
): Promise<TemplateRecipient> =>
  apiClient.post(`/templates/${templateId}/recipients`, data).then((r) => r.data);

export const deleteTemplateRecipient = (
  templateId: string,
  recipientId: string,
): Promise<void> =>
  apiClient.delete(`/templates/${templateId}/recipients/${recipientId}`);

// Fields
export const listTemplateFields = (
  templateId: string,
  docId: string,
): Promise<TemplateField[]> =>
  apiClient.get(`/templates/${templateId}/documents/${docId}/fields`).then((r) => r.data);

export const addTemplateField = (
  templateId: string,
  docId: string,
  data: TemplateFieldCreate,
): Promise<TemplateField> =>
  apiClient.post(`/templates/${templateId}/documents/${docId}/fields`, data).then((r) => r.data);

export const deleteTemplateField = (
  templateId: string,
  docId: string,
  fieldId: string,
): Promise<void> =>
  apiClient.delete(`/templates/${templateId}/documents/${docId}/fields/${fieldId}`);

// Create envelope from template
export const createEnvelopeFromTemplate = (
  templateId: string,
  data: CreateEnvelopeFromTemplate,
): Promise<Envelope> =>
  apiClient.post(`/templates/${templateId}/create-envelope`, data).then((r) => r.data);
