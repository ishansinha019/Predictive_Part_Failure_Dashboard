import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface ReliabilityChartProps {
  data: number[]; // Array of time-to-failure days
  partId: string;
}

// Helper function to bin the data
const binData = (data: number[]) => {
  if (!data || data.length === 0) return [];

  const binSize = 100;
  const maxDays = Math.max(...data);
  const bins = [];

  for (let i = 0; i <= maxDays; i += binSize) {
    const binStart = i;
    const binEnd = i + binSize - 1;
    const count = data.filter(d => d >= binStart && d <= binEnd).length;
    
    if (count > 0) {
      bins.push({
        name: `${binStart}-${binEnd} days`,
        count: count,
      });
    }
  }
  return bins;
};

const ReliabilityChart: React.FC<ReliabilityChartProps> = ({ data, partId }) => {
  const binnedData = binData(data);

  if (binnedData.length === 0) {
    return (
      <div className="p-4 bg-slate-50 rounded-lg border border-slate-200 text-center h-full flex items-center justify-center">
        <p className="text-slate-500">No failure data available to build reliability profile for {partId}.</p>
      </div>
    );
  }

  return (
    <div className="border border-slate-200 p-6 rounded-lg shadow-sm bg-white h-full">
      <h3 className="text-xl font-semibold mb-6 text-slate-800">
        Reliability Profile for {partId}
      </h3>
      <p className="text-sm text-slate-600 mb-4 -mt-4">
        Historical failure distribution by time in service.
      </p>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={binnedData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis allowDecimals={false} label={{ value: 'Failure Count', angle: -90, position: 'insideLeft' }} />
          <Tooltip />
          <Legend />
          <Bar dataKey="count" name="Failure Count" fill="#8884d8" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default ReliabilityChart;