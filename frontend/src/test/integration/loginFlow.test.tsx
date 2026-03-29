/**
 * Integration test: Login flow
 *
 * Tests the full login interaction: form submit → API call → store update → navigation.
 * API calls are intercepted with axios-mock-adapter (no real network).
 */
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import MockAdapter from 'axios-mock-adapter';

import { LoginPage } from '../../pages/auth/LoginPage';
import { useAuthStore } from '../../stores/authStore';
import { useUiStore } from '../../stores/uiStore';
import apiClient from '../../api/client';
import { ROUTES } from '../../lib/routes';

const mockUser = {
  id: 'user-abc',
  email: 'user@example.com',
  full_name: 'Jane Doe',
  company: 'ACME',
  is_active: true,
  is_verified: true,
  created_at: '2024-01-01T00:00:00Z',
};

const mockTokens = {
  access_token: 'access-jwt',
  refresh_token: 'refresh-jwt',
  token_type: 'bearer',
  expires_in: 900,
};

let mock: MockAdapter;
let queryClient: QueryClient;

beforeEach(() => {
  mock = new MockAdapter(apiClient);
  queryClient = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  useAuthStore.setState({ accessToken: null, refreshToken: null, user: null, isAuthenticated: false });
  useUiStore.setState({ toasts: [] });
});

afterEach(() => {
  mock.restore();
});

function renderLoginPage() {
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[ROUTES.LOGIN]}>
        <Routes>
          <Route path={ROUTES.LOGIN} element={<LoginPage />} />
          <Route path={ROUTES.DASHBOARD} element={<div>Dashboard Page</div>} />
          <Route path={ROUTES.REGISTER} element={<div>Register Page</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('Login flow (integration)', () => {
  it('should render the login form', () => {
    renderLoginPage();
    expect(screen.getByRole('heading', { name: /sign in/i })).toBeInTheDocument();
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('should show validation errors for empty submit', async () => {
    const user = userEvent.setup();
    renderLoginPage();
    await user.click(screen.getByRole('button', { name: /sign in/i }));
    await waitFor(() => {
      expect(screen.getByText('Enter a valid email')).toBeInTheDocument();
    });
  });

  it('should show password required error when password is empty', async () => {
    const user = userEvent.setup();
    renderLoginPage();
    await user.type(screen.getByLabelText('Email'), 'user@example.com');
    // Leave password empty and submit
    await user.click(screen.getByRole('button', { name: /sign in/i }));
    await waitFor(() => {
      expect(screen.getByText('Password is required')).toBeInTheDocument();
    });
  });

  it('should authenticate and navigate to dashboard on successful login', async () => {
    mock.onPost('/api/v1/auth/login').reply(200, mockTokens);
    mock.onGet('/api/v1/auth/me').reply(200, mockUser);

    const user = userEvent.setup();
    renderLoginPage();

    await user.type(screen.getByLabelText('Email'), 'user@example.com');
    await user.type(screen.getByLabelText('Password'), 'correctpassword');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText('Dashboard Page')).toBeInTheDocument();
    });

    const authState = useAuthStore.getState();
    expect(authState.isAuthenticated).toBe(true);
    expect(authState.accessToken).toBe('access-jwt');
    expect(authState.user?.email).toBe('user@example.com');
  });

  it('should add error toast on failed login', async () => {
    mock.onPost('/api/v1/auth/login').reply(401, { detail: 'Invalid credentials' });

    const user = userEvent.setup();
    renderLoginPage();

    await user.type(screen.getByLabelText('Email'), 'user@example.com');
    await user.type(screen.getByLabelText('Password'), 'wrongpassword');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      const toasts = useUiStore.getState().toasts;
      expect(toasts.some((t) => t.type === 'error')).toBe(true);
    });

    // Should stay on login page
    expect(screen.queryByText('Dashboard Page')).not.toBeInTheDocument();
  });

  it('should show loading spinner during login request', async () => {
    // Delay the response
    mock.onPost('/api/v1/auth/login').reply(() => new Promise((resolve) => setTimeout(() => resolve([200, mockTokens]), 200)));
    mock.onGet('/api/v1/auth/me').reply(200, mockUser);

    const user = userEvent.setup();
    renderLoginPage();

    await user.type(screen.getByLabelText('Email'), 'user@example.com');
    await user.type(screen.getByLabelText('Password'), 'password');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    // Button should be disabled while loading
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /sign in/i })).toBeDisabled();
    });
  });

  it('should have a link to the register page', () => {
    renderLoginPage();
    expect(screen.getByRole('link', { name: 'Register' })).toBeInTheDocument();
  });

  it('should navigate to register page when register link is clicked', async () => {
    const user = userEvent.setup();
    renderLoginPage();
    await user.click(screen.getByRole('link', { name: 'Register' }));
    expect(screen.getByText('Register Page')).toBeInTheDocument();
  });
});
