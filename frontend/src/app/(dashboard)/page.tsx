'use client';

import { useState } from 'react';
import IndexCards from '@/components/dashboard/IndexCard';
import MarketChart from '@/components/dashboard/MarketChart';
import SectorHeatmap from '@/components/dashboard/SectorHeatmap';
import TopMovers from '@/components/dashboard/TopMovers';

export default function DashboardPage() {
  const [chartAsset, setChartAsset] = useState({
    symbol: '^NSEI',
    label: 'NIFTY 50'
  });

  return (
    <div className="px-6 py-5 max-w-[1600px] mx-auto space-y-5">
      {/* Row 1 — Index Cards */}
      <section className="animate-fade-up" style={{ animationDelay: '0ms' }}>
        <IndexCards
          activeSymbol={chartAsset.symbol}
          onSelect={(symbol, label) => setChartAsset({ symbol, label })}
        />
      </section>

      {/* Row 2 — Chart + Sidebar */}
      <div
        className="grid gap-5 animate-fade-up"
        style={{
          gridTemplateColumns: '1fr 380px',
          animationDelay: '80ms',
        }}
      >
        {/* Market Chart */}
        <MarketChart symbol={chartAsset.symbol} label={chartAsset.label} />

        {/* Right Sidebar */}
        <div className="flex flex-col gap-5">
          <SectorHeatmap />
          <TopMovers />
        </div>
      </div>
    </div>
  );
}
