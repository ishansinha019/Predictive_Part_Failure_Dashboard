import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import Navbar from '../components/layout/Navbar';
import PredictionForm from '../features/dashboard/PredictionForm';
import HistoryChart from '../features/dashboard/HistoryChart';
import ReliabilityChart from '../features/dashboard/ReliabilityChart'; // 1. Import new chart
import apiService from '../api/apiService'; // 2. Import apiService

const MachineDetailPage = () => {
  const [refreshKey, setRefreshKey] = useState(0);
  const { machineId } = useParams<{ machineId: string }>();

  // 3. Add state for the new feature
  const [currentPartId, setCurrentPartId] = useState('P-BRG-02'); // Default part
  const [partStats, setPartStats] = useState<number[]>([]);

  // 4. Add a useEffect to fetch reliability data when partId changes
  useEffect(() => {
    if (!currentPartId) return;

    const fetchPartStats = async () => {
      try {
        const response = await apiService.get(`/parts/${currentPartId}/stats`);
        setPartStats(response.data.time_to_failure_days);
      } catch (error) {
        console.error("Failed to fetch part stats", error);
        setPartStats([]); // Clear stats on error
      }
    };

    fetchPartStats();
  }, [currentPartId, refreshKey]); // Also refresh when a prediction is made

  if (!machineId) {
    return <div>Error: No machine ID specified.</div>;
  }

  const handlePredictionSuccess = () => {
    setRefreshKey(prevKey => prevKey + 1);
  };

  // 5. This handler will be passed to the PredictionForm
  const handlePartIdChange = (newPartId: string) => {
    setCurrentPartId(newPartId);
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <main className="p-6 md:p-8">
        
        <Link to="/" className="text-blue-600 hover:underline mb-4 inline-block">
          &larr; Back to Fleet
        </Link>
        
        <h2 className="text-3xl font-bold text-slate-900 mb-6">
          Details for {machineId}
        </h2>
        
        {/* Main 2-column layout */}
        <div className="flex flex-col lg:flex-row gap-6 mb-6">
          <div className="lg:flex-1">
            <PredictionForm 
              machineId={machineId}
              onPredictionSuccess={handlePredictionSuccess}
              onPartIdChange={handlePartIdChange} // 6. Pass the handler down
            />
          </div>
          <div className="lg:flex-2">
            <HistoryChart 
              machineId={machineId} 
              key={refreshKey} 
            />
          </div>
        </div>

        {/* 7. Add the new ReliabilityChart in a full-width row */}
        <div className="w-full">
          <ReliabilityChart data={partStats} partId={currentPartId} />
        </div>
      </main>
    </div>
  );
};

export default MachineDetailPage;