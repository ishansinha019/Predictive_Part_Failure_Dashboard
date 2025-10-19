import React, { useState } from 'react';
import apiService from '../../api/apiService';
import { PredictionRequest } from '../../types';

const PredictionForm = () => {
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
    } catch (error) {
      console.error("Prediction failed", error);
    }
  };

  return (
    <div style={{ border: '1px solid #ccc', padding: '1rem', flex: 1 }}>
      <h3>Make a New Prediction</h3>
      <form onSubmit={handleSubmit}>
        {/* Simplified form for brevity */}
        <div>Machine ID: <input name="machine_id" value={formData.machine_id} onChange={handleChange} /></div>
        <div style={{ margin: '1rem 0' }}>Part ID: <input name="part_id" value={formData.part_id} onChange={handleChange} /></div>
        <div>Days in Service: <input name="time_in_service_days" type="number" value={formData.time_in_service_days} onChange={handleChange} /></div>
        <button type="submit" style={{ marginTop: '1rem' }}>Predict Failure</button>
      </form>
      {result && (
        <div style={{ marginTop: '1rem', background: '#f0f0f0', padding: '1rem' }}>
          <h4>Prediction Result</h4>
          <p>Failure Risk: <strong>{(result.failure_risk * 100).toFixed(2)}%</strong></p>
          <p>Recommendation: <strong>{result.recommendation}</strong></p>
        </div>
      )}
    </div>
  );
};

export default PredictionForm;