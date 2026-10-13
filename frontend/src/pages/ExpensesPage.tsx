import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getExpenses, getCategories, updateTransaction, deleteTransaction } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { Search, Calendar, ChevronDown, MoreHorizontal, Paperclip, Plus, ChevronsUpDown, Trash2, CheckCircle2, AlertTriangle } from 'lucide-react';
import './ExpensesPage.css';

const ExpensesPage: React.FC = () => {
  const navigate = useNavigate();
  const { token } = useAuth();
  
  const [expenses, setExpenses] = useState<any[]>([]);
  const [categories, setCategories] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Delete modal state
  const [deleteModalTx, setDeleteModalTx] = useState<any | null>(null);
  const [isDeleting, setIsDeleting] = useState<boolean>(false);
  const [successToast, setSuccessToast] = useState<string | null>(null);

  // Filters
  const [status, setStatus] = useState<string>('');
  const [paymentStatus, setPaymentStatus] = useState<string>('');
  const [search, setSearch] = useState<string>('');
  const [dateFrom, setDateFrom] = useState<string>('');
  const [dateTo, setDateTo] = useState<string>('');

  const [editingCell, setEditingCell] = useState<{ id: string, field: 'net_amount' | 'total_amount' } | null>(null);
  const [editValue, setEditValue] = useState<string>('');
  const [categoryId, setCategoryId] = useState<string>('');

  const handleDeleteExpense = async () => {
    if (!token || !deleteModalTx) return;
    try {
      setIsDeleting(true);
      await deleteTransaction(token, deleteModalTx.id, 'EXPENSE');
      setExpenses(prev => prev.filter(t => t.id !== deleteModalTx.id));
      setSuccessToast(`Deleted entry for ${deleteModalTx.vendor_customer || 'expense'}`);
      setDeleteModalTx(null);
      setTimeout(() => setSuccessToast(null), 4000);
    } catch (err: any) {
      alert(err.message || 'Failed to delete expense entry');
    } finally {
      setIsDeleting(false);
    }
  };

  const loadData = async () => {
    if (!token) return;
    try {
      setLoading(true);
      setError(null);
      
      const cats = await getCategories(token);
      setCategories(cats.filter((c: any) => c.type === 'EXPENSE'));

      const data = await getExpenses(token);
      setExpenses(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch expense transactions');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [token]); // We fetch all once, then filter client-side

  const getCategoryName = (id: string) => {
    const cat = categories.find(c => c.id === id);
    return cat ? cat.name : 'Uncategorized';
  };

  const [dateSortAsc, setDateSortAsc] = useState<boolean>(false);
  const toggleSort = () => setDateSortAsc(prev => !prev);

  const filteredExpenses = expenses.filter(tx => {
    if (status && tx.status !== status) return false;
    if (paymentStatus && tx.payment_status !== paymentStatus) return false;
    if (categoryId && tx.category_id !== categoryId) return false;
    if (dateFrom && (!tx.date || tx.date < dateFrom)) return false;
    if (dateTo && (!tx.date || tx.date > dateTo)) return false;
    if (search) {
      const term = search.toLowerCase();
      const vendor = (tx.vendor_customer || '').toLowerCase();
      const inv = (tx.invoice_number || '').toLowerCase();
      const notes = (tx.notes || '').toLowerCase();
      if (!vendor.includes(term) && !inv.includes(term) && !notes.includes(term)) {
        return false;
      }
    }
    return true;
  });

  const displayedExpenses = [...filteredExpenses].sort((a, b) => {
    const da = a.date || '';
    const db = b.date || '';
    return dateSortAsc ? da.localeCompare(db) : db.localeCompare(da);
  });

  return (
    <div className="expenses-page-wrapper">
      <div className="expenses-container">
        
        {/* Hero Section */}
        <div className="expenses-hero">
          <div className="expenses-hero-text">
            <h1>Expenses</h1>
            <p>Track and manage all your business expenses in one place.</p>
          </div>
          <button className="btn-add-expense" onClick={() => navigate('/upload')}>
            <Plus size={18} /> Add Expense
          </button>
        </div>

        {/* Filter Card */}
        <div className="filter-card">
          <div className="filter-grid">
            
            {/* Search */}
            <div className="filter-group">
              <label className="filter-label">Search (Vendor, Invoice, Notes)</label>
              <div className="filter-input-wrapper">
                <Search size={16} className="filter-icon" />
                <input 
                  type="text"
                  className="filter-input with-icon"
                  placeholder="Search..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>
            </div>

            {/* Transaction Status */}
            <div className="filter-group">
              <label className="filter-label">Transaction Status</label>
              <div className="filter-input-wrapper">
                <select 
                  className="filter-select"
                  value={status}
                  onChange={(e) => setStatus(e.target.value)}
                >
                  <option value="">Select an option</option>
                  <option value="DRAFT">Draft</option>
                  <option value="NEEDS_REVIEW">Needs Review</option>
                  <option value="APPROVED">Approved</option>
                </select>
                <ChevronDown size={16} className="filter-select-chevron" />
              </div>
            </div>

            {/* Payment Status */}
            <div className="filter-group">
              <label className="filter-label">Payment Status</label>
              <div className="filter-input-wrapper">
                <select 
                  className="filter-select"
                  value={paymentStatus}
                  onChange={(e) => setPaymentStatus(e.target.value)}
                >
                  <option value="">Select an option</option>
                  <option value="PAID">Paid</option>
                  <option value="UNPAID">Unpaid</option>
                </select>
                <ChevronDown size={16} className="filter-select-chevron" />
              </div>
            </div>

            {/* Category */}
            <div className="filter-group">
              <label className="filter-label">Category</label>
              <div className="filter-input-wrapper">
                <select 
                  className="filter-select"
                  value={categoryId}
                  onChange={(e) => setCategoryId(e.target.value)}
                >
                  <option value="">Select an option</option>
                  {categories.map(c => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
                <ChevronDown size={16} className="filter-select-chevron" />
              </div>
            </div>

            {/* Date From */}
            <div className="filter-group">
              <label className="filter-label">Date From</label>
              <div className="filter-input-wrapper">
                <Calendar size={16} className="filter-icon" />
                <input 
                  type="date"
                  className="filter-input with-icon filter-date-input"
                  value={dateFrom}
                  onChange={(e) => setDateFrom(e.target.value)}
                />
              </div>
            </div>

            {/* Date To (Second Row) */}
            <div className="filter-group filter-group-dateto">
              <label className="filter-label">Date To</label>
              <div className="filter-input-wrapper">
                <Calendar size={16} className="filter-icon" />
                <input 
                  type="date"
                  className="filter-input with-icon filter-date-input"
                  value={dateTo}
                  onChange={(e) => setDateTo(e.target.value)}
                />
              </div>
            </div>

          </div>
        </div>

        {/* States */}
        {error && (
          <div className="error-container">
            {error}
          </div>
        )}

        {loading ? (
          <div className="state-container">Loading expense transactions...</div>
        ) : expenses.length === 0 ? (
          <div className="state-container">
            <p>No expenses recorded yet.</p>
          </div>
        ) : filteredExpenses.length === 0 ? (
          <div className="state-container">
            <p>No expenses match your filters.</p>
            <p style={{ fontSize: '0.875rem', marginTop: '0.5rem' }}>Try adjusting your search criteria.</p>
          </div>
        ) : (
          /* Table Card */
          <div className="table-card">
            <div className="expenses-table-container">
              <table className="expenses-table">
                <thead>
                  <tr>
                    <th style={{ width: '90px' }}>
                      <div className="table-header-sort" onClick={toggleSort}>
                        DATE <ChevronsUpDown size={12} />
                      </div>
                    </th>
                    <th style={{ minWidth: '130px', maxWidth: '200px' }}>VENDOR</th>
                    <th style={{ minWidth: '95px', maxWidth: '130px' }}>INVOICE #</th>
                    <th style={{ minWidth: '110px', maxWidth: '150px' }}>CATEGORY</th>
                    <th style={{ width: '75px', textAlign: 'right' }}>USD</th>
                    <th style={{ width: '85px', textAlign: 'right' }}>NET</th>
                    <th style={{ width: '75px', textAlign: 'right' }}>GST</th>
                    <th style={{ width: '90px', textAlign: 'right' }}>TOTAL</th>
                    <th style={{ minWidth: '85px', maxWidth: '110px' }}>ACCOUNT</th>
                    <th style={{ width: '80px', textAlign: 'center' }}>PAY STATUS</th>
                    <th style={{ width: '75px', textAlign: 'center' }}>TYPE</th>
                    <th style={{ width: '70px', textAlign: 'center' }}>BIZ/PERS</th>
                    <th style={{ width: '85px', textAlign: 'center' }}>STATUS</th>
                    <th style={{ width: '65px', textAlign: 'center' }}>ACTIONS</th>
                  </tr>
                </thead>
                <tbody>
                  {displayedExpenses.map((tx) => (
                    <tr key={tx.id} onClick={() => navigate(`/review/${tx.id}`)} style={{ cursor: 'pointer' }}>
                      <td style={{ whiteSpace: 'nowrap', fontSize: '0.8rem' }}>{tx.date || '-'}</td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', maxWidth: '200px' }} title={tx.vendor_customer}>
                          {tx.document_id && <Paperclip size={13} style={{ color: '#9CA3AF', flexShrink: 0 }} />}
                          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontWeight: 500 }}>
                            {tx.vendor_customer || '-'}
                          </span>
                        </div>
                      </td>
                      <td title={tx.invoice_number}>
                        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'block', maxWidth: '130px', fontSize: '0.8rem' }}>
                          {tx.invoice_number || '-'}
                        </span>
                      </td>
                      <td title={getCategoryName(tx.category_id)}>
                        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'block', maxWidth: '150px', fontSize: '0.78rem' }}>
                          {getCategoryName(tx.category_id)}
                        </span>
                      </td>
                      <td className="col-usd" style={{ whiteSpace: 'nowrap', textAlign: 'right', fontSize: '0.8rem' }}>
                        {tx.usd_amount ? parseFloat(tx.usd_amount).toLocaleString('en-US', { style: 'currency', currency: 'USD' }) : '-'}
                      </td>
                      
                      {/* NET AMOUNT */}
                      <td className="col-net" style={{ whiteSpace: 'nowrap', textAlign: 'right', fontSize: '0.8rem' }} onClick={(e) => {
                        e.stopPropagation();
                        setEditingCell({ id: tx.id, field: 'net_amount' });
                        setEditValue((tx.net_amount || '0').toString());
                      }}>
                        {editingCell?.id === tx.id && editingCell?.field === 'net_amount' ? (
                          <div style={{ display: 'flex', gap: '4px', justifyContent: 'flex-end' }}>
                            <input 
                              autoFocus
                              type="number" 
                              step="0.01"
                              value={editValue} 
                              onChange={e => setEditValue(e.target.value)}
                              onClick={e => e.stopPropagation()}
                              onKeyDown={async (e) => {
                                if (e.key === 'Enter') {
                                  e.stopPropagation();
                                  try {
                                    if (token && editValue !== (tx.net_amount || '0').toString()) {
                                      await updateTransaction(token, tx.id, 'EXPENSE', { net_amount: parseFloat(editValue) || 0 });
                                      setExpenses(prev => prev.map(t => t.id === tx.id ? { ...t, net_amount: parseFloat(editValue) || 0 } : t));
                                    }
                                  } catch(err) { console.error(err); }
                                  setEditingCell(null);
                                } else if (e.key === 'Escape') {
                                  setEditingCell(null);
                                }
                              }}
                              onBlur={() => setEditingCell(null)}
                              style={{ width: '75px', padding: '2px 4px', border: '1px solid #cbd5e1', borderRadius: '4px' }}
                            />
                          </div>
                        ) : (
                          <span style={{ borderBottom: '1px dashed #cbd5e1', paddingBottom: '2px' }} title="Click to edit">
                            {parseFloat(tx.net_amount || '0').toLocaleString('en-IN', { style: 'currency', currency: 'INR' })}
                          </span>
                        )}
                      </td>

                      <td className="col-gst" style={{ whiteSpace: 'nowrap', textAlign: 'right', fontSize: '0.8rem' }}>
                        {parseFloat(tx.gst_amount || '0').toLocaleString('en-IN', { style: 'currency', currency: 'INR' })}
                      </td>
                      
                      {/* TOTAL AMOUNT */}
                      <td className="col-total" style={{ whiteSpace: 'nowrap', textAlign: 'right', fontSize: '0.8125rem' }} onClick={(e) => {
                        e.stopPropagation();
                        setEditingCell({ id: tx.id, field: 'total_amount' });
                        setEditValue((tx.total_amount || '0').toString());
                      }}>
                        {editingCell?.id === tx.id && editingCell?.field === 'total_amount' ? (
                          <div style={{ display: 'flex', gap: '4px', justifyContent: 'flex-end' }}>
                            <input 
                              autoFocus
                              type="number" 
                              step="0.01"
                              value={editValue} 
                              onChange={e => setEditValue(e.target.value)}
                              onClick={e => e.stopPropagation()}
                              onKeyDown={async (e) => {
                                if (e.key === 'Enter') {
                                  e.stopPropagation();
                                  try {
                                    if (token && editValue !== (tx.total_amount || '0').toString()) {
                                      await updateTransaction(token, tx.id, 'EXPENSE', { total_amount: parseFloat(editValue) || 0 });
                                      setExpenses(prev => prev.map(t => t.id === tx.id ? { ...t, total_amount: parseFloat(editValue) || 0 } : t));
                                    }
                                  } catch(err) { console.error(err); }
                                  setEditingCell(null);
                                } else if (e.key === 'Escape') {
                                  setEditingCell(null);
                                }
                              }}
                              onBlur={() => setEditingCell(null)}
                              style={{ width: '75px', padding: '2px 4px', border: '1px solid #cbd5e1', borderRadius: '4px', fontWeight: 'bold' }}
                            />
                          </div>
                        ) : (
                          <span style={{ borderBottom: '1px dashed #cbd5e1', paddingBottom: '2px' }} title="Click to edit">
                            {parseFloat(tx.total_amount || '0').toLocaleString('en-IN', { style: 'currency', currency: 'INR' })}
                          </span>
                        )}
                      </td>
                      <td title={tx.payment_account}>
                        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'block', maxWidth: '110px', fontSize: '0.78rem' }}>
                          {tx.payment_account || '-'}
                        </span>
                      </td>
                      <td style={{ textAlign: 'center', whiteSpace: 'nowrap' }}>
                        {tx.payment_status ? (
                          <span className={`status-pill ${tx.payment_status === 'PAID' ? 'success' : 'warning'}`}>
                            {tx.payment_status}
                          </span>
                        ) : '-'}
                      </td>
                      <td style={{ textAlign: 'center', whiteSpace: 'nowrap', fontSize: '0.75rem' }}>
                        {tx.expense_type === 'OPERATING_EXPENSE' ? 'Opex' : tx.expense_type === 'ASSET' ? 'Asset' : (tx.expense_type || '-')}
                      </td>
                      <td style={{ textAlign: 'center', whiteSpace: 'nowrap' }}>
                        <span className="status-pill neutral" style={{ padding: '0.15rem 0.45rem', fontSize: '0.65rem' }}>
                          {tx.business_personal ? tx.business_personal.substring(0, 4) : '-'}
                        </span>
                      </td>
                      <td style={{ textAlign: 'center', whiteSpace: 'nowrap' }}>
                        <span className={`status-pill ${tx.status === 'APPROVED' ? 'success' : tx.status === 'NEEDS_REVIEW' ? 'warning' : 'neutral'}`}>
                          {tx.status === 'NEEDS_REVIEW' ? 'Review' : tx.status === 'APPROVED' ? 'Approved' : tx.status.replace('_', ' ')}
                        </span>
                      </td>
                      <td style={{ textAlign: 'center', whiteSpace: 'nowrap' }}>
                        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                          <button 
                            className="btn-action" 
                            title="Review details"
                            onClick={(e) => {
                              e.stopPropagation();
                              navigate(`/review/${tx.id}`);
                            }}
                          >
                            <MoreHorizontal size={15} />
                          </button>
                          <button 
                            className="btn-action btn-action-delete" 
                            title="Delete entry"
                            onClick={(e) => {
                              e.stopPropagation();
                              setDeleteModalTx(tx);
                            }}
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Success Toast */}
        {successToast && (
          <div className="toast-notification">
            <CheckCircle2 size={16} /> {successToast}
          </div>
        )}

        {/* Delete Confirmation Modal */}
        {deleteModalTx && (
          <div className="delete-modal-backdrop" onClick={() => !isDeleting && setDeleteModalTx(null)}>
            <div className="delete-modal-dialog" onClick={(e) => e.stopPropagation()}>
              <div className="delete-modal-header">
                <div className="delete-modal-icon">
                  <AlertTriangle size={22} />
                </div>
                <div>
                  <h3>Delete Expense Entry</h3>
                  <p className="delete-modal-sub">This action cannot be undone.</p>
                </div>
              </div>
              <div className="delete-modal-body">
                <p>Are you sure you want to permanently delete this duplicate or unwanted expense?</p>
                <div className="delete-modal-details">
                  <div><strong>Vendor:</strong> {deleteModalTx.vendor_customer || 'Unknown'}</div>
                  <div><strong>Invoice #:</strong> {deleteModalTx.invoice_number || 'N/A'}</div>
                  <div><strong>Date:</strong> {deleteModalTx.date || 'N/A'}</div>
                  <div><strong>Total Amount:</strong> {parseFloat(deleteModalTx.total_amount || '0').toLocaleString('en-IN', { style: 'currency', currency: 'INR' })}</div>
                </div>
              </div>
              <div className="delete-modal-footer">
                <button 
                  type="button" 
                  className="btn-modal-cancel" 
                  onClick={() => setDeleteModalTx(null)}
                  disabled={isDeleting}
                >
                  Cancel
                </button>
                <button 
                  type="button" 
                  className="btn-modal-delete" 
                  onClick={handleDeleteExpense}
                  disabled={isDeleting}
                >
                  {isDeleting ? 'Deleting...' : 'Delete Expense'}
                </button>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
};

export default ExpensesPage;
