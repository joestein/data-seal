export const ROUTES = {
  LOGIN: '/login',
  REGISTER: '/register',
  DASHBOARD: '/',
  ENVELOPE_NEW: '/envelopes/new',
  ENVELOPE_DETAIL: (id: string) => `/envelopes/${id}`,
  SIGNING: (token: string) => `/sign/${token}`,
  TEMPLATES: '/templates',
  TEMPLATE_DETAIL: (id: string) => `/templates/${id}`,
  POWERFORMS: '/powerforms',
  WEBHOOKS: '/webhooks',
  WEBHOOK_DETAIL: (id: string) => `/webhooks/${id}`,
  SETTINGS: '/settings',
} as const;
