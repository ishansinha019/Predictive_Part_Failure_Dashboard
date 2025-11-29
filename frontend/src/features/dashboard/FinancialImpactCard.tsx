import React, { useState } from 'react';

interface FinancialProps {
  partId: string;
  failureRisk: number; // 0 to 1
}

// --- MARKET DATA CONSTANTS ---
const DAILY_DOWNTIME_COST = 1500; // Loss of production + labor per day

// Detailed Cost & Time Database per Part Type
// Includes part price AND specific repair durations
const PART_DATA: Record<string, { cost: number, unplannedDays: number, plannedDays: number }> = {
  // Main Bearing: Heavy lift, requires crane, long lead time
  'P-BRG': { cost: 12000, unplannedDays: 7, plannedDays: 2 },
  
  // Gearbox: Major overhaul, extremely expensive and slow
  'P-GBX': { cost: 45000, unplannedDays: 14, plannedDays: 3 },
  
  // Pitch/Yaw Motors: Standard replacement
  'P-MTR': { cost: 3500, unplannedDays: 4, plannedDays: 1 },
  
  // Hydraulic Valves: Quick replacement
  'P-VLV': { cost: 600, unplannedDays: 2, plannedDays: 0.5 },
  
  // Sensors: Very quick, usually in stock
  'P-SEN': { cost: 300, unplannedDays: 1, plannedDays: 0.2 },
  
  // Controllers: Specialized technician needed
  'P-CTR': { cost: 2500, unplannedDays: 3, plannedDays: 0.5 },
  
  // Default fallback for unknown parts
  'DEFAULT': { cost: 1000, unplannedDays: 3, plannedDays: 1 }
};

const FinancialImpactCard: React.FC<FinancialProps> = ({ partId, failureRisk }) => {
  const [isScheduled, setIsScheduled] = useState(false); // State to track button click

  // 1. Determine Component Data
  // Extract prefix (e.g., 'P-BRG' from 'P-BRG-02') to look up data
  const prefix = partId.split('-').slice(0, 2).join('-');
  const partData = PART_DATA[prefix] || PART_DATA['DEFAULT'];

  // 2. Calculate Scenarios using dynamic days
  const unplannedCost = partData.cost + (partData.unplannedDays * DAILY_DOWNTIME_COST);
  const plannedCost = partData.cost + (partData.plannedDays * DAILY_DOWNTIME_COST);
  const potentialSavings = unplannedCost - plannedCost;

  // 3. Handle Click Action
  const handleScheduleClick = () => {
    if (window.confirm(`Confirm maintenance schedule for ${partId}? Estimated cost: $${plannedCost.toLocaleString()}`)) {
      setIsScheduled(true);
      alert(`Maintenance Work Order #WO-${Math.floor(Math.random() * 10000)} created successfully.`);
    }
  };

  // 4. Render logic
  if (failureRisk < 0.5) return null;

  const isCritical = failureRisk > 0.75;
  const cardColor = isCritical ? "bg-red-50 border-red-200" : "bg-orange-50 border-orange-200";
  const textColor = isCritical ? "text-red-800" : "text-orange-800";

  return (
    <div className={`border rounded-lg p-6 shadow-sm ${cardColor} mt-6`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className={`text-xl font-bold ${textColor} flex items-center gap-2`}>
          Financial Impact Analysis
        </h3>
        <span className="text-sm font-semibold bg-white px-3 py-1 rounded-full shadow-sm text-slate-700">
          ROI Opportunity
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
        {/* Reactive Scenario */}
        <div className="bg-white p-4 rounded-md shadow-sm border border-slate-100">
          <p className="text-xs text-gray-500 uppercase tracking-wide font-semibold">Reactive Cost (Unplanned)</p>
          <p className="text-2xl font-bold text-red-600 mt-1">
            ${unplannedCost.toLocaleString()}
          </p>
          <p className="text-xs text-gray-400 mt-2">
            Includes {partData.unplannedDays} days downtime + emergency labor
          </p>
        </div>

        {/* Savings / Action */}
        <div className="flex flex-col items-center justify-center">
          <p className="text-lg font-medium text-gray-600">Potential Savings</p>
          <p className="text-3xl font-extrabold text-green-600 my-2">
            ${potentialSavings.toLocaleString()}
          </p>
          
          <button 
            onClick={handleScheduleClick}
            disabled={isScheduled}
            className={`text-xs px-4 py-2 rounded transition shadow-sm font-medium ${
              isScheduled 
                ? 'bg-gray-400 text-white cursor-not-allowed' 
                : 'bg-green-600 text-white hover:bg-green-700'
            }`}
          >
            {isScheduled ? 'Maintenance Scheduled ✓' : 'Schedule Maintenance Now'}
          </button>
        </div>

        {/* Proactive Scenario */}
        <div className="bg-white p-4 rounded-md shadow-sm border border-slate-100">
          <p className="text-xs text-gray-500 uppercase tracking-wide font-semibold">Proactive Cost (Planned)</p>
          <p className="text-2xl font-bold text-blue-600 mt-1">
            ${plannedCost.toLocaleString()}
          </p>
          <p className="text-xs text-gray-400 mt-2">
            Includes {partData.plannedDays} day{partData.plannedDays !== 1 ? 's' : ''} downtime + standard labor
          </p>
        </div>
      </div>
    </div>
  );
};

export default FinancialImpactCard;