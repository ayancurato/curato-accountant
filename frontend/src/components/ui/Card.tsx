import React from 'react';
import './Card.css';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  noPadding?: boolean;
}

export const Card: React.FC<CardProps> = ({ children, className = '', noPadding = false }) => {
  return (
    <div className={`curato-card ${noPadding ? 'curato-card-no-padding' : ''} ${className}`}>
      {children}
    </div>
  );
};
