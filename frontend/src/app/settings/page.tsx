'use client';

import { Settings } from 'lucide-react';

export default function SettingsPage() {
    return (
        <div className="flex flex-col items-center justify-center h-[60vh] gap-4">
            <div
                className="w-16 h-16 rounded-2xl flex items-center justify-center"
                style={{ background: 'rgba(136,136,136,0.08)', border: '1px solid #333' }}
            >
                <Settings size={28} color="#888" />
            </div>
            <div className="text-base font-bold" style={{ color: '#e5e5e5' }}>Settings</div>
            <div className="text-sm" style={{ color: '#888' }}>
                Configuration panel coming soon.
            </div>
        </div>
    );
}
