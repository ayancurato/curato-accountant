import React from 'react';
import './Table.css';

interface TableProps {
  children: React.ReactNode;
  className?: string;
}

export const Table: React.FC<TableProps> = ({ children, className = '' }) => {
  return (
    <div className={`curato-table-container ${className}`}>
      <table className="curato-table">
        {children}
      </table>
    </div>
  );
};

export const TableHeader: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <thead className="curato-table-head">
    {children}
  </thead>
);

export const TableBody: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <tbody className="curato-table-body">
    {children}
  </tbody>
);

export const TableRow: React.FC<{ children: React.ReactNode, onClick?: () => void }> = ({ children, onClick }) => (
  <tr className={`curato-table-row ${onClick ? 'curato-table-row-clickable' : ''}`} onClick={onClick}>
    {children}
  </tr>
);

export const TableHead: React.FC<{ children: React.ReactNode, className?: string }> = ({ children, className = '' }) => (
  <th className={`curato-table-th ${className}`}>
    {children}
  </th>
);

export const TableCell: React.FC<{ children: React.ReactNode, className?: string }> = ({ children, className = '' }) => (
  <td className={`curato-table-td ${className}`}>
    {children}
  </td>
);
