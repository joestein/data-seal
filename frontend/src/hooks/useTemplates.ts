import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import * as templatesApi from '../api/templates';
import type { TemplateCreate, TemplateUpdate, CreateEnvelopeFromTemplate } from '../api/types';

export function useTemplates() {
  return useQuery({
    queryKey: ['templates'],
    queryFn: templatesApi.listTemplates,
  });
}

export function useTemplate(id: string) {
  return useQuery({
    queryKey: ['templates', id],
    queryFn: () => templatesApi.getTemplate(id),
    enabled: !!id,
  });
}

export function useCreateTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: TemplateCreate) => templatesApi.createTemplate(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
    },
  });
}

export function useUpdateTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: TemplateUpdate }) =>
      templatesApi.updateTemplate(id, data),
    onSuccess: (_data, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['templates', id] });
      queryClient.invalidateQueries({ queryKey: ['templates'] });
    },
  });
}

export function useDeleteTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => templatesApi.deleteTemplate(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
    },
  });
}

export function useTemplateDocuments(templateId: string) {
  return useQuery({
    queryKey: ['templates', templateId, 'documents'],
    queryFn: () => templatesApi.listTemplateDocuments(templateId),
    enabled: !!templateId,
  });
}

export function useTemplateRecipients(templateId: string) {
  return useQuery({
    queryKey: ['templates', templateId, 'recipients'],
    queryFn: () => templatesApi.listTemplateRecipients(templateId),
    enabled: !!templateId,
  });
}

export function useCreateEnvelopeFromTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ templateId, data }: { templateId: string; data: CreateEnvelopeFromTemplate }) =>
      templatesApi.createEnvelopeFromTemplate(templateId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['envelopes'] });
    },
  });
}
