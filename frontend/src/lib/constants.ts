import type { FieldType, EnvelopeStatus } from '../api/types';

export const FIELD_TYPE_LABELS: Record<FieldType, string> = {
  signature: 'Signature',
  initials: 'Initials',
  date_signed: 'Date Signed',
  text: 'Text',
  checkbox: 'Checkbox',
  dropdown: 'Dropdown',
};

export const FIELD_DEFAULT_SIZES: Record<FieldType, { width: number; height: number }> = {
  signature: { width: 20, height: 6 },
  initials: { width: 10, height: 6 },
  date_signed: { width: 15, height: 4 },
  text: { width: 20, height: 4 },
  checkbox: { width: 3, height: 3 },
  dropdown: { width: 20, height: 4 },
};

export const STATUS_COLORS: Record<EnvelopeStatus, { bg: string; text: string }> = {
  created: { bg: 'bg-gray-100', text: 'text-gray-700' },
  sent: { bg: 'bg-blue-100', text: 'text-blue-700' },
  delivered: { bg: 'bg-indigo-100', text: 'text-indigo-700' },
  signed: { bg: 'bg-amber-100', text: 'text-amber-700' },
  completed: { bg: 'bg-green-100', text: 'text-green-700' },
  voided: { bg: 'bg-red-100', text: 'text-red-700' },
  declined: { bg: 'bg-orange-100', text: 'text-orange-700' },
};

export const RECIPIENT_COLORS = [
  '#3b82f6', // blue
  '#10b981', // emerald
  '#f59e0b', // amber
  '#ef4444', // red
  '#8b5cf6', // violet
  '#ec4899', // pink
  '#06b6d4', // cyan
  '#84cc16', // lime
];

export const MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024; // 25 MB
export const ACCEPTED_FILE_TYPES = ['application/pdf'];
export const DEBOUNCE_MS = 300;
export const PAGE_SIZE = 20;

export const WEBHOOK_EVENT_TYPES = [
  'envelope.sent',
  'envelope.delivered',
  'envelope.completed',
  'envelope.voided',
  'envelope.declined',
  'recipient.signed',
  'recipient.declined',
];

export const API_KEY_SCOPES = [
  '*',
  'read:envelopes',
  'write:envelopes',
  'read:templates',
  'write:templates',
  'read:webhooks',
  'write:webhooks',
];
