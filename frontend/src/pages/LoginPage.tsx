import React from 'react';
import LoginForm from '../features/authentication/LoginForm';

const LoginPage = () => {
  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
      <div>
        <h2>Login to Your Account</h2>
        <LoginForm />
      </div>
    </div>
  );
};

export default LoginPage;