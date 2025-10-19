import React from 'react';
import { useAuth } from '../../hooks/useAuth';

const Navbar = () => {
  const { logout } = useAuth();

  return (
    <nav style={{ background: '#333', color: 'white', padding: '1rem', display: 'flex', justifyContent: 'space-between' }}>
      <h1>Predictive Maintenance Dashboard</h1>
      <button onClick={logout}>Logout</button>
    </nav>
  );
};

export default Navbar;