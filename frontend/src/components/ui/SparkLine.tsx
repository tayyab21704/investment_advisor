'use client';

interface SparkLineProps {
    data: number[];
    color?: string;
    width?: number;
    height?: number;
}

export default function SparkLine({
    data,
    color,
    width = 100,
    height = 30,
}: SparkLineProps) {
    if (!data || data.length < 2) return null;

    const valid = data.filter((v) => v != null && !isNaN(v));
    if (valid.length < 2) return null;

    const min = Math.min(...valid);
    const max = Math.max(...valid);
    const range = max - min || 1;

    const xStep = width / (valid.length - 1);
    const points = valid.map((v, i) => {
        const x = i * xStep;
        const y = height - ((v - min) / range) * (height * 0.85) - height * 0.075;
        return `${x.toFixed(1)},${y.toFixed(1)}`;
    });
    const polyline = points.join(' ');

    const trend = valid[valid.length - 1] >= valid[0];
    const strokeColor = color ?? (trend ? '#22c55e' : '#ef4444');

    return (
        <svg
            width={width}
            height={height}
            viewBox={`0 0 ${width} ${height}`}
            fill="none"
            style={{ overflow: 'visible' }}
            aria-hidden="true"
        >
            <polyline
                points={polyline}
                stroke={strokeColor}
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                fill="none"
            />
        </svg>
    );
}
