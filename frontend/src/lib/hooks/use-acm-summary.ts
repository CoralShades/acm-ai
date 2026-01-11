/**
 * Hook to fetch ACM summary/stats for the dashboard
 * This is a convenience wrapper around useACMStats for dashboard use
 */

import { useACMStats } from './use-acm';

export interface ACMSummary {
  highRisk: number;
  mediumRisk: number;
  lowRisk: number;
  totalRecords: number;
  buildingCount: number;
  roomCount: number;
}

/**
 * Hook to fetch ACM summary statistics for the dashboard
 * Returns normalized field names for easier use in dashboard components
 */
export function useACMSummary() {
  const query = useACMStats();

  return {
    ...query,
    data: query.data
      ? {
          highRisk: query.data.high_risk_count,
          mediumRisk: query.data.medium_risk_count,
          lowRisk: query.data.low_risk_count,
          totalRecords: query.data.total_records,
          buildingCount: query.data.building_count,
          roomCount: query.data.room_count,
          // Also keep original fields for RiskChart
          high_risk_count: query.data.high_risk_count,
          medium_risk_count: query.data.medium_risk_count,
          low_risk_count: query.data.low_risk_count,
        }
      : undefined,
  };
}
