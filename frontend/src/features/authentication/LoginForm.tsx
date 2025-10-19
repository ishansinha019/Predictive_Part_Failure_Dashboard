import React, { useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import apiService from '../../api/apiService';

const LoginForm = () => {
  const { login } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      // NOTE: FastAPI's OAuth2 expects form data, not JSON
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);
      
      const response = await apiService.post('/auth/token', formData);
      const { access_token } = response.data;
      
      // In a real app, you'd fetch user details separately
      login({ username: username }, access_token);

    } catch (err) {
      setError('Invalid username or password.');
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label>Username: </label>
        <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} required />
      </div>
      <div style={{ marginTop: '1rem' }}>
        <label>Password: </label>
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
      </div>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <button type="submit" style={{ marginTop: '1rem' }}>Login</button>
    </form>
  );
};

export default LoginForm;