import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import * as recipientsApi from '../api/recipients';
import type { RecipientCreate, RecipientUpdate } from '../api/types';

export function useRecipients(envelopeId: string) {
  return useQuery({
    queryKey: ['envelopes', envelopeId, 'recipients'],
    queryFn: () => recipientsApi.listRecipients(envelopeId),
    enabled: !!envelopeId,
  });
}

export function useAddRecipient(envelopeId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: RecipientCreate) => recipientsApi.addRecipient(envelopeId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['envelopes', envelopeId, 'recipients'],
      });
    },
  });
}

export function useUpdateRecipient(envelopeId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ recipientId, data }: { recipientId: string; data: RecipientUpdate }) =>
      recipientsApi.updateRecipient(envelopeId, recipientId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['envelopes', envelopeId, 'recipients'],
      });
    },
  });
}

export function useDeleteRecipient(envelopeId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (recipientId: string) =>
      recipientsApi.deleteRecipient(envelopeId, recipientId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['envelopes', envelopeId, 'recipients'],
      });
    },
  });
}
