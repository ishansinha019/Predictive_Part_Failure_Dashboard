import React, { useState } from 'react';
import apiService from '../../api/apiService';
import { PredictionRequest } from '../../types';
import RiskGauge from './RiskGauge'; // 1. Import the new component

interface PredictionFormProps {
  onPredictionSuccess: () => void;
}

const PredictionForm: React.FC<PredictionFormProps> = ({ onPredictionSuccess }) => {
  const [formData, setFormData] = useState<PredictionRequest>({
    machine_id: 'M-185',
    part_id: 'P-BRG-02',
    time_in_service_days: 450,
  });
  const [result, setResult] = useState<any>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await apiService.post('/predictions/predict', formData);
      setResult(response.data);
      onPredictionSuccess();
    } catch (error) {
      console.error("Prediction failed", error);
    }
  };

  return (
    <div style={{ border: '1px solid #ccc', padding: '1rem', flex: 1 }}>
      <h3>Make a New Prediction</h3>
      <form onSubmit={handleSubmit}>
        {/* Form inputs... */}
        <div>Machine ID: <input name="machine_id" value={formData.machine_id} onChange={handleChange} /></div>
        <div style={{ margin: '1rem 0' }}>Part ID: <input name="part_id" value={formData.part_id} onChange={handleChange} /></div>
        <div>Days in Service: <input name="time_in_service_days" type="number" value={formData.time_in_service_days} onChange={handleChange} /></div>
        <button type="submit" style={{ marginTop: '1rem' }}>Predict Failure</button>
      </form>
      
      {/* 2. --- THIS IS THE UPDATED PART --- */}
      {result && (
        <div style={{ marginTop: '1rem', background: 'beige', padding: '0.5rem' }}>
          <h3>Prediction Result</h3>
          
          {/* Replace the text with the gauge */}
          <RiskGauge risk={result.failure_risk} />
          
          <p style={{ textAlign: 'center', fontSize: '1.1rem', marginTop: '1rem' }}>
            Recommendation: <strong>{result.recommendation}</strong>
          </p>
        </div>
      )}
    </div>
  );
};

export default PredictionForm;