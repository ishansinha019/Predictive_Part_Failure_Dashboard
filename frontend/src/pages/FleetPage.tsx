import React from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../components/layout/Navbar';

// Mock data for our fleet
const machines = [
  { id: 'M-185', status: 'Operational', risk: 'Low' },
  { id: 'M-201', status: 'Operational', risk: 'Low' },
  { id: 'M-202', status: 'At Risk', risk: 'Medium' },
];

// A simple "Fleet Card" component
const FleetCard: React.FC<{ machine: any }> = ({ machine }) => {
  const statusColor = machine.status === 'At Risk' ? 'text-yellow-500' : 'text-green-500';

  return (
    // Make the whole card a clickable link
    <Link 
      to={`/machine/${machine.id}`}
      className="bg-white border border-slate-200 p-6 rounded-lg shadow-sm hover:shadow-md transition-shadow cursor-pointer"
    >
      <h3 className="text-xl font-semibold text-slate-800">{machine.id}</h3>
      <p className="text-slate-600 mt-2">
        Status: <span className={`font-medium ${statusColor}`}>{machine.status}</span>
      </p>
      <p className="text-slate-600">
        Failure Risk: <span className="font-medium">{machine.risk}</span>
      </p>
      <div className="mt-4 text-blue-600 font-medium">
        View Details &rarr;
      </div>
    </Link>
  );
};

// The main FleetPage component
const FleetPage = () => {
  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <main className="p-6 md:p-8">
        <h2 className="text-3xl font-bold text-slate-900 mb-6">
          Machine Fleet
        </h2>
        
        {/* Grid layout for the cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {machines.map(machine => (
            <FleetCard key={machine.id} machine={machine} />
          ))}
        </div>
      </main>
    </div>
  );
};

export default FleetPage;