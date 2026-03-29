import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import * as authApi from '../api/auth';
import { useAuthStore } from '../stores/authStore';
import { useUiStore } from '../stores/uiStore';
import type { UserLogin, UserRegister, UserUpdate, ApiKeyCreate } from '../api/types';

export function useProfile() {
  const { isAuthenticated } = useAuthStore();
  return useQuery({
    queryKey: ['profile'],
    queryFn: authApi.getProfile,
    enabled: isAuthenticated,
  });
}

export function useLogin() {
  const { login, setTokens } = useAuthStore();
  const { addToast } = useUiStore();
  return useMutation({
    mutationFn: async (data: UserLogin) => {
      const tokens = await authApi.login(data);
      setTokens(tokens.access_token, tokens.refresh_token);
      const user = await authApi.getProfile();
      return { tokens, user };
    },
    onSuccess: ({ tokens, user }) => {
      login(tokens.access_token, tokens.refresh_token, user);
    },
    onError: (error: unknown) => {
      const message =
        (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'Login failed. Please try again.';
      addToast({ type: 'error', message });
    },
  });
}

export function useRegister() {
  const { addToast } = useUiStore();
  return useMutation({
    mutationFn: (data: UserRegister) => authApi.register(data),
    onSuccess: () => {
      addToast({ type: 'success', message: 'Account created. Please log in.' });
    },
  });
}

export function useUpdateProfile() {
  const queryClient = useQueryClient();
  const { setUser } = useAuthStore();
  return useMutation({
    mutationFn: (data: UserUpdate) => authApi.updateProfile(data),
    onSuccess: (user) => {
      setUser(user);
      queryClient.invalidateQueries({ queryKey: ['profile'] });
    },
  });
}

export function useApiKeys() {
  return useQuery({
    queryKey: ['apiKeys'],
    queryFn: authApi.listApiKeys,
  });
}

export function useCreateApiKey() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ApiKeyCreate) => authApi.createApiKey(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['apiKeys'] });
    },
  });
}

export function useRevokeApiKey() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => authApi.revokeApiKey(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['apiKeys'] });
    },
  });
}
