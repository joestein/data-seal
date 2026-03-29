import apiClient from './client';
import type { OAuthApp, OAuthAppCreate, OAuthAppCreated } from './types';

export const listOAuthApps = (): Promise<OAuthApp[]> =>
  apiClient.get('/oauth/apps').then((r) => r.data);

export const createOAuthApp = (data: OAuthAppCreate): Promise<OAuthAppCreated> =>
  apiClient.post('/oauth/apps', data).then((r) => r.data);

export const deleteOAuthApp = (id: string): Promise<void> =>
  apiClient.delete(`/oauth/apps/${id}`);
