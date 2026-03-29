import { describe, it, expect, beforeEach } from 'vitest';
import { useAuthStore } from '../../stores/authStore';
import type { User } from '../../api/types';

const mockUser: User = {
  id: 'user-123',
  email: 'test@example.com',
  full_name: 'Test User',
  company: null,
  is_active: true,
  is_verified: true,
  created_at: '2024-01-01T00:00:00Z',
};

beforeEach(() => {
  // Reset store state before each test
  useAuthStore.setState({
    accessToken: null,
    refreshToken: null,
    user: null,
    isAuthenticated: false,
  });
});

describe('authStore', () => {
  describe('initial state', () => {
    it('should have null tokens and user by default', () => {
      const state = useAuthStore.getState();
      expect(state.accessToken).toBeNull();
      expect(state.refreshToken).toBeNull();
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
    });
  });

  describe('login', () => {
    it('should set tokens and user, mark as authenticated', () => {
      useAuthStore.getState().login('access-token', 'refresh-token', mockUser);
      const state = useAuthStore.getState();
      expect(state.accessToken).toBe('access-token');
      expect(state.refreshToken).toBe('refresh-token');
      expect(state.user).toEqual(mockUser);
      expect(state.isAuthenticated).toBe(true);
    });
  });

  describe('logout', () => {
    it('should clear all auth state', () => {
      // First log in
      useAuthStore.getState().login('access-token', 'refresh-token', mockUser);
      // Then log out
      useAuthStore.getState().logout();
      const state = useAuthStore.getState();
      expect(state.accessToken).toBeNull();
      expect(state.refreshToken).toBeNull();
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
    });
  });

  describe('setTokens', () => {
    it('should update tokens and mark as authenticated', () => {
      useAuthStore.getState().setTokens('new-access', 'new-refresh');
      const state = useAuthStore.getState();
      expect(state.accessToken).toBe('new-access');
      expect(state.refreshToken).toBe('new-refresh');
      expect(state.isAuthenticated).toBe(true);
    });

    it('should not change user when only updating tokens', () => {
      useAuthStore.setState({ user: mockUser });
      useAuthStore.getState().setTokens('new-access', 'new-refresh');
      expect(useAuthStore.getState().user).toEqual(mockUser);
    });
  });

  describe('setUser', () => {
    it('should update only the user field', () => {
      useAuthStore.setState({ accessToken: 'token', refreshToken: 'refresh', isAuthenticated: true });
      useAuthStore.getState().setUser(mockUser);
      const state = useAuthStore.getState();
      expect(state.user).toEqual(mockUser);
      expect(state.accessToken).toBe('token');
    });
  });
});
