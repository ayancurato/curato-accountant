import React from 'react';
import './Input.css';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  fullWidth?: boolean;
}

export const Input: React.FC<InputProps> = ({ 
  label, 
  error, 
  fullWidth = true, 
  className = '', 
  id, 
  ...props 
}) => {
  const inputId = id || `input-${Math.random().toString(36).substring(2, 9)}`;

  return (
    <div className={`curato-input-group ${fullWidth ? 'curato-input-full' : ''} ${className}`}>
      {label && <label htmlFor={inputId} className="curato-input-label">{label}</label>}
      <input 
        id={inputId}
        className={`curato-input ${error ? 'curato-input-error' : ''}`} 
        {...props} 
      />
      {error && <span className="curato-input-error-msg">{error}</span>}
    </div>
  );
};
