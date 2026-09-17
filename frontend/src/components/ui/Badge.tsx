import React from 'react';
import './Badge.css';

interface BadgeProps {
  status: 'UPLOADED' | 'PROCESSING' | 'READY' | 'NEEDS_REVIEW' | 'APPROVED' | 'ERROR' | 'UNPAID' | 'PAID' | 'OUTSTANDING' | 'RECEIVED';
  children?: React.ReactNode;
}

export const Badge: React.FC<BadgeProps> = ({ status, children }) => {
  const text = children || status.replace('_', ' ');
  
  return (
    <span className={`curato-badge curato-badge-${status.toLowerCase()}`}>
      {text}
    </span>
  );
};
