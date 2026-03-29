import apiClient from './client';
import type { PowerForm, PowerFormCreate, PowerFormUpdate } from './types';

export const listPowerForms = (): Promise<PowerForm[]> =>
  apiClient.get('/powerforms').then((r) => r.data);

export const getPowerForm = (id: string): Promise<PowerForm> =>
  apiClient.get(`/powerforms/${id}`).then((r) => r.data);

export const createPowerForm = (data: PowerFormCreate): Promise<PowerForm> =>
  apiClient.post('/powerforms', data).then((r) => r.data);

export const updatePowerForm = (id: string, data: PowerFormUpdate): Promise<PowerForm> =>
  apiClient.put(`/powerforms/${id}`, data).then((r) => r.data);

export const deletePowerForm = (id: string): Promise<void> =>
  apiClient.delete(`/powerforms/${id}`);
