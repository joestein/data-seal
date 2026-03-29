import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  FileSignature,
  Layers,
  Zap,
  Webhook,
  Settings,
} from 'lucide-react';
import { clsx } from 'clsx';
import { ROUTES } from '../../lib/routes';

const NAV_ITEMS = [
  { to: ROUTES.DASHBOARD, label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: ROUTES.TEMPLATES, label: 'Templates', icon: Layers },
  { to: ROUTES.POWERFORMS, label: 'PowerForms', icon: Zap },
  { to: ROUTES.WEBHOOKS, label: 'Webhooks', icon: Webhook },
  { to: ROUTES.SETTINGS, label: 'Settings', icon: Settings },
];

export function Sidebar() {
  return (
    <aside className="flex h-full w-60 flex-col border-r border-gray-200 bg-white">
      <div className="flex h-16 items-center gap-2 border-b border-gray-200 px-6">
        <FileSignature className="h-7 w-7 text-brand-600" />
        <span className="text-lg font-bold text-gray-900">DataSeal</span>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-4" aria-label="Main navigation">
        {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-brand-50 text-brand-700'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900',
              )
            }
          >
            <Icon className="h-5 w-5" />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
