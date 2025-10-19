import React from 'react';
import Navbar from '../components/layout/Navbar';
import PredictionForm from '../features/dashboard/PredictionForm';
import HistoryChart from '../features/dashboard/HistoryChart';

const DashboardPage = () => {
  return (
    <div>
      <Navbar />
      <main style={{ padding: '2rem' }}>
        <h2>Dashboard</h2>
        <div style={{ display: 'flex', gap: '2rem' }}>
          <PredictionForm />
          <HistoryChart machineId="M-185" />
        </div>
      </main>
    </div>
  );
};

export default DashboardPage;