import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { AlertCircle, CheckCircle, Check } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Input } from '../components/ui/Input';
import { Select } from '../components/ui/Select';
import { getTransaction, getDocument, getDocumentFile, getCategories, updateTransaction, approveTransaction } from '../api/client';
import { useAuth } from '../context/AuthContext';
import './ReviewPage.css';

const formatAnomalyMessage = (anomaly: any) => {
  const type = anomaly.type || anomaly;
  switch (type) {
    case 'MISSING_GSTIN': return 'GSTIN is missing';
    case 'DUPLICATE_TRANSACTION': return 'Potential duplicate detected';
    case 'GST_MISMATCH': return 'GST amount does not match the invoice totals';
    case 'MISSING_INVOICE_NUMBER': return 'Invoice number missing';
    case 'CATEGORY_MISSING': return 'Category could not be determined';
    default: return anomaly.message || type;
  }
};

const ReviewPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { token } = useAuth();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [tx, setTx] = useState<any>(null);
  const [originalTx, setOriginalTx] = useState<any>(null);
  const [doc, setDoc] = useState<any>(null);
  const [docObjectUrl, setDocObjectUrl] = useState<string | null>(null);
  const [docLoading, setDocLoading] = useState(false);
  const [docError, setDocError] = useState<string | null>(null);
  const [categories, setCategories] = useState<any[]>([]);
  
  const [isSaving, setIsSaving] = useState(false);
  const [isApproving, setIsApproving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    if (!token || !id) return;
    
    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);

        const cats = await getCategories(token);
        setCategories(cats);

        const transaction = await getTransaction(token, id);
        
        ['net_amount', 'gst_amount', 'total_amount', 'usd_amount', 'exchange_rate', 'gst_rate', 'cgst', 'sgst', 'igst'].forEach(field => {
          if (transaction[field] !== null && transaction[field] !== undefined) {
            transaction[field] = Number(transaction[field]).toFixed(2);
          }
        });

        setTx(transaction);
        setOriginalTx(JSON.parse(JSON.stringify(transaction)));

        if (transaction.document_id) {
          const document = await getDocument(token, transaction.document_id);
          setDoc(document);
        }
      } catch (err: any) {
        setError(err.message || 'Failed to load transaction data');
      } finally {
        setLoading(false);
      }
    };
    
    loadData();
  }, [token, id]);

  useEffect(() => {
    if (!token || !doc?.id) return;

    let objectUrl: string | null = null;
    let isMounted = true;

    const loadDocumentFile = async () => {
      try {
        setDocLoading(true);
        setDocError(null);
        const blob = await getDocumentFile(token, doc.id);
        
        if (!isMounted) return;
        
        objectUrl = window.URL.createObjectURL(blob);
        setDocObjectUrl(objectUrl);
      } catch (err: any) {
        if (!isMounted) return;
        setDocError(err.message || 'Failed to load document preview');
      } finally {
        if (isMounted) {
          setDocLoading(false);
        }
      }
    };

    loadDocumentFile();

    return () => {
      isMounted = false;
      if (objectUrl) {
        window.URL.revokeObjectURL(objectUrl);
      }
    };
  }, [token, doc?.id]);

  const hasChanges = JSON.stringify(tx) !== JSON.stringify(originalTx);
  const isApproved = tx?.status === 'APPROVED';

  const handleChange = (field: string, value: any) => {
    setTx((prev: any) => {
      const updated = { ...prev, [field]: value };
      
      if (field === 'usd_amount' || field === 'exchange_rate') {
        const parsedUSD = parseFloat(updated.usd_amount || '0');
        const parsedRate = parseFloat(updated.exchange_rate || '0');
        if (!isNaN(parsedUSD) && !isNaN(parsedRate) && parsedRate > 0) {
          updated.net_amount = (parsedUSD * parsedRate).toFixed(2);
          updated.total_amount = (parsedUSD * parsedRate).toFixed(2);
        }
      }
      return updated;
    });
    setSaveSuccess(false);
  };

  const handleSave = async () => {
    if (!token || !id || !tx) return;
    try {
      setIsSaving(true);
      setError(null);
      
      const payload = { ...tx };
      delete payload.id;
      delete payload.company_id;
      delete payload.document_id;
      delete payload.created_at;
      delete payload.updated_at;
      delete payload.type;

      const updated = await updateTransaction(token, id, tx.type, payload);
      setTx(updated);
      setOriginalTx(JSON.parse(JSON.stringify(updated)));
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
      return true;
    } catch (err: any) {
      setError(err.message || 'Failed to save changes');
      return false;
    } finally {
      setIsSaving(false);
    }
  };

  const handleApprove = async () => {
    if (!token || !id || !tx) return;
    try {
      setIsApproving(true);
      setError(null);

      if (hasChanges) {
        const saved = await handleSave();
        if (!saved) return;
      }

      await approveTransaction(token, id, tx.type);
      setTx((prev: any) => ({ ...prev, status: 'APPROVED' }));
      setOriginalTx((prev: any) => ({ ...prev, status: 'APPROVED' }));
    } catch (err: any) {
      setError(err.message || 'Failed to approve transaction');
    } finally {
      setIsApproving(false);
    }
  };

  if (loading) return <div className="container" style={{ padding: '2rem' }}>Loading review workspace...</div>;
  if (error && !tx) return <div className="container" style={{ padding: '2rem', color: 'red' }}>Error: {error}</div>;
  if (!tx) return <div className="container" style={{ padding: '2rem' }}>Transaction not found.</div>;
  
  const anomalies = Array.isArray(tx.anomalies) ? tx.anomalies : [];
  const needsAttention = tx.status === 'NEEDS_REVIEW' || anomalies.length > 0;

  return (
    <div className="review-container">
      <div className="review-header">
        <div className="review-header-title">
          <Button variant="outline" size="sm" onClick={() => navigate('/upload')}>← Back</Button>
          <h1>Review Transaction</h1>
        </div>
        <div className="review-header-status">
          {doc && <Badge status={doc.status}>Document: {doc.status.replace('_', ' ')}</Badge>}
          <Badge status={tx.status}>Transaction: {tx.status.replace('_', ' ')}</Badge>
        </div>
      </div>

      {error && (
        <div style={{ backgroundColor: '#FEE2E2', color: '#991B1B', padding: '1rem', borderRadius: '0.5rem', marginBottom: '1rem' }}>
          {error}
        </div>
      )}

      <div className="review-workspace">
        <div className="review-col-left">
          <div className="document-viewer">
            {docLoading ? (
              <div style={{ padding: '2rem', textAlign: 'center' }}>Loading document preview...</div>
            ) : docError ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: '#991B1B' }}>
                <AlertCircle style={{ margin: '0 auto', marginBottom: '0.5rem' }} />
                <p>{docError}</p>
              </div>
            ) : docObjectUrl ? (
              doc.file_type === 'application/pdf' ? (
                <iframe src={docObjectUrl} title="Document Viewer" />
              ) : (
                <img src={docObjectUrl} alt="Document" />
              )
            ) : (
              <p>No document attached</p>
            )}
          </div>
        </div>

        <div className="review-col-right">
          {needsAttention && !isApproved && (
            <div className="attention-panel">
              <h3><AlertCircle size={18} /> Needs Attention</h3>
              <ul>
                {anomalies.map((a: any, i: number) => <li key={i}>{formatAnomalyMessage(a)}</li>)}
              </ul>
            </div>
          )}
          
          {!needsAttention && !isApproved && (
            <div className="validation-passed">
              <CheckCircle size={18} /> Validation passed
            </div>
          )}

          <div className="review-section">
            <h2>Document Information</h2>
            <div className="review-grid">
              <Input 
                label="Document Type" 
                value={tx.type} 
                disabled 
              />
              <Input 
                label={tx.type === 'EXPENSE' ? 'Vendor' : 'Customer'} 
                value={tx.vendor_customer || ''} 
                onChange={(e) => handleChange('vendor_customer', e.target.value)} 
                disabled={isApproved}
              />
              <Input 
                label="Invoice Number" 
                value={tx.invoice_number || ''} 
                onChange={(e) => handleChange('invoice_number', e.target.value)} 
                disabled={isApproved}
              />
              <Input 
                label="Date" 
                type="date"
                value={tx.date || ''} 
                onChange={(e) => handleChange('date', e.target.value)} 
                disabled={isApproved}
              />
              <Input 
                label="Due Date" 
                type="date"
                value={tx.due_date || ''} 
                onChange={(e) => handleChange('due_date', e.target.value)} 
                disabled={isApproved}
              />
            </div>
          </div>

          <div className="review-section">
            <h2>Financial Information</h2>
            <div className="review-grid">
              <Input 
                label="Currency" 
                value={tx.currency || 'N/A'} 
                disabled 
              />
              {tx.usd_amount !== null && tx.usd_amount !== undefined && (
                <>
                  <Input 
                    label="USD Amount" 
                    type="number"
                    step="0.01"
                    value={tx.usd_amount || ''} 
                    onChange={(e) => handleChange('usd_amount', e.target.value)} 
                    disabled={isApproved}
                  />
                  <Input 
                    label="Exchange Rate" 
                    type="number"
                    step="0.0001"
                    value={tx.exchange_rate || ''} 
                    onChange={(e) => handleChange('exchange_rate', e.target.value)} 
                    disabled={isApproved}
                  />
                </>
              )}
              <Input 
                label="Net Amount" 
                type="number"
                step="0.01"
                value={tx.net_amount || ''} 
                onChange={(e) => handleChange('net_amount', e.target.value)} 
                disabled={isApproved}
              />
              <Input 
                label="GST Amount" 
                type="number"
                step="0.01"
                value={tx.gst_amount || ''} 
                onChange={(e) => handleChange('gst_amount', e.target.value)} 
                disabled={isApproved}
              />
              <Input 
                label="Total Amount" 
                type="number"
                step="0.01"
                value={tx.total_amount || ''} 
                onChange={(e) => handleChange('total_amount', e.target.value)} 
                disabled={isApproved}
                style={{ fontWeight: 'bold' }}
              />
            </div>
          </div>

          <div className="review-section">
            <h2>GST Details</h2>
            <div className="review-grid">
              <Input 
                label={tx.type === 'EXPENSE' ? 'Vendor GSTIN' : 'Customer GSTIN'} 
                value={tx.type === 'EXPENSE' ? (tx.vendor_gstin || '') : (tx.customer_gstin || '')} 
                onChange={(e) => handleChange(tx.type === 'EXPENSE' ? 'vendor_gstin' : 'customer_gstin', e.target.value)} 
                disabled={isApproved}
                className={anomalies.some((a: any) => a.type === 'MISSING_GSTIN') ? 'field-attention' : ''}
              />
              <Input 
                label="GST Rate (%)" 
                type="number"
                value={tx.gst_rate || ''} 
                onChange={(e) => handleChange('gst_rate', parseFloat(e.target.value))} 
                disabled={isApproved}
              />
              <Input 
                label="CGST" 
                type="number" step="0.01"
                value={tx.cgst || 0} 
                onChange={(e) => handleChange('cgst', parseFloat(e.target.value))} 
                disabled={isApproved}
              />
              <Input 
                label="SGST" 
                type="number" step="0.01"
                value={tx.sgst || 0} 
                onChange={(e) => handleChange('sgst', parseFloat(e.target.value))} 
                disabled={isApproved}
              />
              <Input 
                label="IGST" 
                type="number" step="0.01"
                value={tx.igst || 0} 
                onChange={(e) => handleChange('igst', parseFloat(e.target.value))} 
                disabled={isApproved}
              />
              <Select
                label="ITC Eligible"
                value={tx.itc_eligible === true ? 'true' : tx.itc_eligible === false ? 'false' : ''}
                onChange={(e) => handleChange('itc_eligible', e.target.value === 'true')}
                options={[
                  { value: 'true', label: 'Yes' },
                  { value: 'false', label: 'No' }
                ]}
                disabled={isApproved}
              />
              <Select
                label="ITC Status"
                value={tx.itc_status || ''}
                onChange={(e) => handleChange('itc_status', e.target.value)}
                options={[
                  { value: 'CLAIMED', label: 'Claimed' },
                  { value: 'UNCLAIMED', label: 'Unclaimed' },
                  { value: 'REJECTED', label: 'Rejected' }
                ]}
                disabled={isApproved}
              />
            </div>
          </div>

          <div className="review-section">
            <h2>Classification</h2>
            <div className="review-grid">
              <Select
                label="Category"
                value={tx.category_id || ''}
                onChange={(e) => handleChange('category_id', e.target.value)}
                options={categories.filter(c => c.type === tx.type).map(c => ({ value: c.id, label: c.name }))}
                disabled={isApproved}
                className={anomalies.some((a: any) => a.type === 'CATEGORY_MISSING') ? 'field-attention' : ''}
              />
              <Select
                label="Expense Type"
                value={tx.expense_type || ''}
                onChange={(e) => handleChange('expense_type', e.target.value)}
                options={[
                  { value: 'OPERATING_EXPENSE', label: 'Operating Expense' },
                  { value: 'ASSET', label: 'Asset' },
                  { value: 'OTHER', label: 'Other' }
                ]}
                disabled={isApproved}
              />
              <Select
                label="Business / Personal"
                value={tx.business_personal || ''}
                onChange={(e) => handleChange('business_personal', e.target.value)}
                options={[
                  { value: 'BUSINESS', label: 'Business' },
                  { value: 'PERSONAL', label: 'Personal' },
                  { value: 'MIXED', label: 'Mixed' }
                ]}
                disabled={isApproved}
              />
            </div>
          </div>

          <div className="review-section">
            <h2>Payment</h2>
            <div className="review-grid">
              <Select
                label="Payment Method"
                value={tx.payment_account || ''}
                onChange={(e) => handleChange('payment_account', e.target.value)}
                options={[
                  { value: 'Current Account', label: 'Current Account' },
                  { value: 'Company Debit Card', label: 'Company Debit Card' },
                  { value: 'Cash', label: 'Cash' },
                  { value: 'UPI Transfer by Founder', label: 'UPI Transfer by Founder' },
                  { value: "Founder's Credit Card", label: "Founder's Credit Card" }
                ]}
                disabled={isApproved}
              />
              <Select
                label="Payment Status"
                value={tx.payment_status || ''}
                onChange={(e) => handleChange('payment_status', e.target.value)}
                options={tx.type === 'EXPENSE' 
                  ? [{ value: 'PAID', label: 'Paid' }, { value: 'UNPAID', label: 'Unpaid' }]
                  : [{ value: 'RECEIVED', label: 'Received' }, { value: 'OUTSTANDING', label: 'Outstanding' }]
                }
                disabled={isApproved}
              />
            </div>
          </div>

          <div className="review-section">
            <h2>TDS</h2>
            <div className="review-grid">
              <Select
                label="TDS Applicable"
                value={tx.tds_applicable === true ? 'true' : tx.tds_applicable === false ? 'false' : ''}
                onChange={(e) => handleChange('tds_applicable', e.target.value === 'true')}
                options={[
                  { value: 'true', label: 'Yes' },
                  { value: 'false', label: 'No' }
                ]}
                disabled={isApproved}
              />
              <Input 
                label="TDS Amount" 
                type="number" step="0.01"
                value={tx.tds_amount || 0} 
                onChange={(e) => handleChange('tds_amount', parseFloat(e.target.value))} 
                disabled={isApproved}
              />
              <Select
                label="TDS Deducted"
                value={tx.tds_deducted === true ? 'true' : tx.tds_deducted === false ? 'false' : ''}
                onChange={(e) => handleChange('tds_deducted', e.target.value === 'true')}
                options={[
                  { value: 'true', label: 'Yes' },
                  { value: 'false', label: 'No' }
                ]}
                disabled={isApproved}
              />
              <Select
                label="TDS Deposited"
                value={tx.tds_deposited === true ? 'true' : tx.tds_deposited === false ? 'false' : ''}
                onChange={(e) => handleChange('tds_deposited', e.target.value === 'true')}
                options={[
                  { value: 'true', label: 'Yes' },
                  { value: 'false', label: 'No' }
                ]}
                disabled={isApproved}
              />
            </div>
          </div>

          <div className="review-section">
            <h2>Notes</h2>
            <div className="review-grid review-grid-full">
              <Input 
                label="Internal Notes" 
                value={tx.notes || ''} 
                onChange={(e) => handleChange('notes', e.target.value)} 
                disabled={isApproved}
              />
            </div>
          </div>

          <div className="review-actions">
            {hasChanges && <span className="unsaved-indicator">Unsaved changes</span>}
            {saveSuccess && <span style={{ color: '#059669', display: 'flex', alignItems: 'center', gap: '0.25rem' }}><Check size={16}/> Saved</span>}
            
            {!isApproved && (
              <>
                <Button variant="outline" onClick={handleSave} disabled={isSaving || !hasChanges}>
                  {isSaving ? 'Saving...' : 'Save Changes'}
                </Button>
                <Button variant="primary" onClick={handleApprove} disabled={isApproving}>
                  {isApproving ? 'Approving...' : 'Approve Transaction'}
                </Button>
              </>
            )}
          </div>

        </div>
      </div>
    </div>
  );
};

export default ReviewPage;
