import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getIncomes, getCategories } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../components/ui/Table';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Select } from '../components/ui/Select';
import { Card } from '../components/ui/Card';

const IncomePage: React.FC = () => {
  const navigate = useNavigate();
  const { token } = useAuth();
  
  const [incomes, setIncomes] = useState<any[]>([]);
  const [categories, setCategories] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [status, setStatus] = useState<string>('');
  const [paymentStatus, setPaymentStatus] = useState<string>('');
  const [search, setSearch] = useState<string>('');
  const [dateFrom, setDateFrom] = useState<string>('');
  const [dateTo, setDateTo] = useState<string>('');
  const [categoryId, setCategoryId] = useState<string>('');

  const loadData = async () => {
    if (!token) return;
    try {
      setLoading(true);
      setError(null);
      
      const cats = await getCategories(token);
      setCategories(cats.filter((c: any) => c.type === 'INCOME'));

      const filters: any = {};
      if (status) filters.status = status;
      if (paymentStatus) filters.payment_status = paymentStatus;
      if (search) filters.search = search;
      if (dateFrom) filters.date_from = dateFrom;
      if (dateTo) filters.date_to = dateTo;
      if (categoryId) filters.category_id = categoryId;

      const data = await getIncomes(token, filters);
      setIncomes(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch income transactions');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [token, status, paymentStatus, search, dateFrom, dateTo, categoryId]);

  const getCategoryName = (id: string) => {
    const cat = categories.find(c => c.id === id);
    return cat ? cat.name : 'Uncategorized';
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>Income</h1>
        <Button variant="primary" onClick={() => navigate('/upload')}>+ Add Income</Button>
      </div>

      <Card>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginBottom: '1.5rem' }}>
          <div style={{ flex: '1 1 200px' }}>
            <Input 
              label="Search (Customer, Invoice, Notes)" 
              value={search} 
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search..."
            />
          </div>
          <div style={{ flex: '1 1 150px' }}>
            <Select 
              label="Transaction Status" 
              value={status} 
              onChange={(e) => setStatus(e.target.value)}
              options={[
                { value: '', label: 'All Statuses' },
                { value: 'DRAFT', label: 'Draft' },
                { value: 'NEEDS_REVIEW', label: 'Needs Review' },
                { value: 'APPROVED', label: 'Approved' }
              ]}
            />
          </div>
          <div style={{ flex: '1 1 150px' }}>
            <Select 
              label="Payment Status" 
              value={paymentStatus} 
              onChange={(e) => setPaymentStatus(e.target.value)}
              options={[
                { value: '', label: 'All Payments' },
                { value: 'RECEIVED', label: 'Received' },
                { value: 'OUTSTANDING', label: 'Outstanding' }
              ]}
            />
          </div>
          <div style={{ flex: '1 1 150px' }}>
            <Select 
              label="Category" 
              value={categoryId} 
              onChange={(e) => setCategoryId(e.target.value)}
              options={[
                { value: '', label: 'All Categories' },
                ...categories.map(c => ({ value: c.id, label: c.name }))
              ]}
            />
          </div>
          <div style={{ flex: '1 1 120px' }}>
            <Input 
              label="Date From" 
              type="date"
              value={dateFrom} 
              onChange={(e) => setDateFrom(e.target.value)}
            />
          </div>
          <div style={{ flex: '1 1 120px' }}>
            <Input 
              label="Date To" 
              type="date"
              value={dateTo} 
              onChange={(e) => setDateTo(e.target.value)}
            />
          </div>
        </div>

        {error && (
          <div style={{ backgroundColor: '#FEE2E2', color: '#991B1B', padding: '1rem', borderRadius: '0.5rem', marginBottom: '1rem' }}>
            {error}
          </div>
        )}

        {loading ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: '#6B7280' }}>Loading income transactions...</div>
        ) : incomes.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: '#6B7280', backgroundColor: '#F9FAFB', borderRadius: '0.5rem' }}>
            <p>No income transactions found.</p>
            {search || status || paymentStatus || dateFrom || dateTo || categoryId ? (
              <p style={{ fontSize: '0.875rem', marginTop: '0.5rem' }}>Try adjusting your filters.</p>
            ) : null}
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Date</TableHead>
                <TableHead>Customer</TableHead>
                <TableHead>Invoice #</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>Net</TableHead>
                <TableHead>GST</TableHead>
                <TableHead>Total</TableHead>
                <TableHead>Payment Status</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {incomes.map((tx) => (
                <TableRow key={tx.id} onClick={() => navigate(`/review/${tx.id}`)}>
                  <TableCell>{tx.date || '-'}</TableCell>
                  <TableCell>{tx.vendor_customer || '-'}</TableCell>
                  <TableCell>{tx.invoice_number || '-'}</TableCell>
                  <TableCell>{getCategoryName(tx.category_id)}</TableCell>
                  <TableCell>{parseFloat(tx.net_amount).toLocaleString('en-IN', { style: 'currency', currency: tx.currency || 'INR' })}</TableCell>
                  <TableCell>{parseFloat(tx.gst_amount).toLocaleString('en-IN', { style: 'currency', currency: tx.currency || 'INR' })}</TableCell>
                  <TableCell><strong>{parseFloat(tx.total_amount).toLocaleString('en-IN', { style: 'currency', currency: tx.currency || 'INR' })}</strong></TableCell>
                  <TableCell>
                    {tx.payment_status ? (
                      <span style={{ 
                        display: 'inline-block',
                        padding: '0.25rem 0.5rem', 
                        borderRadius: '9999px', 
                        fontSize: '0.75rem', 
                        fontWeight: '600',
                        backgroundColor: tx.payment_status === 'RECEIVED' ? '#D1FAE5' : '#FEF3C7',
                        color: tx.payment_status === 'RECEIVED' ? '#065F46' : '#92400E'
                      }}>
                        {tx.payment_status}
                      </span>
                    ) : '-'}
                  </TableCell>
                  <TableCell>
                    <Badge status={tx.status}>{tx.status.replace('_', ' ')}</Badge>
                  </TableCell>
                  <TableCell>
                    <Button variant="outline" size="sm" onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/review/${tx.id}`);
                    }}>Review</Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Card>
    </div>
  );
};

export default IncomePage;
