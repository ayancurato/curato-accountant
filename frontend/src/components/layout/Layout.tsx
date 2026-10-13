import React from 'react';
import { Outlet, NavLink, Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import './Layout.css';

const Layout: React.FC = () => {
  const { logout, user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const isWidePage = location.pathname.startsWith('/expenses') || location.pathname.startsWith('/income');

  return (
    <div className="curato-layout">
      <header className="curato-header">
        <div className={`curato-header-inner ${isWidePage ? 'curato-header-wide' : 'container'}`}>
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
            {user && (
              <span style={{ fontSize: '0.8125rem', color: '#64748b', display: 'flex', alignItems: 'center', padding: '0.25rem 0.5rem' }}>
                {user.email}
              </span>
            )}
            <button onClick={handleLogout} className="curato-nav-link" style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
              Logout
            </button>
          </nav>
        </div>
      </header>

      <main className={`curato-main ${isWidePage ? 'curato-main-wide' : 'container'}`}>
        <Outlet />
      </main>
    </div>
  );
};

export default Layout;
