import React, { useState } from 'react'; // Import useState
import Navbar from '../components/layout/Navbar';
import PredictionForm from '../features/dashboard/PredictionForm';
import HistoryChart from '../features/dashboard/HistoryChart';

const DashboardPage = () => {
  // 1. Add a state variable to act as a "refresh key"
  const [refreshKey, setRefreshKey] = useState(0);

  // 2. Create a function to update the key
  const handlePredictionSuccess = () => {
    setRefreshKey(prevKey => prevKey + 1);
  };

  return (
    <div>
      <Navbar />
      <main style={{ padding: '2rem' }}>
        <h2>Dashboard</h2>
        <div style={{ display: 'flex', gap: '2rem' }}>
          {/* 3. Pass the function down to the form */}
          <PredictionForm onPredictionSuccess={handlePredictionSuccess} />
          
          {/* 4. Pass the key down to the chart */}
          <HistoryChart machineId="M-185" key={refreshKey} />
        </div>
      </main>
    </div>
  );
};

export default DashboardPage;