import React, { useState } from 'react';
import apiService from '../../api/apiService';
import { PredictionRequest } from '../../types';
import RiskGauge from './RiskGauge';

// Props: Receives machineId from the parent page
interface PredictionFormProps {
  machineId: string;
  onPredictionSuccess: () => void;
}

const PredictionForm: React.FC<PredictionFormProps> = ({ machineId, onPredictionSuccess }) => {
  
  // State: Uses the machineId prop for its initial state
  const [formData, setFormData] = useState<PredictionRequest>({
    machine_id: machineId,
    part_id: 'P-BRG-02',
    time_in_service_days: 450,
  });
  const [result, setResult] = useState<any>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    // Handle number conversion for the 'days' field
    const value = e.target.type === 'number' ? e.target.valueAsNumber : e.target.value;
    setFormData({ ...formData, [e.target.name]: value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await apiService.post('/predictions/predict', formData);
      setResult(response.data);
      onPredictionSuccess(); // Triggers the chart refresh
    } catch (error) {
      console.error("Prediction failed", error);
    }
  };

  return (
    <div className="border border-slate-200 p-6 rounded-lg shadow-sm bg-white">
      <h3 className="text-xl font-semibold mb-6 text-slate-800">
        Make a New Prediction
      </h3>
      
      <form onSubmit={handleSubmit}>
        
        {/* Wrapper adds consistent vertical spacing */}
        <div className="space-y-4">
          <div>
            <label htmlFor="machine_id" className="block text-sm font-medium text-gray-700">
              Machine ID
            </label>
            <input
              type="text"
              name="machine_id"
              id="machine_id"
              value={formData.machine_id}
              readOnly // Machine ID is fixed on this page
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-gray-100 text-gray-500 focus:outline-none"
            />
          </div>

          <div>
            <label htmlFor="part_id" className="block text-sm font-medium text-gray-700">
              Part ID
            </label>
            <input
              type="text"
              name="part_id"
              id="part_id"
              value={formData.part_id}
              onChange={handleChange}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label htmlFor="time_in_service_days" className="block text-sm font-medium text-gray-700">
              Days in Service
            </label>
            <input
              type="number"
              name="time_in_service_days"
              id="time_in_service_days"
              value={formData.time_in_service_days}
              onChange={handleChange}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>

        <button
          type="submit"
          className="mt-6 w-full bg-blue-600 text-white py-2 px-4 rounded-md shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          Predict Failure
        </button>
      </form>

      {/* Result section with the gauge */}
      {result && (
        <div className="mt-6 bg-slate-50 p-4 rounded-lg border border-slate-200">
          <h4 className="text-lg font-semibold text-center text-slate-900 mb-2">
            Prediction Result
          </h4>
          
          <RiskGauge risk={result.failure_risk} />
          
          <p className="text-center text-base mt-3 text-slate-800">
            Recommendation: <strong className="font-semibold">{result.recommendation}</strong>
          </p>
        </div>
      )}
    </div>
  );
};

export default PredictionForm;