import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom'; // 1. Import useParams and Link
import Navbar from '../components/layout/Navbar';
import PredictionForm from '../features/dashboard/PredictionForm';
import HistoryChart from '../features/dashboard/HistoryChart';

const MachineDetailPage = () => {
  const [refreshKey, setRefreshKey] = useState(0);
  
  // 2. Read the 'machineId' from the URL
  const { machineId } = useParams<{ machineId: string }>();

  // 3. Handle a missing machine ID
  if (!machineId) {
    return <div>Error: No machine ID specified.</div>;
  }

  const handlePredictionSuccess = () => {
    setRefreshKey(prevKey => prevKey + 1);
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <main className="p-6 md:p-8">
        
        {/* 4. Add a "Back" link */}
        <Link to="/" className="text-blue-600 hover:underline mb-4 inline-block">
          &larr; Back to Fleet
        </Link>
        
        <h2 className="text-3xl font-bold text-slate-900 mb-6">
          Details for {machineId}
        </h2>
        
        <div className="flex flex-col lg:flex-row gap-6">
          <div className="lg:flex-1">
            {/* 5. Pass the dynamic machineId to the form */}
            <PredictionForm 
              machineId={machineId}
              onPredictionSuccess={handlePredictionSuccess} 
            />
          </div>
          <div className="lg:flex-2">
            {/* 6. Pass the dynamic machineId to the chart */}
            <HistoryChart 
              machineId={machineId} 
              key={refreshKey} 
            />
          </div>
        </div>
      </main>
    </div>
  );
};

export default MachineDetailPage;