import { cn } from '@/lib/utils';
import React from 'react';

type BadgeVariant = 'gain' | 'loss' | 'neutral' | 'info' | 'council';

interface BadgeProps {
    children: React.ReactNode;
    variant?: BadgeVariant;
    className?: string;
}

export const Badge = ({ children, variant = 'info', className }: BadgeProps) => {
    const variants = {
        gain: "text-green bg-green-dim",
        loss: "text-red bg-red-dim",
        neutral: "text-amber bg-amber-dim",
        info: "text-blue bg-blue-dim",
        council: "text-purple bg-purple-dim",
    };

    return (
        <span className={cn(
            "font-mono text-[10px] md:text-body-xs font-medium px-2 py-0.5 rounded-sm inline-flex items-center gap-1",
            variants[variant],
            className
        )}>
            {children}
        </span>
    );
};
