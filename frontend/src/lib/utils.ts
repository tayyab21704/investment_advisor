// ─── Investment Council — Formatting Utilities ───────────────────────────────

/**
 * Merge class names (lightweight clsx-compatible helper).
 * Supports strings, conditionals, and undefined/null.
 */
export function cn(...classes: (string | boolean | null | undefined)[]): string {
    return classes.filter(Boolean).join(' ');
}


/**
 * Format a number as Indian Rupees (₹1,23,456.78)
 */
export function formatINR(n: number | null | undefined): string {
    if (n == null || isNaN(n)) return '—';
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    }).format(n);
}

/**
 * Format a crore value compactly (₹1.23L Cr or ₹8,450 Cr)
 */
export function formatCr(n: number | null | undefined): string {
    if (n == null || isNaN(n)) return '—';
    if (n >= 100000) {
        return `₹${(n / 100000).toFixed(2)}L Cr`;
    }
    if (n >= 1000) {
        return `₹${n.toLocaleString('en-IN', { maximumFractionDigits: 0 })} Cr`;
    }
    return `₹${n.toFixed(2)} Cr`;
}

/**
 * Format a percentage with sign (+1.24% or -0.83%)
 */
export function formatPct(n: number | null | undefined, decimals = 2): string {
    if (n == null || isNaN(n)) return '—';
    const sign = n >= 0 ? '+' : '';
    return `${sign}${n.toFixed(decimals)}%`;
}

/**
 * Return a Tailwind CSS text color class based on the sign of a number.
 */
export function pctColor(n: number | null | undefined): string {
    if (n == null || isNaN(n)) return 'text-[#888888]';
    if (n > 0) return 'text-[#22c55e]';
    if (n < 0) return 'text-[#ef4444]';
    return 'text-[#888888]';
}

/**
 * Format a large number compactly (volume etc.): 1.2M, 45.3K
 */
export function formatVolume(n: number | null | undefined): string {
    if (n == null || isNaN(n)) return '—';
    if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
    if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
    return String(n);
}

/**
 * Format a date string to a readable label (eg. "22 Feb" or "22 Feb 2025")
 */
export function formatDate(ts: string, includeYear = false): string {
    try {
        const d = new Date(ts);
        const opts: Intl.DateTimeFormatOptions = { day: '2-digit', month: 'short' };
        if (includeYear) opts.year = 'numeric';
        return d.toLocaleDateString('en-IN', opts);
    } catch {
        return ts;
    }
}

/**
 * Format IST time string to "HH:MM:SS"
 */
export function formatTime(ts: string): string {
    try {
        const d = new Date(ts);
        return d.toLocaleTimeString('en-IN', {
            hour: '2-digit', minute: '2-digit', second: '2-digit',
            hour12: false, timeZone: 'Asia/Kolkata',
        });
    } catch {
        return ts;
    }
}

/**
 * Clamp a number between min and max.
 */
export function clamp(val: number, min: number, max: number): number {
    return Math.max(min, Math.min(max, val));
}
