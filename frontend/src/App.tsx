import { Routes, Route } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import { ProtectedRoute } from './components/layout/ProtectedRoute';
import { ToastContainer } from './components/common/ToastContainer';

import { LoginPage } from './pages/auth/LoginPage';
import { RegisterPage } from './pages/auth/RegisterPage';
import { DashboardPage } from './pages/dashboard/DashboardPage';
import { EnvelopeCreatePage } from './pages/envelopes/EnvelopeCreatePage';
import { EnvelopeDetailPage } from './pages/envelopes/EnvelopeDetailPage';
import { SigningPage } from './pages/signing/SigningPage';
import { TemplateListPage } from './pages/templates/TemplateListPage';
import { TemplateDetailPage } from './pages/templates/TemplateDetailPage';
import { PowerFormListPage } from './pages/powerforms/PowerFormListPage';
import { WebhookListPage } from './pages/webhooks/WebhookListPage';
import { WebhookDetailPage } from './pages/webhooks/WebhookDetailPage';
import { SettingsPage } from './pages/settings/SettingsPage';

export function App() {
  return (
    <>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/sign/:token" element={<SigningPage />} />

        {/* Protected routes */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <AppShell />
            </ProtectedRoute>
          }
        >
          <Route index element={<DashboardPage />} />
          <Route path="envelopes/new" element={<EnvelopeCreatePage />} />
          <Route path="envelopes/:id" element={<EnvelopeDetailPage />} />
          <Route path="templates" element={<TemplateListPage />} />
          <Route path="templates/:id" element={<TemplateDetailPage />} />
          <Route path="powerforms" element={<PowerFormListPage />} />
          <Route path="webhooks" element={<WebhookListPage />} />
          <Route path="webhooks/:id" element={<WebhookDetailPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
      </Routes>
      <ToastContainer />
    </>
  );
}
