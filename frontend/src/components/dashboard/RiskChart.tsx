'use client';

import { useMemo } from 'react';

interface RiskChartProps {
  data?: {
    high_risk_count: number;
    medium_risk_count: number;
    low_risk_count: number;
  };
}

export function RiskChart({ data }: RiskChartProps) {
  const chartData = useMemo(() => {
    if (!data) return [];
    const total = data.high_risk_count + data.medium_risk_count + data.low_risk_count;
    if (total === 0) return [];

    return [
      { label: 'High', value: data.high_risk_count, percent: (data.high_risk_count / total) * 100, color: 'bg-danger-500' },
      { label: 'Medium', value: data.medium_risk_count, percent: (data.medium_risk_count / total) * 100, color: 'bg-warning-500' },
      { label: 'Low', value: data.low_risk_count, percent: (data.low_risk_count / total) * 100, color: 'bg-success-500' },
    ];
  }, [data]);

  if (chartData.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-muted-foreground">
        No ACM data available
      </div>
    );
  }

  const total = chartData.reduce((sum, item) => sum + item.value, 0);

  return (
    <div className="space-y-4">
      {/* Bar chart with accessibility */}
      <div
        className="flex h-8 rounded-lg overflow-hidden"
        role="img"
        aria-label={`Risk distribution chart: ${chartData.map((item) => `${item.label} risk ${item.value} items (${Math.round(item.percent)}%)`).join(', ')}`}
      >
        {chartData.map((item) => (
          <div
            key={item.label}
            className={`${item.color} transition-all`}
            style={{ width: `${item.percent}%` }}
            role="presentation"
            aria-hidden="true"
          />
        ))}
      </div>

      {/* Legend */}
      <div className="flex justify-between" role="list" aria-label="Risk distribution legend">
        {chartData.map((item) => (
          <div key={item.label} className="text-center" role="listitem">
            <div className={`w-3 h-3 rounded-full ${item.color} mx-auto mb-1`} aria-hidden="true" />
            <p className="text-sm font-medium">{item.value}</p>
            <p className="text-xs text-muted-foreground">{item.label}</p>
          </div>
        ))}
      </div>

      {/* Screen reader summary */}
      <p className="sr-only">
        Total of {total} ACM items: {chartData.map((item) => `${item.value} ${item.label.toLowerCase()} risk`).join(', ')}
      </p>
    </div>
  );
}
