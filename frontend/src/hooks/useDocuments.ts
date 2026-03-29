import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import * as documentsApi from '../api/documents';

export function useDocuments(envelopeId: string) {
  return useQuery({
    queryKey: ['envelopes', envelopeId, 'documents'],
    queryFn: () => documentsApi.listDocuments(envelopeId),
    enabled: !!envelopeId,
  });
}

export function useDocument(envelopeId: string, docId: string) {
  return useQuery({
    queryKey: ['envelopes', envelopeId, 'documents', docId],
    queryFn: () => documentsApi.getDocument(envelopeId, docId),
    enabled: !!envelopeId && !!docId,
  });
}

export function useUploadDocument(envelopeId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => documentsApi.uploadDocument(envelopeId, file),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['envelopes', envelopeId, 'documents'],
      });
    },
  });
}

export function useDeleteDocument(envelopeId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (docId: string) => documentsApi.deleteDocument(envelopeId, docId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['envelopes', envelopeId, 'documents'],
      });
    },
  });
}

export function useDocumentPages(envelopeId: string, docId: string) {
  return useQuery({
    queryKey: ['envelopes', envelopeId, 'documents', docId, 'pages'],
    queryFn: () => documentsApi.getDocumentPages(envelopeId, docId),
    enabled: !!envelopeId && !!docId,
  });
}
