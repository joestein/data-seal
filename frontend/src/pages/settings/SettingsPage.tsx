import { useState } from 'react';
import { Save, Plus, Trash2, Copy, Key, User, Globe } from 'lucide-react';
import { Button } from '../../components/common/Button';
import { Input } from '../../components/common/Input';
import { Modal } from '../../components/common/Modal';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { Badge } from '../../components/common/Badge';
import { ConfirmDialog } from '../../components/common/ConfirmDialog';
import { useProfile, useUpdateProfile, useApiKeys, useCreateApiKey, useRevokeApiKey } from '../../hooks/useAuth';
import { listOAuthApps, createOAuthApp, deleteOAuthApp } from '../../api/oauth';
import { formatDateTime, copyToClipboard } from '../../lib/utils';
import { API_KEY_SCOPES } from '../../lib/constants';
import { useUiStore } from '../../stores/uiStore';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { OAuthAppCreate } from '../../api/types';

type Tab = 'profile' | 'apikeys' | 'oauth';

export function SettingsPage() {
  const [tab, setTab] = useState<Tab>('profile');

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold text-gray-900">Settings</h1>
      <div className="mb-6 border-b border-gray-200">
        <div className="flex gap-6">
          {([
            { key: 'profile' as Tab, label: 'Profile', icon: User },
            { key: 'apikeys' as Tab, label: 'API Keys', icon: Key },
            { key: 'oauth' as Tab, label: 'OAuth Apps', icon: Globe },
          ]).map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={`flex items-center gap-2 border-b-2 pb-3 text-sm font-medium transition-colors ${
                tab === key
                  ? 'border-brand-600 text-brand-700'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <Icon className="h-4 w-4" />
              {label}
            </button>
          ))}
        </div>
      </div>

      {tab === 'profile' && <ProfileTab />}
      {tab === 'apikeys' && <ApiKeysTab />}
      {tab === 'oauth' && <OAuthTab />}
    </div>
  );
}

function ProfileTab() {
  const { data: profile, isLoading } = useProfile();
  const updateProfile = useUpdateProfile();
  const { addToast } = useUiStore();
  const [fullName, setFullName] = useState('');
  const [company, setCompany] = useState('');
  const [initialized, setInitialized] = useState(false);

  if (isLoading || !profile) return <LoadingSpinner className="py-8" />;

  if (!initialized) {
    setFullName(profile.full_name);
    setCompany(profile.company ?? '');
    setInitialized(true);
  }

  const handleSave = () => {
    updateProfile.mutate(
      { full_name: fullName, company: company || null },
      { onSuccess: () => addToast({ type: 'success', message: 'Profile updated' }) },
    );
  };

  return (
    <div className="max-w-lg rounded-lg border border-gray-200 bg-white p-6">
      <div className="space-y-4">
        <Input label="Email" value={profile.email} disabled />
        <Input label="Full Name" value={fullName} onChange={(e) => setFullName(e.target.value)} />
        <Input label="Company" value={company} onChange={(e) => setCompany(e.target.value)} />
        <p className="text-xs text-gray-500">
          Account created: {formatDateTime(profile.created_at)}
        </p>
        <Button onClick={handleSave} loading={updateProfile.isPending}>
          <Save className="mr-1 h-4 w-4" /> Save
        </Button>
      </div>
    </div>
  );
}

function ApiKeysTab() {
  const { data: keys, isLoading } = useApiKeys();
  const createKey = useCreateApiKey();
  const revokeKey = useRevokeApiKey();
  const { addToast } = useUiStore();

  const [showCreate, setShowCreate] = useState(false);
  const [keyName, setKeyName] = useState('');
  const [scopes, setScopes] = useState<string[]>(['*']);
  const [createdKey, setCreatedKey] = useState<string | null>(null);
  const [revokeId, setRevokeId] = useState<string | null>(null);

  const toggleScope = (scope: string) => {
    setScopes((prev) => prev.includes(scope) ? prev.filter((s) => s !== scope) : [...prev, scope]);
  };

  const handleCreate = () => {
    createKey.mutate(
      { name: keyName, scopes },
      {
        onSuccess: (result) => {
          setShowCreate(false);
          setCreatedKey(result.key);
          setKeyName('');
          setScopes(['*']);
        },
      },
    );
  };

  if (isLoading) return <LoadingSpinner className="py-8" />;

  return (
    <div>
      <div className="mb-4 flex justify-end">
        <Button onClick={() => setShowCreate(true)}>
          <Plus className="mr-1 h-4 w-4" /> Create Key
        </Button>
      </div>

      {(keys ?? []).length === 0 ? (
        <p className="py-8 text-center text-sm text-gray-500">No API keys.</p>
      ) : (
        <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Prefix</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Scopes</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Last Used</th>
                <th className="px-6 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {(keys ?? []).map((k) => (
                <tr key={k.id}>
                  <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-gray-900">{k.name}</td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm font-mono text-gray-500">{k.key_prefix}...</td>
                  <td className="px-6 py-4">
                    <div className="flex flex-wrap gap-1">
                      {k.scopes.map((s) => <Badge key={s}>{s}</Badge>)}
                    </div>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                    {k.last_used_at ? formatDateTime(k.last_used_at) : 'Never'}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-right">
                    <button
                      onClick={() => setRevokeId(k.id)}
                      className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-red-600"
                      aria-label="Revoke"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Create API Key">
        <div className="space-y-4">
          <Input label="Key Name" value={keyName} onChange={(e) => setKeyName(e.target.value)} placeholder="e.g., CI Pipeline" />
          <div>
            <label className="mb-2 block text-sm font-medium text-gray-700">Scopes</label>
            {API_KEY_SCOPES.map((scope) => (
              <label key={scope} className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={scopes.includes(scope)}
                  onChange={() => toggleScope(scope)}
                  className="h-4 w-4 rounded border-gray-300 text-brand-600"
                />
                <span className="text-sm text-gray-700">{scope}</span>
              </label>
            ))}
          </div>
          <div className="flex justify-end gap-3">
            <Button variant="secondary" onClick={() => setShowCreate(false)}>Cancel</Button>
            <Button onClick={handleCreate} disabled={!keyName.trim()} loading={createKey.isPending}>Create</Button>
          </div>
        </div>
      </Modal>

      <Modal open={!!createdKey} onClose={() => setCreatedKey(null)} title="API Key Created" size="md">
        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            Copy this key now. It will not be shown again.
          </p>
          <div className="flex items-center gap-2 rounded-lg bg-gray-100 p-3 font-mono text-sm break-all">
            {createdKey}
            <button
              onClick={() => {
                if (createdKey) copyToClipboard(createdKey);
                addToast({ type: 'info', message: 'Copied!' });
              }}
              className="flex-shrink-0 rounded p-1 hover:bg-gray-200"
            >
              <Copy className="h-4 w-4" />
            </button>
          </div>
          <div className="flex justify-end">
            <Button onClick={() => setCreatedKey(null)}>Done</Button>
          </div>
        </div>
      </Modal>

      <ConfirmDialog
        open={!!revokeId}
        onClose={() => setRevokeId(null)}
        onConfirm={() => { if (revokeId) revokeKey.mutate(revokeId); setRevokeId(null); }}
        title="Revoke API Key"
        message="This key will stop working immediately."
        confirmLabel="Revoke"
        loading={revokeKey.isPending}
      />
    </div>
  );
}

function OAuthTab() {
  const queryClient = useQueryClient();
  const { addToast } = useUiStore();
  const { data: apps, isLoading } = useQuery({
    queryKey: ['oauthApps'],
    queryFn: listOAuthApps,
  });

  const createMutation = useMutation({
    mutationFn: (data: OAuthAppCreate) => createOAuthApp(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['oauthApps'] }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteOAuthApp(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['oauthApps'] }),
  });

  const [showCreate, setShowCreate] = useState(false);
  const [appName, setAppName] = useState('');
  const [redirectUris, setRedirectUris] = useState('');
  const [appScopes, setAppScopes] = useState('');
  const [createdSecret, setCreatedSecret] = useState<string | null>(null);
  const [deleteId, setDeleteId] = useState<string | null>(null);

  const handleCreate = () => {
    createMutation.mutate(
      {
        name: appName,
        redirect_uris: redirectUris.split('\n').filter(Boolean),
        scopes: appScopes.split(',').map((s) => s.trim()).filter(Boolean),
      },
      {
        onSuccess: (app) => {
          setShowCreate(false);
          setCreatedSecret(app.client_secret);
          setAppName('');
          setRedirectUris('');
          setAppScopes('');
        },
      },
    );
  };

  if (isLoading) return <LoadingSpinner className="py-8" />;

  return (
    <div>
      <div className="mb-4 flex justify-end">
        <Button onClick={() => setShowCreate(true)}>
          <Plus className="mr-1 h-4 w-4" /> Create App
        </Button>
      </div>

      {(apps ?? []).length === 0 ? (
        <p className="py-8 text-center text-sm text-gray-500">No OAuth apps.</p>
      ) : (
        <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Client ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Redirect URIs</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Created</th>
                <th className="px-6 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {(apps ?? []).map((app) => (
                <tr key={app.id}>
                  <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-gray-900">{app.name}</td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm font-mono text-gray-500">{app.client_id}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{app.redirect_uris.join(', ')}</td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">{formatDateTime(app.created_at)}</td>
                  <td className="whitespace-nowrap px-6 py-4 text-right">
                    <button
                      onClick={() => setDeleteId(app.id)}
                      className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-red-600"
                      aria-label="Delete"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Create OAuth App" size="lg">
        <div className="space-y-4">
          <Input label="App Name" value={appName} onChange={(e) => setAppName(e.target.value)} placeholder="My App" />
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Redirect URIs (one per line)</label>
            <textarea
              className="input-field"
              rows={3}
              value={redirectUris}
              onChange={(e) => setRedirectUris(e.target.value)}
              placeholder="https://myapp.com/callback"
            />
          </div>
          <Input
            label="Scopes (comma-separated)"
            value={appScopes}
            onChange={(e) => setAppScopes(e.target.value)}
            placeholder="read:envelopes, write:envelopes"
          />
          <div className="flex justify-end gap-3">
            <Button variant="secondary" onClick={() => setShowCreate(false)}>Cancel</Button>
            <Button onClick={handleCreate} disabled={!appName.trim() || !redirectUris.trim()} loading={createMutation.isPending}>Create</Button>
          </div>
        </div>
      </Modal>

      <Modal open={!!createdSecret} onClose={() => setCreatedSecret(null)} title="OAuth App Created" size="md">
        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            Copy this client secret now. It will not be shown again.
          </p>
          <div className="flex items-center gap-2 rounded-lg bg-gray-100 p-3 font-mono text-sm break-all">
            {createdSecret}
            <button
              onClick={() => {
                if (createdSecret) copyToClipboard(createdSecret);
                addToast({ type: 'info', message: 'Copied!' });
              }}
              className="flex-shrink-0 rounded p-1 hover:bg-gray-200"
            >
              <Copy className="h-4 w-4" />
            </button>
          </div>
          <div className="flex justify-end">
            <Button onClick={() => setCreatedSecret(null)}>Done</Button>
          </div>
        </div>
      </Modal>

      <ConfirmDialog
        open={!!deleteId}
        onClose={() => setDeleteId(null)}
        onConfirm={() => { if (deleteId) deleteMutation.mutate(deleteId); setDeleteId(null); }}
        title="Delete OAuth App"
        message="This app and all its tokens will be revoked."
        confirmLabel="Delete"
        loading={deleteMutation.isPending}
      />
    </div>
  );
}
