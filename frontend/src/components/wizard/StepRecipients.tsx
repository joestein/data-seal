import { useState } from 'react';
import { Plus, Trash2 } from 'lucide-react';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { useRecipients, useAddRecipient, useDeleteRecipient } from '../../hooks/useRecipients';
import { RECIPIENT_COLORS } from '../../lib/constants';
import type { RecipientRole } from '../../api/types';

interface StepRecipientsProps {
  envelopeId: string;
  onNext: () => void;
  onBack: () => void;
}

export function StepRecipients({ envelopeId, onNext, onBack }: StepRecipientsProps) {
  const { data: recipients } = useRecipients(envelopeId);
  const addRecipient = useAddRecipient(envelopeId);
  const deleteRecipient = useDeleteRecipient(envelopeId);

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [role, setRole] = useState<RecipientRole>('signer');
  const [order, setOrder] = useState(1);

  const handleAdd = () => {
    if (!name.trim() || !email.trim()) return;
    addRecipient.mutate(
      { name: name.trim(), email: email.trim(), role, routing_order: order },
      {
        onSuccess: () => {
          setName('');
          setEmail('');
          setOrder((recipients?.length ?? 0) + 2);
        },
      },
    );
  };

  const list = recipients ?? [];
  const hasSigners = list.some((r) => r.role === 'signer');

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-gray-200 p-4">
        <h3 className="mb-4 text-sm font-medium text-gray-900">Add Recipient</h3>
        <div className="grid grid-cols-12 gap-3">
          <div className="col-span-3">
            <Input
              label="Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Full name"
            />
          </div>
          <div className="col-span-3">
            <Input
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="email@example.com"
            />
          </div>
          <div className="col-span-2">
            <label className="mb-1 block text-sm font-medium text-gray-700">Role</label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value as RecipientRole)}
              className="input-field"
            >
              <option value="signer">Signer</option>
              <option value="cc">CC</option>
              <option value="in_person_signer">In-Person</option>
            </select>
          </div>
          <div className="col-span-2">
            <Input
              label="Order"
              type="number"
              min={1}
              value={order}
              onChange={(e) => setOrder(Number(e.target.value))}
            />
          </div>
          <div className="col-span-2 flex items-end">
            <Button
              onClick={handleAdd}
              loading={addRecipient.isPending}
              disabled={!name.trim() || !email.trim()}
            >
              <Plus className="mr-1 h-4 w-4" />
              Add
            </Button>
          </div>
        </div>
      </div>

      {list.length > 0 && (
        <div className="rounded-lg border border-gray-200">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Recipient</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Email</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Role</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Order</th>
                <th className="px-6 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {list.map((r, i) => (
                <tr key={r.id}>
                  <td className="whitespace-nowrap px-6 py-3">
                    <div className="flex items-center gap-2">
                      <div
                        className="h-3 w-3 rounded-full"
                        style={{ backgroundColor: RECIPIENT_COLORS[i % RECIPIENT_COLORS.length] }}
                      />
                      <span className="text-sm font-medium text-gray-900">{r.name}</span>
                    </div>
                  </td>
                  <td className="whitespace-nowrap px-6 py-3 text-sm text-gray-500">{r.email}</td>
                  <td className="whitespace-nowrap px-6 py-3 text-sm text-gray-500 capitalize">{r.role}</td>
                  <td className="whitespace-nowrap px-6 py-3 text-sm text-gray-500">{r.routing_order}</td>
                  <td className="whitespace-nowrap px-6 py-3 text-right">
                    <button
                      onClick={() => deleteRecipient.mutate(r.id)}
                      className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-red-600"
                      aria-label={`Remove ${r.name}`}
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

      <div className="flex justify-between">
        <Button variant="secondary" onClick={onBack}>
          Back
        </Button>
        <Button onClick={onNext} disabled={!hasSigners}>
          Next: Place Fields
        </Button>
      </div>
    </div>
  );
}
