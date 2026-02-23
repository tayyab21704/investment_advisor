'use client';

type Regime = 'BULLISH' | 'BEARISH' | 'NEUTRAL';

interface RegimeBadgeProps {
    regime: Regime;
    confidence?: number | null;
    size?: 'xs' | 'sm';
}

const styles: Record<Regime, string> = {
    BULLISH:
        'bg-[rgba(234,146,62,0.12)] text-[#ea923e] border border-[rgba(234,146,62,0.25)]',
    BEARISH:
        'bg-[rgba(239,68,68,0.12)] text-[#ef4444] border border-[rgba(239,68,68,0.2)]',
    NEUTRAL:
        'bg-[rgba(136,136,136,0.1)] text-[#888888] border border-[#333]',
};

export default function RegimeBadge({ regime, confidence, size = 'xs' }: RegimeBadgeProps) {
    const textSize = size === 'xs' ? 'text-[9px]' : 'text-[11px]';
    return (
        <span
            className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full font-mono font-semibold tracking-widest uppercase ${textSize} ${styles[regime]}`}
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
