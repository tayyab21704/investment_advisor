'use client';

type Regime = 'BULLISH' | 'BEARISH' | 'NEUTRAL';

interface RegimeBadgeProps {
    regime: Regime;
    confidence?: number | null;
    size?: 'xs' | 'sm' | 'md';
}

const styles: Record<Regime, string> = {
    BULLISH:
        'bg-positive-dim text-positive border border-positive/20',
    BEARISH:
        'bg-negative-dim text-negative border border-negative/20',
    NEUTRAL:
        'bg-bg-elevated text-text-secondary border border-border-default',
};

export default function RegimeBadge({ regime, confidence, size = 'xs' }: RegimeBadgeProps) {
    const textSize = size === 'xs' ? 'text-[9px]' : size === 'sm' ? 'text-[11px]' : 'text-xs px-2 py-1';
    return (
        <span
            className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md font-mono font-semibold tracking-widest uppercase ${textSize} ${styles[regime]}`}
        >
            {regime}
            {confidence != null && (
                <span className="opacity-60 normal-case tracking-normal">
                    {Math.round(confidence * 100)}%
                </span>
            )}
        </span>
    );
}
