'use client';

import { Settings } from 'lucide-react';

export default function SettingsPage() {
    return (
        <div className="flex flex-col items-center justify-center h-[60vh] gap-5">
            <div
                className="w-20 h-20 rounded-3xl flex items-center justify-center bg-bg-elevated border border-border-default shadow-lg"
            >
                <Settings size={36} className="text-text-muted animate-[spin_6s_linear_infinite]" />
            </div>
            <div className="text-xl tracking-tight font-bold text-text-primary">Settings</div>
            <div className="text-sm text-text-secondary">
                Configuration panel coming soon.
            </div>
        </div>
    );
}
