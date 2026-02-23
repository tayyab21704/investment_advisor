'use client';

import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { formatPct } from '@/lib/utils';

interface ChangeLabelProps {
    value: number | null | undefined;
    showArrow?: boolean;
    size?: 'xs' | 'sm' | 'md' | 'lg';
    /** If true, renders absolute value + % separately */
    absolute?: number | null;
}

const sizeMap = {
    xs: 'text-[10px]',
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base font-semibold',
};

const iconSizeMap = {
    xs: 12,
    sm: 12,
    md: 14,
    lg: 16,
};

export default function ChangeLabel({
    value,
    showArrow = true,
    size = 'sm',
    absolute,
}: ChangeLabelProps) {
    if (value == null || isNaN(value)) {
        return <span className="text-[#888888] text-xs font-mono">—</span>;
    }

    const isPositive = value > 0;
    const isNegative = value < 0;
    const color = isPositive ? '#22c55e' : isNegative ? '#ef4444' : '#888888';
    const Icon = isPositive ? TrendingUp : isNegative ? TrendingDown : Minus;
    const iconSize = iconSizeMap[size];

    return (
        <span
            className={`inline-flex items-center gap-0.5 font-mono ${sizeMap[size]}`}
            style={{ color }}
        >
            {showArrow && <Icon size={iconSize} strokeWidth={2} />}
            {absolute != null && (
                <span className="mr-0.5">{absolute > 0 ? '+' : ''}{absolute.toFixed(2)}</span>
            )}
            <span>{formatPct(value)}</span>
        </span>
    );
}
