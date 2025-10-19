import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import apiService from '../../api/apiService';
import { Prediction } from '../../types';

interface HistoryChartProps {
  machineId: string;
}

const HistoryChart: React.FC<HistoryChartProps> = ({ machineId }) => {
  const [data, setData] = useState<Prediction[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const response = await apiService.get(`/machines/${machineId}/history`);
        const formattedData = response.data.map((d: any) => ({
          ...d,
          prediction_timestamp: new Date(d.prediction_timestamp).toLocaleDateString(),
          failure_risk_percent: (d.prediction_score * 100).toFixed(2)
        }));
        setData(formattedData);
      } catch (error) {
        console.error("Failed to fetch history", error);
      } finally {
        setLoading(false);
      }
    };
    fetchHistory();
  }, [machineId]);

  if (loading) return <p>Loading chart data...</p>;

  return (
    <div style={{ border: '1px solid #ccc', padding: '1rem', flex: 2 }}>
        <h3>Failure Risk History for {machineId}</h3>
        <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="prediction_timestamp" />
                <YAxis label={{ value: 'Risk (%)', angle: -90, position: 'insideLeft' }} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="failure_risk_percent" name="Failure Risk" stroke="#8884d8" activeDot={{ r: 8 }} />
            </LineChart>
        </ResponsiveContainer>
    </div>
  );
};

export default HistoryChart;