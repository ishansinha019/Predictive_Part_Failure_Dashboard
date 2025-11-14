import React from 'react';
import { Routes, Route } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import MachineDetailPage from './pages/MachineDetailPage'; // 1. Renamed this
import FleetPage from './pages/FleetPage'; // 2. Added this new page
import ProtectedRoute from './components/common/ProtectedRoute';
import PublicRoute from './components/common/PublicRoute';

function App() {
  return (
    <Routes>
      <Route
        path="/login"
        element={
          <PublicRoute>
            <LoginPage />
          </PublicRoute>
        }
      />
      {/* 3. The new homepage is the FleetPage */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <FleetPage />
          </ProtectedRoute>
        }
      />
      {/* 4. This is the new dynamic route for details */}
      <Route
        path="/machine/:machineId" 
        element={
          <ProtectedRoute>
            <MachineDetailPage />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

export default App;