import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import * as fieldsApi from '../api/fields';
import type { FieldCreate, FieldUpdate } from '../api/types';

export function useFields(envelopeId: string, docId: string) {
  return useQuery({
    queryKey: ['envelopes', envelopeId, 'documents', docId, 'fields'],
    queryFn: () => fieldsApi.listFields(envelopeId, docId),
    enabled: !!envelopeId && !!docId,
  });
}

export function useCreateField(envelopeId: string, docId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: FieldCreate) => fieldsApi.createField(envelopeId, docId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['envelopes', envelopeId, 'documents', docId, 'fields'],
      });
    },
  });
}

export function useUpdateField(envelopeId: string, docId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ fieldId, data }: { fieldId: string; data: FieldUpdate }) =>
      fieldsApi.updateField(envelopeId, docId, fieldId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['envelopes', envelopeId, 'documents', docId, 'fields'],
      });
    },
  });
}

export function useDeleteField(envelopeId: string, docId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (fieldId: string) => fieldsApi.deleteField(envelopeId, docId, fieldId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['envelopes', envelopeId, 'documents', docId, 'fields'],
      });
    },
  });
}
