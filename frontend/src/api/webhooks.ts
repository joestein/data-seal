import apiClient from './client';
import type { WebhookEndpoint, WebhookCreate, WebhookUpdate, WebhookDelivery } from './types';

export const listWebhooks = (): Promise<WebhookEndpoint[]> =>
  apiClient.get('/webhooks').then((r) => r.data);

export const getWebhook = (id: string): Promise<WebhookEndpoint> =>
  apiClient.get(`/webhooks/${id}`).then((r) => r.data);

export const createWebhook = (data: WebhookCreate): Promise<WebhookEndpoint> =>
  apiClient.post('/webhooks', data).then((r) => r.data);

export const updateWebhook = (id: string, data: WebhookUpdate): Promise<WebhookEndpoint> =>
  apiClient.put(`/webhooks/${id}`, data).then((r) => r.data);

export const deleteWebhook = (id: string): Promise<void> =>
  apiClient.delete(`/webhooks/${id}`);

export const testWebhook = (id: string): Promise<{ message: string }> =>
  apiClient.post(`/webhooks/${id}/test`).then((r) => r.data);

export const listDeliveries = (
  webhookId: string,
  params?: { page?: number; page_size?: number },
): Promise<WebhookDelivery[]> =>
  apiClient.get(`/webhooks/${webhookId}/deliveries`, { params }).then((r) => r.data);
