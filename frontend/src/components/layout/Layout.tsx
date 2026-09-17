import React from 'react';
import { Outlet, NavLink, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import './Layout.css';

const Layout: React.FC = () => {
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="curato-layout">
      <header className="curato-header">
        <div className="container curato-header-inner">
          <Link to="/reports" className="curato-logo-link">
            <img src="/curato-logo.jpg" alt="Curato Logo" className="curato-logo" />
          </Link>
          
          <nav className="curato-nav">
            <NavLink to="/upload" className={({ isActive }) => `curato-nav-link ${isActive ? 'active' : ''}`}>
              Upload
            </NavLink>
            <NavLink to="/income" className={({ isActive }) => `curato-nav-link ${isActive ? 'active' : ''}`}>
              Income
            </NavLink>
            <NavLink to="/expenses" className={({ isActive }) => `curato-nav-link ${isActive ? 'active' : ''}`}>
              Expenses
            </NavLink>
            <NavLink to="/reports" className={({ isActive }) => `curato-nav-link ${isActive ? 'active' : ''}`}>
              Reports
            </NavLink>
            <NavLink to="/ca" className={({ isActive }) => `curato-nav-link ${isActive ? 'active' : ''}`}>
              CA
            </NavLink>
            <button onClick={handleLogout} className="curato-nav-link" style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
              Logout
            </button>
          </nav>
        </div>
      </header>

      <main className="curato-main container">
        <Outlet />
      </main>
    </div>
  );
};

export default Layout;
