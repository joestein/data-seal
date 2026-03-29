import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import * as webhooksApi from '../api/webhooks';
import type { WebhookCreate, WebhookUpdate } from '../api/types';

export function useWebhooks() {
  return useQuery({
    queryKey: ['webhooks'],
    queryFn: webhooksApi.listWebhooks,
  });
}

export function useWebhook(id: string) {
  return useQuery({
    queryKey: ['webhooks', id],
    queryFn: () => webhooksApi.getWebhook(id),
    enabled: !!id,
  });
}

export function useCreateWebhook() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: WebhookCreate) => webhooksApi.createWebhook(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['webhooks'] });
    },
  });
}

export function useUpdateWebhook() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: WebhookUpdate }) =>
      webhooksApi.updateWebhook(id, data),
    onSuccess: (_data, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['webhooks', id] });
      queryClient.invalidateQueries({ queryKey: ['webhooks'] });
    },
  });
}

export function useDeleteWebhook() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => webhooksApi.deleteWebhook(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['webhooks'] });
    },
  });
}

export function useTestWebhook() {
  return useMutation({
    mutationFn: (id: string) => webhooksApi.testWebhook(id),
  });
}

export function useWebhookDeliveries(webhookId: string, params?: { page?: number; page_size?: number }) {
  return useQuery({
    queryKey: ['webhooks', webhookId, 'deliveries', params],
    queryFn: () => webhooksApi.listDeliveries(webhookId, params),
    enabled: !!webhookId,
  });
}
