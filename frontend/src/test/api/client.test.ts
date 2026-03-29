import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';

// We need to control the stores before importing client
import { useAuthStore } from '../../stores/authStore';
import { useUiStore } from '../../stores/uiStore';

// Dynamic import so we can reset module state
let apiClient: typeof import('../../api/client').default;

// Use a fresh mock adapter per test suite
let mock: MockAdapter;

beforeEach(async () => {
  // Reset stores
  useAuthStore.setState({ accessToken: null, refreshToken: null, user: null, isAuthenticated: false });
  useUiStore.setState({ toasts: [] });

  // Re-import client to get a fresh instance
  // (vitest module cache means we get same instance, but we can reset mock)
  const mod = await import('../../api/client');
  apiClient = mod.default;
  mock = new MockAdapter(apiClient);
});

afterEach(() => {
  mock.restore();
  vi.clearAllMocks();
});

describe('API client request interceptor', () => {
  it('should attach Authorization header when access token is set', async () => {
    useAuthStore.setState({ accessToken: 'my-access-token', isAuthenticated: true });
    mock.onGet('/api/v1/test').reply((config) => {
      expect(config.headers?.Authorization).toBe('Bearer my-access-token');
      return [200, { ok: true }];
    });
    await apiClient.get('/test');
  });

  it('should not attach Authorization header when no access token', async () => {
    mock.onGet('/api/v1/test').reply((config) => {
      expect(config.headers?.Authorization).toBeUndefined();
      return [200, { ok: true }];
    });
    await apiClient.get('/test');
  });
});

describe('API client response interceptor', () => {
  it('should return successful responses as-is', async () => {
    mock.onGet('/api/v1/ping').reply(200, { pong: true });
    const response = await apiClient.get('/ping');
    expect(response.data).toEqual({ pong: true });
  });

  it('should surface string error detail as toast on non-401 error', async () => {
    mock.onPost('/api/v1/envelopes').reply(400, { detail: 'Validation failed' });
    await expect(apiClient.post('/envelopes', {})).rejects.toThrow();
    const toasts = useUiStore.getState().toasts;
    expect(toasts.some((t) => t.message === 'Validation failed')).toBe(true);
  });

  it('should surface errors object detail as joined toast message', async () => {
    mock.onPost('/api/v1/envelopes').reply(422, { detail: { errors: ['Field A is required', 'Field B is invalid'] } });
    await expect(apiClient.post('/envelopes', {})).rejects.toThrow();
    const toasts = useUiStore.getState().toasts;
    expect(toasts.some((t) => t.message === 'Field A is required, Field B is invalid')).toBe(true);
  });

  it('should add a generic error toast when no detail is present', async () => {
    mock.onGet('/api/v1/me').reply(500, {});
    await expect(apiClient.get('/me')).rejects.toThrow();
    const toasts = useUiStore.getState().toasts;
    expect(toasts.some((t) => t.message === 'An error occurred')).toBe(true);
  });
});

describe('API client 401 refresh flow', () => {
  it('should logout when 401 occurs and no refresh token is present', async () => {
    useAuthStore.setState({ accessToken: 'expired', refreshToken: null, isAuthenticated: true });
    mock.onGet('/api/v1/profile').reply(401, { detail: 'Unauthorized' });

    await expect(apiClient.get('/profile')).rejects.toThrow();
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
  });

  it('should refresh token and retry request on 401 when refresh token exists', async () => {
    useAuthStore.setState({ accessToken: 'expired-token', refreshToken: 'valid-refresh', isAuthenticated: true });

    // Set up mock: first call 401, refresh succeeds, retry succeeds
    mock.onGet('/api/v1/protected').replyOnce(401).onGet('/api/v1/protected').reply(200, { data: 'ok' });

    // Mock the vanilla axios refresh call
    const axiosMock = new MockAdapter(axios);
    axiosMock.onPost('/api/v1/auth/refresh').reply(200, {
      access_token: 'new-access',
      refresh_token: 'new-refresh',
    });

    const response = await apiClient.get('/protected');
    expect(response.data).toEqual({ data: 'ok' });
    expect(useAuthStore.getState().accessToken).toBe('new-access');

    axiosMock.restore();
  });

  it('should logout when refresh token call fails', async () => {
    useAuthStore.setState({ accessToken: 'expired', refreshToken: 'bad-refresh', isAuthenticated: true });

    mock.onGet('/api/v1/protected').reply(401);

    const axiosMock = new MockAdapter(axios);
    axiosMock.onPost('/api/v1/auth/refresh').reply(401, { detail: 'Refresh token invalid' });

    await expect(apiClient.get('/protected')).rejects.toThrow();
    expect(useAuthStore.getState().isAuthenticated).toBe(false);

    axiosMock.restore();
  });
});
