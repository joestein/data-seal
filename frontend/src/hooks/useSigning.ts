import { useMutation, useQuery } from '@tanstack/react-query';
import * as signingApi from '../api/signing';

export function useSigningSession(token: string) {
  return useQuery({
    queryKey: ['signing', token],
    queryFn: () => signingApi.getSigningSession(token),
    enabled: !!token,
    retry: false,
  });
}

export function useSubmitFieldValue(token: string) {
  return useMutation({
    mutationFn: ({ fieldId, value }: { fieldId: string; value: string }) =>
      signingApi.submitFieldValue(token, fieldId, value),
  });
}

export function useCompleteSigning(token: string) {
  return useMutation({
    mutationFn: () => signingApi.completeSigning(token),
  });
}

export function useDeclineSigning(token: string) {
  return useMutation({
    mutationFn: (reason?: string) => signingApi.declineSigning(token, reason),
  });
}
