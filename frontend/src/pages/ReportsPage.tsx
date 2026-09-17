import React, { useState, useEffect } from 'react';
import { Card } from '../components/ui/Card';
import { getReports } from '../api/client';
import { DollarSign, TrendingUp, TrendingDown, Clock, Scale } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const formatCurrency = (amount: number | string) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR'
  }).format(Number(amount));
};

const formatMonth = (monthStr: string) => {
  if (!monthStr) return '';
  const [y, m] = monthStr.split('-');
  const date = new Date(parseInt(y), parseInt(m) - 1, 1);
  return date.toLocaleString('en-IN', { month: 'long', year: 'numeric' });
};

const MetricCard = ({ title, amount, icon: Icon, color }: { title: string, amount: number, icon: any, color: string }) => (
  <Card noPadding>
    <div style={{ padding: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem', borderLeft: `4px solid ${color}` }}>
      <div style={{ backgroundColor: `${color}15`, padding: '1rem', borderRadius: '50%', color: color }}>
        <Icon size={24} />
      </div>
      <div>
        <h3 style={{ fontSize: '0.875rem', color: '#64748b', margin: 0, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{title}</h3>
        <p style={{ fontSize: '1.5rem', fontWeight: 600, margin: '0.25rem 0 0', color: '#0f172a' }}>{formatCurrency(amount)}</p>
      </div>
    </div>
  </Card>
);

const BarChartList = ({ data, labelKey, amountKey, maxAmount }: { data: any[], labelKey: string, amountKey: string, maxAmount: number }) => {
  if (!data || data.length === 0) {
    return <div style={{ padding: '2rem', textAlign: 'center', color: '#94a3b8' }}>No data for this period</div>;
  }
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      {data.map((item, i) => {
        const percentage = maxAmount > 0 ? (Number(item[amountKey]) / maxAmount) * 100 : 0;
        return (
          <div key={i}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem', fontSize: '0.875rem' }}>
              <span style={{ fontWeight: 500, color: '#334155' }}>{item[labelKey]}</span>
              <span style={{ color: '#0f172a' }}>{formatCurrency(item[amountKey])}</span>
            </div>
            <div style={{ width: '100%', height: '8px', backgroundColor: '#e2e8f0', borderRadius: '4px', overflow: 'hidden' }}>
              <div style={{ width: `${percentage}%`, height: '100%', backgroundColor: '#0ea5e9', borderRadius: '4px' }} />
            </div>
          </div>
        );
      })}
    </div>
  );
};

export const ReportsPage: React.FC = () => {
  const { token } = useAuth();
  const [preset, setPreset] = useState('financial_year');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const loadReports = async () => {
    if (!token) return;
    try {
      setLoading(true);
      setError('');
      const params: Record<string, string> = {};
      if (preset === 'custom') {
        if (dateFrom) params.date_from = dateFrom;
        if (dateTo) params.date_to = dateTo;
      } else {
        params.preset = preset;
      }
      
      const result = await getReports(token, params);
      setData(result);
    } catch (err: any) {
      setError(err.message || 'Failed to load reports');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReports();
  }, [preset, dateFrom, dateTo, token]);

  const m = data?.metrics || {
    total_income: 0, total_expenses: 0, net: 0,
    gst_collected: 0, gst_paid: 0, outstanding_income: 0, unpaid_expenses: 0
  };

  const expMaxCat = data?.expenses?.by_category?.reduce((max: number, c: any) => Math.max(max, Number(c.amount)), 0) || 0;
  const expMaxVen = data?.expenses?.by_vendor?.reduce((max: number, c: any) => Math.max(max, Number(c.amount)), 0) || 0;
  const expMaxTrend = data?.expenses?.monthly_trend?.reduce((max: number, c: any) => Math.max(max, Number(c.amount)), 0) || 0;

  const incMaxCat = data?.income?.by_category?.reduce((max: number, c: any) => Math.max(max, Number(c.amount)), 0) || 0;
  const incMaxCus = data?.income?.by_customer?.reduce((max: number, c: any) => Math.max(max, Number(c.amount)), 0) || 0;
  const incMaxTrend = data?.income?.monthly_trend?.reduce((max: number, c: any) => Math.max(max, Number(c.amount)), 0) || 0;

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', paddingBottom: '3rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2rem' }}>
        <div>
          <h1 style={{ fontSize: '1.875rem', fontWeight: 600, color: '#0f172a', margin: '0 0 0.5rem 0' }}>Financial Reports</h1>
          <p style={{ color: '#64748b', margin: 0 }}>Overview of approved transactions and metrics</p>
        </div>
        
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', backgroundColor: 'white', padding: '1rem', borderRadius: '0.5rem', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#64748b', marginBottom: '0.25rem' }}>PERIOD</label>
            <select 
              value={preset} 
              onChange={e => setPreset(e.target.value)}
              style={{ padding: '0.5rem', borderRadius: '0.375rem', border: '1px solid #cbd5e1', outline: 'none' }}
            >
              <option value="this_month">This Month</option>
              <option value="this_quarter">This Quarter</option>
              <option value="financial_year">Financial Year</option>
              <option value="custom">Custom Date Range</option>
            </select>
          </div>
          
          {preset === 'custom' && (
            <>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#64748b', marginBottom: '0.25rem' }}>FROM</label>
                <input type="date" value={dateFrom} onChange={e => setDateFrom(e.target.value)} style={{ padding: '0.5rem', borderRadius: '0.375rem', border: '1px solid #cbd5e1', outline: 'none' }} />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#64748b', marginBottom: '0.25rem' }}>TO</label>
                <input type="date" value={dateTo} onChange={e => setDateTo(e.target.value)} style={{ padding: '0.5rem', borderRadius: '0.375rem', border: '1px solid #cbd5e1', outline: 'none' }} />
              </div>
            </>
          )}
        </div>
      </div>

      {error && (
        <div style={{ backgroundColor: '#fee2e2', color: '#991b1b', padding: '1rem', borderRadius: '0.5rem', marginBottom: '2rem' }}>
          {error}
        </div>
      )}

      {loading && !data ? (
        <div style={{ textAlign: 'center', padding: '3rem', color: '#64748b' }}>Calculating reports...</div>
      ) : (
        <>
          {/* Core Metrics Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1.5rem', marginBottom: '3rem' }}>
            <MetricCard title="Total Income" amount={m.total_income} icon={TrendingUp} color="#10b981" />
            <MetricCard title="Total Expenses" amount={m.total_expenses} icon={TrendingDown} color="#f43f5e" />
            <MetricCard title="Net Income" amount={Math.max(0, m.net)} icon={Scale} color="#3b82f6" />
            <MetricCard title="GST Collected" amount={m.gst_collected} icon={DollarSign} color="#8b5cf6" />
            <MetricCard title="GST Paid" amount={m.gst_paid} icon={DollarSign} color="#f59e0b" />
            <MetricCard title="Outstanding Income" amount={m.outstanding_income} icon={Clock} color="#14b8a6" />
            <MetricCard title="Unpaid Expenses" amount={m.unpaid_expenses} icon={Clock} color="#ef4444" />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
            {/* Income Analysis */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: '#0f172a', margin: 0, borderBottom: '2px solid #e2e8f0', paddingBottom: '0.5rem' }}>Income Analysis</h2>
              
              <Card>
                <div style={{ padding: '0.5rem' }}>
                  <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '1.5rem', color: '#334155' }}>By Customer</h3>
                  <BarChartList data={data?.income?.by_customer || []} labelKey="name" amountKey="amount" maxAmount={incMaxCus} />
                </div>
              </Card>

              <Card>
                <div style={{ padding: '0.5rem' }}>
                  <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '1.5rem', color: '#334155' }}>By Category</h3>
                  <BarChartList data={data?.income?.by_category || []} labelKey="category_name" amountKey="amount" maxAmount={incMaxCat} />
                </div>
              </Card>

              <Card>
                <div style={{ padding: '0.5rem' }}>
                  <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '1.5rem', color: '#334155' }}>Monthly Trend</h3>
                  <BarChartList 
                    data={(data?.income?.monthly_trend || []).map((t: any) => ({ ...t, formattedMonth: formatMonth(t.month) }))} 
                    labelKey="formattedMonth" amountKey="amount" maxAmount={incMaxTrend} 
                  />
                </div>
              </Card>
            </div>

            {/* Expense Analysis */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: '#0f172a', margin: 0, borderBottom: '2px solid #e2e8f0', paddingBottom: '0.5rem' }}>Expense Analysis</h2>
              
              <Card>
                <div style={{ padding: '0.5rem' }}>
                  <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '1.5rem', color: '#334155' }}>By Vendor</h3>
                  <BarChartList data={data?.expenses?.by_vendor || []} labelKey="name" amountKey="amount" maxAmount={expMaxVen} />
                </div>
              </Card>

              <Card>
                <div style={{ padding: '0.5rem' }}>
                  <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '1.5rem', color: '#334155' }}>By Category</h3>
                  <BarChartList data={data?.expenses?.by_category || []} labelKey="category_name" amountKey="amount" maxAmount={expMaxCat} />
                </div>
              </Card>

              <Card>
                <div style={{ padding: '0.5rem' }}>
                  <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '1.5rem', color: '#334155' }}>Monthly Trend</h3>
                  <BarChartList 
                    data={(data?.expenses?.monthly_trend || []).map((t: any) => ({ ...t, formattedMonth: formatMonth(t.month) }))} 
                    labelKey="formattedMonth" amountKey="amount" maxAmount={expMaxTrend} 
                  />
                </div>
              </Card>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default ReportsPage;
