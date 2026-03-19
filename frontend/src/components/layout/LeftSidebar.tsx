"use client";

import Link from 'next/link';
import { LayoutDashboard, PieChart, Users, Settings, LogOut } from 'lucide-react';
import { signOut } from 'next-auth/react';

export default function LeftSidebar() {
  return (
    <aside className="w-[72px] lg:w-[84px] h-screen bg-bg-surface border-r border-border-subtle flex flex-col items-center py-6 shrink-0 z-20 hidden md:flex">
      {/* Brand Icon */}
      <div className="w-10 h-10 rounded-full bg-bg-elevated border border-border-default flex items-center justify-center mb-6">
        <div className="w-5 h-5 rounded-full bg-text-primary"></div>
        <div className="w-5 h-2 rounded-b-full bg-text-primary absolute bottom-[50%] opacity-50"></div>
      </div>

      {/* Nav Actions */}
      <nav className="flex-1 w-full flex flex-col items-center gap-3 mt-4">
        {/* Active item example */}
        <Link
          href="/"
          className="w-14 h-[60px] rounded-xl bg-bg-elevated border border-border-default text-text-primary flex flex-col items-center justify-center relative shadow-sm gap-1 group"
        >
          <LayoutDashboard size={20} className="text-primary" />
          <span className="text-[9px] font-medium tracking-wide">Home</span>
          {/* Active indicator */}
          <div className="absolute right-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-border-accent rounded-l-md"></div>
        </Link>

        {/* Inactive items */}
        <Link href="/portfolio" className="w-14 h-[60px] rounded-xl text-text-muted hover:text-text-primary hover:bg-bg-elevated transition-colors flex flex-col items-center justify-center gap-1">
          <PieChart size={20} />
          <span className="text-[9px] font-medium tracking-wide">Portfolio</span>
        </Link>
        <Link href="/council" className="w-14 h-[60px] rounded-xl text-text-muted hover:text-text-primary hover:bg-bg-elevated transition-colors flex flex-col items-center justify-center gap-1">
          <Users size={20} />
          <span className="text-[9px] font-medium tracking-wide">Council</span>
        </Link>
        <Link href="/profile" className="w-14 h-[60px] rounded-xl text-text-muted hover:text-text-primary hover:bg-bg-elevated transition-colors flex flex-col items-center justify-center gap-1">
          <Settings size={20} />
          <span className="text-[9px] font-medium tracking-wide">Profile</span>
        </Link>
      </nav>

      {/* Bottom Actions */}
      <div className="w-full flex flex-col items-center gap-3 mt-auto">
        <Link href="/settings" className="w-14 h-[60px] rounded-xl text-text-muted hover:text-text-primary hover:bg-bg-elevated transition-colors flex flex-col items-center justify-center gap-1">
          <Settings size={20} />
          <span className="text-[9px] font-medium tracking-wide">Settings</span>
        </Link>
        <button onClick={() => signOut({ callbackUrl: '/login' })} className="w-14 h-[52px] rounded-xl text-text-muted hover:text-negative hover:bg-negative-dim transition-colors flex flex-col items-center justify-center gap-1 border border-transparent">
          <LogOut size={20} />
          <span className="text-[9px] font-medium tracking-wide">Logout</span>
        </button>

        {/* User avatar */}
        <div className="mt-2 w-10 h-10 rounded-full bg-border-default overflow-hidden border border-border-subtle">
          <img src="https://api.dicebear.com/7.x/notionists/svg?seed=Felix&backgroundColor=CBCDFF" alt="User" className="w-full h-full object-cover" />
        </div>
      </div>
    </aside>
  );
}
