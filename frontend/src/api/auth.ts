import apiClient from './client';
import type {
  UserRegister,
  UserLogin,
  TokenResponse,
  User,
  UserUpdate,
  ApiKeyCreate,
  ApiKeyResponse,
  ApiKeyCreatedResponse,
} from './types';

export const register = (data: UserRegister): Promise<User> =>
  apiClient.post('/auth/register', data).then((r) => r.data);

export const login = (data: UserLogin): Promise<TokenResponse> =>
  apiClient.post('/auth/login', data).then((r) => r.data);

export const refreshToken = (refresh_token: string): Promise<TokenResponse> =>
  apiClient.post('/auth/refresh', { refresh_token }).then((r) => r.data);

export const logout = (refresh_token: string): Promise<void> =>
  apiClient.post('/auth/logout', { refresh_token });

export const getProfile = (): Promise<User> =>
  apiClient.get('/auth/me').then((r) => r.data);

export const updateProfile = (data: UserUpdate): Promise<User> =>
  apiClient.put('/auth/me', data).then((r) => r.data);

export const createApiKey = (data: ApiKeyCreate): Promise<ApiKeyCreatedResponse> =>
  apiClient.post('/auth/api-keys', data).then((r) => r.data);

export const listApiKeys = (): Promise<ApiKeyResponse[]> =>
  apiClient.get('/auth/api-keys').then((r) => r.data);

export const revokeApiKey = (id: string): Promise<void> =>
  apiClient.delete(`/auth/api-keys/${id}`);
