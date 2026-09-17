import React from 'react';
import './Input.css'; // Reuses input styling

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  fullWidth?: boolean;
  options: { value: string; label: string }[];
}

export const Select: React.FC<SelectProps> = ({ 
  label, 
  error, 
  fullWidth = true, 
  className = '', 
  id, 
  options,
  ...props 
}) => {
  const selectId = id || `select-${Math.random().toString(36).substring(2, 9)}`;

  return (
    <div className={`curato-input-group ${fullWidth ? 'curato-input-full' : ''} ${className}`}>
      {label && <label htmlFor={selectId} className="curato-input-label">{label}</label>}
      <select 
        id={selectId}
        className={`curato-input ${error ? 'curato-input-error' : ''}`} 
        {...props} 
      >
        <option value="" disabled>Select an option</option>
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </select>
      {error && <span className="curato-input-error-msg">{error}</span>}
    </div>
  );
};
