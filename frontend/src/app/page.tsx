'use client';

import React, { useState, useEffect } from 'react';
import { Header } from '@/components/Header';
import { KpiSummary } from '@/components/KpiSummary';
import { PaymentQueue } from '@/components/PaymentQueue';
import { PaymentDetailDrawer } from '@/components/PaymentDetailDrawer';
import { HumanApprovalsQueue } from '@/components/HumanApprovalsQueue';
import { AuditTrailModal } from '@/components/AuditTrailModal';
import { BatchEvaluationView } from '@/components/BatchEvaluationView';
import { MerchantAssistant } from '@/components/MerchantAssistant';

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

  const loadDashboardData = async () => {
    setIsLoading(true);
    try {
      const [payRes, metRes] = await Promise.all([
        fetchPayments('', '', '', 100),
        fetchMetrics()
      ]);
      if (payRes?.payments) setPayments(payRes.payments);
      if (metRes) setMetrics(metRes);
    } catch (e) {
      console.error('Error loading dashboard data:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const handleSelectPayment = async (paymentId: string) => {
    try {
      const detail = await fetchPaymentDetail(paymentId);
      setSelectedPaymentDetail(detail);
      setIsDetailOpen(true);
    } catch (e) {
      console.error('Error fetching detail:', e);
    }
  };

  const handleExecuteRecovery = async (paymentId: string) => {
    setIsExecuting(true);
    try {
      await executeRecovery(paymentId, false);
      await loadDashboardData();
      setIsDetailOpen(false);
    } catch (e) {
      console.error('Error executing recovery:', e);
    } finally {
      setIsExecuting(false);
    }
  };

  const handleApprove = async (paymentId: string) => {
    setIsExecuting(true);
    try {
      await approveRecovery(paymentId, 'Approved via Merchant Dashboard');
      await loadDashboardData();
    } catch (e) {
      console.error('Error approving:', e);
    } finally {
      setIsExecuting(false);
    }
  };

  const handleReject = async (paymentId: string) => {
    setIsExecuting(true);
    try {
      await rejectRecovery(paymentId, 'Rejected via Merchant Dashboard');
      await loadDashboardData();
    } catch (e) {
      console.error('Error rejecting:', e);
    } finally {
      setIsExecuting(false);
    }
  };

  const handleOpenAudit = async (paymentId: string) => {
    try {
      const res = await fetchAuditTrail(paymentId);
      setAuditPaymentId(paymentId);
      setAuditLogs(res.logs || []);
      setIsAuditOpen(true);
    } catch (e) {
      console.error('Error opening audit trail:', e);
    }
  };

  const handleTriggerBatch = async () => {
    setIsProcessingBatch(true);
    try {
      await triggerBatchRun(1000);
      await loadDashboardData();
    } catch (e) {
      console.error('Error running batch:', e);
    } finally {
      setIsProcessingBatch(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-blue-600 selection:text-white">
      
      {/* Header */}
      <Header
        activeTab={activeTab}
        setActiveTab={(t) => setActiveTab(t as any)}
        toggleChat={() => setIsChatOpen(true)}
        onRefresh={loadDashboardData}
        isRefreshing={isLoading}
      />

      <main className="max-w-7xl mx-auto px-6 py-8">
        
        {/* Executive KPI Summary */}
        <KpiSummary metrics={metrics.batch_metrics || {}} />

        {/* Tab Views */}
        {activeTab === 'queue' && (
          <PaymentQueue
            payments={payments}
            onSelectPayment={handleSelectPayment}
            onQuickRecover={handleExecuteRecovery}
            onOpenAudit={handleOpenAudit}
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
