'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Header } from '@/components/Header';
import { KpiSummary } from '@/components/KpiSummary';
import { PaymentQueue } from '@/components/PaymentQueue';
import { PaymentDetailDrawer } from '@/components/PaymentDetailDrawer';
import { HumanApprovalsQueue } from '@/components/HumanApprovalsQueue';
import { AuditTrailModal } from '@/components/AuditTrailModal';
import { BatchEvaluationView } from '@/components/BatchEvaluationView';
import { MerchantAssistant } from '@/components/MerchantAssistant';
import { AlertCircle } from 'lucide-react';

import {
  fetchPayments,
  fetchPaymentDetail,
  executeRecovery,
  approveRecovery,
  rejectRecovery,
  fetchAuditTrail,
  fetchMetrics,
  triggerBatchRun
} from '@/lib/api';

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState<'queue' | 'approvals' | 'evaluation'>('queue');
  const [payments, setPayments] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<any>({});
  const [selectedPaymentDetail, setSelectedPaymentDetail] = useState<any>(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);

  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [auditPaymentId, setAuditPaymentId] = useState<string>('');
  const [isAuditOpen, setIsAuditOpen] = useState(false);

  const [isChatOpen, setIsChatOpen] = useState(false);

  const [isLoading, setIsLoading] = useState(true);
  const [isExecuting, setIsExecuting] = useState(false);
  const [isProcessingBatch, setIsProcessingBatch] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const loadDashboardData = useCallback(async (search = '', failureClass = '', status = '') => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const [payRes, metRes] = await Promise.all([
        fetchPayments(status, failureClass, search, 100),
        fetchMetrics()
      ]);
      if (payRes?.payments) setPayments(payRes.payments);
      if (metRes) setMetrics(metRes);
    } catch (e: any) {
      console.error('Error loading dashboard data:', e);
      setErrorMessage('Could not connect to backend server. Please verify backend is running on http://localhost:8000.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  const handleSearch = (term: string, failureClass: string, status: string) => {
    loadDashboardData(term, failureClass, status);
  };

  const handleSelectPayment = async (paymentId: string) => {
    setErrorMessage(null);
    try {
      const detail = await fetchPaymentDetail(paymentId);
      if (detail) {
        setSelectedPaymentDetail(detail);
        setIsDetailOpen(true);
      } else {
        setErrorMessage(`Could not load details for payment ${paymentId}.`);
      }
    } catch (e: any) {
      console.error('Error fetching detail:', e);
      setErrorMessage(`Error fetching details: ${e.message}`);
    }
  };

  const handleExecuteRecovery = async (paymentId: string) => {
    setIsExecuting(true);
    setErrorMessage(null);
    try {
      const res = await executeRecovery(paymentId, false);
      
      // Real-time local state update
      setPayments((prev) =>
        prev.map((p) => {
          if (p.payment_id === paymentId) {
            if (res?.status === 'SUCCESS') {
              return { ...p, status: 'RECOVERED', recovered: true };
            } else if (res?.status === 'PENDING_HUMAN_APPROVAL') {
              return { ...p, status: 'PENDING_APPROVAL' };
            }
          }
          return p;
        })
      );
      
      await loadDashboardData();
      setIsDetailOpen(false);
    } catch (e: any) {
      console.error('Error executing recovery:', e);
      setErrorMessage(`Error executing recovery action: ${e.message}`);
    } finally {
      setIsExecuting(false);
    }
  };

  const handleApprove = async (paymentId: string) => {
    setIsExecuting(true);
    setErrorMessage(null);
    try {
      await approveRecovery(paymentId, 'Approved via Merchant Dashboard');
      setPayments((prev) =>
        prev.map((p) => (p.payment_id === paymentId ? { ...p, status: 'RECOVERED', recovered: true } : p))
      );
      await loadDashboardData();
    } catch (e: any) {
      console.error('Error approving:', e);
      setErrorMessage(`Error approving recovery: ${e.message}`);
    } finally {
      setIsExecuting(false);
    }
  };

  const handleReject = async (paymentId: string) => {
    setIsExecuting(true);
    setErrorMessage(null);
    try {
      await rejectRecovery(paymentId, 'Rejected via Merchant Dashboard');
      setPayments((prev) =>
        prev.map((p) => (p.payment_id === paymentId ? { ...p, status: 'REJECTED' } : p))
      );
      await loadDashboardData();
    } catch (e: any) {
      console.error('Error rejecting:', e);
      setErrorMessage(`Error rejecting recovery: ${e.message}`);
    } finally {
      setIsExecuting(false);
    }
  };

  const handleOpenAudit = async (paymentId: string) => {
    setErrorMessage(null);
    try {
      const res = await fetchAuditTrail(paymentId);
      setAuditPaymentId(paymentId);
      setAuditLogs(res?.logs || []);
      setIsAuditOpen(true);
    } catch (e: any) {
      console.error('Error opening audit trail:', e);
      setErrorMessage(`Error loading audit trail: ${e.message}`);
    }
  };

  const handleTriggerBatch = async () => {
    setIsProcessingBatch(true);
    setErrorMessage(null);
    try {
      await triggerBatchRun(1000);
      await loadDashboardData();
    } catch (e: any) {
      console.error('Error running batch:', e);
      setErrorMessage(`Error running batch evaluation: ${e.message}`);
    } finally {
      setIsProcessingBatch(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-sky-600 selection:text-white">
      
      {/* Header */}
      <Header
        activeTab={activeTab}
        setActiveTab={(t) => setActiveTab(t as any)}
        toggleChat={() => setIsChatOpen(true)}
        onRefresh={() => loadDashboardData()}
        isRefreshing={isLoading}
      />

      <main className="max-w-7xl mx-auto px-6 py-6">
        
        {/* Error Banner */}
        {errorMessage && (
          <div className="mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 flex items-center justify-between text-xs font-semibold">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>{errorMessage}</span>
            </div>
            <button
              onClick={() => setErrorMessage(null)}
              className="text-rose-400 hover:text-rose-200"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Executive KPI Summary */}
        <KpiSummary metrics={metrics.batch_metrics || {}} />

        {/* Tab Views */}
        {activeTab === 'queue' && (
          <PaymentQueue
            payments={payments}
            onSelectPayment={handleSelectPayment}
            onQuickRecover={handleExecuteRecovery}
            onOpenAudit={handleOpenAudit}
            onSearch={handleSearch}
            isLoading={isLoading}
          />
        )}

        {activeTab === 'approvals' && (
          <HumanApprovalsQueue
            payments={payments}
            onApprove={handleApprove}
            onReject={handleReject}
            isProcessing={isExecuting}
          />
        )}

        {activeTab === 'evaluation' && (
          <BatchEvaluationView
            metricsData={metrics}
            onTriggerBatch={handleTriggerBatch}
            isProcessingBatch={isProcessingBatch}
          />
        )}

      </main>

      {/* Payment Detail & Diagnosis Drawer */}
      <PaymentDetailDrawer
        isOpen={isDetailOpen}
        onClose={() => setIsDetailOpen(false)}
        detailData={selectedPaymentDetail}
        onExecute={handleExecuteRecovery}
        isExecuting={isExecuting}
      />

      {/* Audit Trail Modal */}
      <AuditTrailModal
        isOpen={isAuditOpen}
        onClose={() => setIsAuditOpen(false)}
        paymentId={auditPaymentId}
        auditLogs={auditLogs}
      />

      {/* Merchant AI Assistant Chat Drawer */}
      <MerchantAssistant
        isOpen={isChatOpen}
        onClose={() => setIsChatOpen(false)}
      />

    </div>
  );
}
