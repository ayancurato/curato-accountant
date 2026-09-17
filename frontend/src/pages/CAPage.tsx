import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from '../components/ui/Card';
import { getCAReadiness, downloadCAPack, uploadDocuments, updateTransaction } from '../api/client';
import { AlertCircle, CheckCircle, FileText, Download, Upload } from 'lucide-react';

const MetricCard = ({ title, amount, icon: Icon, color }: { title: string, amount: number, icon: any, color: string }) => (
  <Card noPadding>
    <div style={{ padding: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem', borderLeft: `4px solid ${color}` }}>
      <div style={{ backgroundColor: `${color}15`, padding: '1rem', borderRadius: '50%', color: color }}>
        <Icon size={24} />
      </div>
      <div>
        <h3 style={{ fontSize: '0.875rem', color: '#64748b', margin: 0, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{title}</h3>
        <p style={{ fontSize: '1.5rem', fontWeight: 600, margin: '0.25rem 0 0', color: '#0f172a' }}>{amount}</p>
      </div>
    </div>
  </Card>
);

const ExceptionList = ({ title, exceptions, onReview, onUpload }: { title: string, exceptions: any[], onReview: (id: string) => void, onUpload?: (id: string, type: string, e: React.ChangeEvent<HTMLInputElement>) => void }) => {
  if (!exceptions || exceptions.length === 0) return null;
  return (
    <Card>
      <h3 style={{ fontSize: '1.125rem', fontWeight: 600, color: '#0f172a', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <AlertCircle size={20} color="#ef4444" />
        {title} ({exceptions.length})
      </h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        {exceptions.map((tx: any) => (
          <div key={tx.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem', backgroundColor: '#f8fafc', borderRadius: '0.375rem' }}>
            <div>
              <div style={{ fontWeight: 500, color: '#334155' }}>{tx.vendor_customer}</div>
              <div style={{ fontSize: '0.875rem', color: '#64748b' }}>{tx.date || 'No Date'} • ₹{tx.total_amount}</div>
            </div>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              {onUpload && (
                <label style={{ cursor: 'pointer', padding: '0.25rem 0.75rem', backgroundColor: '#f1f5f9', color: '#334155', borderRadius: '0.25rem', fontSize: '0.875rem', display: 'flex', alignItems: 'center', gap: '0.25rem', fontWeight: 500 }}>
                  <Upload size={14} /> Attach Doc
                  <input type="file" style={{ display: 'none' }} accept=".pdf,.png,.jpg,.jpeg" onChange={(e) => onUpload(tx.id, tx.type, e)} />
                </label>
              )}
              <button 
                onClick={() => onReview(tx.id)}
                style={{ padding: '0.25rem 0.75rem', backgroundColor: '#0f172a', color: 'white', border: 'none', borderRadius: '0.25rem', fontSize: '0.875rem', cursor: 'pointer' }}
              >
                Review
              </button>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
};

export const CAPage: React.FC = () => {
  const navigate = useNavigate();
  const [preset, setPreset] = useState('financial_year');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState('');

  const loadData = async () => {
    try {
      setLoading(true);
      setError('');
      const token = localStorage.getItem('token') || '';
      const params: Record<string, string> = {};
      if (preset === 'custom') {
        if (dateFrom) params.start_date = dateFrom;
        if (dateTo) params.end_date = dateTo;
      } else {
        params.preset = preset;
      }
      
      const result = await getCAReadiness(token, params);
      setData(result);
    } catch (err: any) {
      setError(err.message || 'Failed to load CA readiness');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [preset, dateFrom, dateTo]);

  const handleExport = async () => {
    try {
      setExporting(true);
      setError('');
      const token = localStorage.getItem('token') || '';
      const params: Record<string, string> = {};
      if (preset === 'custom') {
        if (dateFrom) params.start_date = dateFrom;
        if (dateTo) params.end_date = dateTo;
      } else {
        params.preset = preset;
      }
      await downloadCAPack(token, params);
    } catch (err: any) {
      setError(err.message || 'Export failed');
    } finally {
      setExporting(false);
    }
  };

  const handleUploadMissingDoc = async (id: string, type: string, e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    try {
      setLoading(true);
      const token = localStorage.getItem('token') || '';
      const files = Array.from(e.target.files);
      const docs = await uploadDocuments(token, files);
      if (docs && docs.length > 0) {
        await updateTransaction(token, id, type, { document_id: docs[0].id });
        await loadData();
      }
    } catch (err: any) {
      setError(err.message || 'Failed to upload document');
      setLoading(false);
    }
  };

  const isReady = data && data.needs_review_count === 0 && data.missing_documents_count === 0;

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto', paddingBottom: '3rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2rem' }}>
        <div>
          <h1 style={{ fontSize: '1.875rem', fontWeight: 600, color: '#0f172a', margin: '0 0 0.5rem 0' }}>CA Readiness</h1>
          <p style={{ color: '#64748b', margin: 0 }}>Review exceptions and generate your CA Pack</p>
        </div>
        
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', backgroundColor: 'white', padding: '1rem', borderRadius: '0.5rem', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#64748b', margin: '0 0 0.25rem 0' }}>PERIOD</label>
            <select 
              value={preset} 
              onChange={e => setPreset(e.target.value)}
              style={{ padding: '0.5rem', borderRadius: '0.375rem', border: '1px solid #cbd5e1', outline: 'none' }}
            >
              <option value="this_month">This Month</option>
              <option value="this_quarter">This Quarter</option>
              <option value="financial_year">Financial Year</option>
              <option value="custom">Custom Range</option>
            </select>
          </div>
          
          {preset === 'custom' && (
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#64748b', margin: '0 0 0.25rem 0' }}>FROM</label>
                <input type="date" value={dateFrom} onChange={e => setDateFrom(e.target.value)} style={{ padding: '0.5rem', borderRadius: '0.375rem', border: '1px solid #cbd5e1', outline: 'none' }} />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#64748b', margin: '0 0 0.25rem 0' }}>TO</label>
                <input type="date" value={dateTo} onChange={e => setDateTo(e.target.value)} style={{ padding: '0.5rem', borderRadius: '0.375rem', border: '1px solid #cbd5e1', outline: 'none' }} />
              </div>
            </div>
          )}

          <button
            onClick={handleExport}
            disabled={exporting || loading}
            style={{ padding: '0.75rem 1.5rem', backgroundColor: '#0ea5e9', color: 'white', border: 'none', borderRadius: '0.5rem', fontWeight: 600, cursor: (exporting || loading) ? 'not-allowed' : 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
          >
            <Download size={18} />
            {exporting ? 'Generating...' : 'Generate CA Pack'}
          </button>
        </div>
      </div>

      {error && (
        <div style={{ padding: '1rem', backgroundColor: '#fef2f2', color: '#b91c1c', borderRadius: '0.5rem', marginBottom: '1.5rem', border: '1px solid #f87171' }}>
          {error}
        </div>
      )}

      {loading && !data && (
        <div style={{ textAlign: 'center', padding: '3rem', color: '#64748b' }}>Loading readiness data...</div>
      )}

      {data && (
        <>
          {isReady ? (
            <div style={{ backgroundColor: '#f0fdf4', border: '1px solid #86efac', padding: '1.5rem', borderRadius: '0.5rem', marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '1rem', color: '#166534' }}>
              <CheckCircle size={32} />
              <div>
                <h2 style={{ fontSize: '1.25rem', fontWeight: 600, margin: '0 0 0.25rem 0' }}>Ready for Export</h2>
                <p style={{ margin: 0, fontSize: '0.875rem' }}>All transactions in this period have been reviewed and have supporting documents.</p>
              </div>
            </div>
          ) : (
            <div style={{ backgroundColor: '#fffbeb', border: '1px solid #fde047', padding: '1.5rem', borderRadius: '0.5rem', marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '1rem', color: '#854d0e' }}>
              <AlertCircle size={32} />
              <div>
                <h2 style={{ fontSize: '1.25rem', fontWeight: 600, margin: '0 0 0.25rem 0' }}>Exceptions Found</h2>
                <p style={{ margin: 0, fontSize: '0.875rem' }}>We recommend resolving these exceptions before sending the pack to your CA.</p>
              </div>
            </div>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '1rem', marginBottom: '2rem' }}>
            <MetricCard title="Total" amount={data.transaction_count} icon={FileText} color="#0ea5e9" />
            <MetricCard title="Needs Review" amount={data.needs_review_count} icon={AlertCircle} color={data.needs_review_count > 0 ? '#ef4444' : '#22c55e'} />
            <MetricCard title="Missing Docs" amount={data.missing_documents_count} icon={AlertCircle} color={data.missing_documents_count > 0 ? '#f97316' : '#22c55e'} />
            <MetricCard title="Duplicates" amount={data.potential_duplicates_count} icon={AlertCircle} color={data.potential_duplicates_count > 0 ? '#eab308' : '#22c55e'} />
            <MetricCard title="GST Issues" amount={data.gst_issues_count} icon={AlertCircle} color={data.gst_issues_count > 0 ? '#ef4444' : '#22c55e'} />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <ExceptionList title="Needs Review" exceptions={data.needs_review} onReview={(id) => navigate(`/review/${id}`)} />
            <ExceptionList title="Missing Documents" exceptions={data.missing_documents} onReview={(id) => navigate(`/review/${id}`)} onUpload={handleUploadMissingDoc} />
            <ExceptionList title="Potential Duplicates" exceptions={data.potential_duplicates} onReview={(id) => navigate(`/review/${id}`)} />
            <ExceptionList title="GST Issues" exceptions={data.gst_issues} onReview={(id) => navigate(`/review/${id}`)} />
          </div>
        </>
      )}
    </div>
  );
};

export default CAPage;
