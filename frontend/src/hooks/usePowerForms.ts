import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import * as powerformsApi from '../api/powerforms';
import type { PowerFormCreate, PowerFormUpdate } from '../api/types';

export function usePowerForms() {
  return useQuery({
    queryKey: ['powerforms'],
    queryFn: powerformsApi.listPowerForms,
  });
}

export function useCreatePowerForm() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: PowerFormCreate) => powerformsApi.createPowerForm(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['powerforms'] });
    },
  });
}

export function useUpdatePowerForm() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: PowerFormUpdate }) =>
      powerformsApi.updatePowerForm(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['powerforms'] });
    },
  });
}

export function useDeletePowerForm() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => powerformsApi.deletePowerForm(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['powerforms'] });
    },
  });
}
