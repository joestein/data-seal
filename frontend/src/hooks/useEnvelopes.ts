import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import * as envelopesApi from '../api/envelopes';
import type { EnvelopeCreate, EnvelopeUpdate, EnvelopeListParams, VoidRequest } from '../api/types';

export function useEnvelopes(params: EnvelopeListParams) {
  return useQuery({
    queryKey: ['envelopes', params],
    queryFn: () => envelopesApi.listEnvelopes(params),
  });
}

export function useEnvelope(id: string) {
  return useQuery({
    queryKey: ['envelopes', id],
    queryFn: () => envelopesApi.getEnvelope(id),
    enabled: !!id,
  });
}

export function useCreateEnvelope() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: EnvelopeCreate) => envelopesApi.createEnvelope(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['envelopes'] });
    },
  });
}

export function useUpdateEnvelope() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: EnvelopeUpdate }) =>
      envelopesApi.updateEnvelope(id, data),
    onSuccess: (_data, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['envelopes', id] });
      queryClient.invalidateQueries({ queryKey: ['envelopes'] });
    },
  });
}

export function useDeleteEnvelope() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => envelopesApi.deleteEnvelope(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['envelopes'] });
    },
  });
}

export function useSendEnvelope() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => envelopesApi.sendEnvelope(id),
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: ['envelopes', id] });
      queryClient.invalidateQueries({ queryKey: ['envelopes'] });
    },
  });
}

export function useVoidEnvelope() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: VoidRequest }) =>
      envelopesApi.voidEnvelope(id, data),
    onSuccess: (_data, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['envelopes', id] });
      queryClient.invalidateQueries({ queryKey: ['envelopes'] });
    },
  });
}

export function useResendEnvelope() {
  return useMutation({
    mutationFn: (id: string) => envelopesApi.resendEnvelope(id),
  });
}

export function useAuditTrail(envelopeId: string) {
  return useQuery({
    queryKey: ['envelopes', envelopeId, 'audit'],
    queryFn: () => envelopesApi.getAuditTrail(envelopeId),
    enabled: !!envelopeId,
  });
}
