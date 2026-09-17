import React, { useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { UploadCloud, File, AlertCircle, CheckCircle, FileText, XCircle, RefreshCw, Shield, Zap, FileCheck } from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { uploadDocuments, processDocument } from '../api/client';
import { useAuth } from '../context/AuthContext';
import './UploadPage.css';

type FileStatus = 'IDLE' | 'UPLOADING' | 'PROCESSING' | 'READY' | 'NEEDS_REVIEW' | 'ERROR';

interface FileState {
  id: string; // internal ui id
  file: File;
  status: FileStatus;
  documentId?: string;
  transactionId?: string;
  documentStatus?: string;
  transactionStatus?: string;
  error?: string;
  anomalies?: { type: string; message: string }[];
}

const formatAnomalyMessage = (anomaly: { type: string; message: string }) => {
  switch (anomaly.type) {
    case 'MISSING_GSTIN': return 'GSTIN is missing';
    case 'DUPLICATE_TRANSACTION': return 'Potential duplicate detected';
    case 'GST_MISMATCH': return 'GST amount does not match the invoice totals';
    case 'MISSING_INVOICE_NUMBER': return 'Invoice number missing';
    case 'CATEGORY_MISSING': return 'Category could not be determined';
    default: return anomaly.message || anomaly.type;
  }
};

const MAX_SIZE_MB = 20;

const UploadPage: React.FC = () => {
  const [files, setFiles] = useState<FileState[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { token } = useAuth();
  const navigate = useNavigate();

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const processFile = async (fileState: FileState) => {
    if (!token) return;
    
    // Update status to UPLOADING
    setFiles(prev => prev.map(f => f.id === fileState.id ? { ...f, status: 'UPLOADING', error: undefined } : f));
    
    try {
      // 1. Upload
      const uploadRes = await uploadDocuments(token, [fileState.file]);
      if (!uploadRes || uploadRes.length === 0) throw new Error('Upload failed');
      
      const doc = uploadRes[0];
      setFiles(prev => prev.map(f => f.id === fileState.id ? { 
        ...f, 
        documentId: doc.id, 
        status: 'PROCESSING' 
      } : f));

      // 2. Process (Synchronous)
      const processRes = await processDocument(token, doc.id);
      
      setFiles(prev => prev.map(f => f.id === fileState.id ? { 
        ...f, 
        status: processRes.document_status as FileStatus,
        documentStatus: processRes.document_status,
        transactionStatus: processRes.transaction_status,
        transactionId: processRes.transaction_id,
        anomalies: processRes.anomalies
      } : f));

    } catch (err: any) {
      setFiles(prev => prev.map(f => f.id === fileState.id ? { 
        ...f, 
        status: 'ERROR', 
        error: err.message || 'An unknown error occurred' 
      } : f));
    }
  };

  const handleFilesSelected = (selectedFiles: FileList | null) => {
    if (!selectedFiles) return;

    const newFiles: FileState[] = Array.from(selectedFiles).map(file => {
      // Validate
      const ext = file.name.split('.').pop()?.toLowerCase();
      const isValidType = ['pdf', 'jpg', 'jpeg', 'png'].includes(ext || '');
      const isValidSize = file.size <= MAX_SIZE_MB * 1024 * 1024;
      
      let error;
      if (!isValidType) error = 'Unsupported file type. Use PDF, JPG, or PNG.';
      else if (!isValidSize) error = `File is too large (Max ${MAX_SIZE_MB}MB).`;

      return {
        id: Math.random().toString(36).substring(2, 9),
        file,
        status: error ? 'ERROR' : 'IDLE',
        error
      };
    });

    setFiles(prev => [...prev, ...newFiles]);
    setIsDragging(false);

    // Auto start valid ones
    newFiles.filter(f => f.status === 'IDLE').forEach(processFile);
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFilesSelected(e.dataTransfer.files);
  }, []);

  const handleRetry = (fileState: FileState) => {
    processFile(fileState);
  };

  return (
    <div className="upload-page-wrapper">
      <div className="bg-decor top-left"></div>
      <div className="bg-decor bottom-right"></div>

      <div className="upload-container">
        <div className="upload-header">
          <div className="eyebrow">DOCUMENT UPLOAD</div>
          <h1>Upload your invoices & receipts</h1>
          <p className="subtitle">Drop your documents below to automatically extract and validate them.</p>
        </div>

        <div className="upload-card-wrapper">
          <div 
            className={`upload-dropzone ${isDragging ? 'drag-active' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <div className="dropzone-decor drop-top-left"></div>
            <div className="dropzone-decor drop-bottom-right"></div>
            
            <div className="upload-icon-wrapper">
              <UploadCloud className="upload-icon" />
            </div>
            
            <div className="upload-title">Drag & drop files here</div>
            <div className="upload-or">or</div>
            
            <button className="btn-browse" onClick={() => fileInputRef.current?.click()}>
              Browse files
            </button>
            
            <div className="upload-formats">Supported formats: PDF, JPG, JPEG, PNG (Max {MAX_SIZE_MB}MB)</div>
            
            <input 
              type="file" 
              ref={fileInputRef} 
              multiple 
              accept=".pdf,.jpg,.jpeg,.png" 
              onChange={(e) => handleFilesSelected(e.target.files)}
              className="hidden-input"
            />
          </div>
        </div>

        <div className="features-row">
          <div className="feature-item">
            <div className="feature-icon feature-icon-green"><FileText size={24} /></div>
            <div className="feature-text">
              <h3>Automatic extraction</h3>
              <p>We extract key details for you</p>
            </div>
          </div>
          <div className="feature-divider"></div>
          <div className="feature-item">
            <div className="feature-icon feature-icon-blue"><Shield size={24} /></div>
            <div className="feature-text">
              <h3>Secure & private</h3>
              <p>Your data is always protected</p>
            </div>
          </div>
          <div className="feature-divider"></div>
          <div className="feature-item">
            <div className="feature-icon feature-icon-purple"><Zap size={24} /></div>
            <div className="feature-text">
              <h3>Saves time</h3>
              <p>No manual data entry</p>
            </div>
          </div>
          <div className="feature-divider"></div>
          <div className="feature-item">
            <div className="feature-icon feature-icon-orange"><FileCheck size={24} /></div>
            <div className="feature-text">
              <h3>Multiple formats</h3>
              <p>PDF, JPG, JPEG, PNG</p>
            </div>
          </div>
        </div>

        {files.length > 0 && (
          <div className="upload-list-wrapper">
            <Card>
              <div className="upload-list-header">Uploaded Documents</div>
          <div className="upload-list">
            {files.map(fs => (
              <div key={fs.id} className="upload-item">
                <div className="upload-item-main">
                  <div className="upload-item-info">
                    <div className={`upload-item-icon ${fs.status === 'ERROR' ? 'upload-item-icon-error' : fs.status === 'READY' ? 'upload-item-icon-success' : ''}`}>
                      {fs.file.type.includes('pdf') ? <FileText size={20} /> : <File size={20} />}
                    </div>
                    <div className="upload-item-details">
                      <div className="upload-item-name">{fs.file.name}</div>
                      <div className="upload-item-meta">{(fs.file.size / 1024 / 1024).toFixed(2)} MB • {fs.file.type || 'Unknown type'}</div>
                    </div>
                  </div>
                  
                  <div className="upload-item-actions">
                    <div className="upload-item-statuses">
                      {['IDLE', 'UPLOADING', 'PROCESSING'].includes(fs.status) && (
                        <Badge status="PROCESSING">{fs.status === 'IDLE' ? 'Waiting' : fs.status.toLowerCase()}</Badge>
                      )}
                      
                      {fs.documentStatus && (
                        <Badge status={fs.documentStatus as any}>
                          Document: {fs.documentStatus.replace('_', ' ')}
                        </Badge>
                      )}

                      {fs.transactionStatus && (
                        <Badge status={fs.transactionStatus as any}>
                          Transaction: {fs.transactionStatus.replace('_', ' ')}
                        </Badge>
                      )}
                      
                      {fs.status === 'ERROR' && (
                        <Badge status="ERROR">Failed</Badge>
                      )}
                    </div>
                    
                    {fs.status === 'NEEDS_REVIEW' && fs.transactionId && (
                      <Button size="sm" onClick={() => navigate(`/review/${fs.transactionId}`)}>
                        Review Transaction
                      </Button>
                    )}
                    
                    {fs.status === 'READY' && fs.transactionId && (
                      <Button size="sm" variant="outline" onClick={() => navigate(`/review/${fs.transactionId}`)}>
                        Review Transaction
                      </Button>
                    )}

                    {fs.status === 'ERROR' && !fs.error?.includes('Unsupported file') && !fs.error?.includes('large') && (
                      <Button size="sm" variant="outline" onClick={() => handleRetry(fs)}>
                        <RefreshCw size={16} style={{ marginRight: '0.25rem' }}/> Retry
                      </Button>
                    )}
                  </div>
                </div>

                {fs.status === 'ERROR' && fs.error && (
                  <div className="upload-item-error">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <XCircle size={16} /> <strong>Error:</strong> {fs.error}
                    </div>
                  </div>
                )}

                {fs.status === 'NEEDS_REVIEW' && fs.anomalies && fs.anomalies.length > 0 && (
                  <div className="upload-item-anomalies">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 500 }}>
                      <AlertCircle size={16} /> Needs Attention
                    </div>
                    <ul>
                      {fs.anomalies.map((a, i) => (
                        <li key={i}>{formatAnomalyMessage(a)}</li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {fs.status === 'READY' && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.5rem', fontSize: '0.875rem', color: 'var(--status-ready-text)' }}>
                    <CheckCircle size={16} /> Invoice successfully processed
                  </div>
                )}
              </div>
            ))}
          </div>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
};

export default UploadPage;
