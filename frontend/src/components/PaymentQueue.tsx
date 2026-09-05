'use client';

import React, { useState } from 'react';
import { Search, Filter, AlertTriangle, ArrowRight, ShieldAlert, CheckCircle2, History } from 'lucide-react';

interface PaymentQueueProps {
  payments: any[];
  onSelectPayment: (paymentId: string) => void;
  onQuickRecover: (paymentId: string) => void;
  onOpenAudit: (paymentId: string) => void;
  isLoading: boolean;
}

export const PaymentQueue: React.FC<PaymentQueueProps> = ({
  payments,
  onSelectPayment,
  onQuickRecover,
  onOpenAudit,
  isLoading
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [failureFilter, setFailureFilter] = useState('');

  const filteredPayments = payments.filter((p) => {
    const matchesSearch =
      p.payment_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.customer_id.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = failureFilter ? p.failure_class === failureFilter : true;
    return matchesSearch && matchesFilter;
  });

  const getCauseBadge = (cause: string) => {
    switch (cause) {
      case 'TEMPORARY_BANK_FAILURE':
        return <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-sky-500/10 text-sky-400 border border-sky-500/20">Bank Downtime</span>;
      case 'PAYMENT_METHOD_FAILURE':
        return <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">Card/UPI Issue</span>;
      case 'CUSTOMER_ABANDONMENT':
        return <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">User Drop-off</span>;
      case 'INSUFFICIENT_FUNDS':
        return <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">Low Balance</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-800 text-slate-400 border border-slate-700">Unknown</span>;
    }
  };

  const getStatusBadge = (status: string, recovered: boolean) => {
    if (recovered || status === 'RECOVERED') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <CheckCircle2 className="w-3 h-3" /> Recovered
        </span>
      );
    }
    if (status === 'PENDING_APPROVAL') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-[11px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
          <ShieldAlert className="w-3 h-3" /> Needs Approval
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-[11px] font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
        <AlertTriangle className="w-3 h-3" /> At Risk
      </span>
    );
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
      
      {/* Controls Bar */}
      <div className="p-4 border-b border-slate-800 flex flex-col md:flex-row items-center justify-between gap-3 bg-slate-900/60">
        
        {/* Search */}
        <div className="relative w-full md:w-80">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search payment ID or customer ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500 transition-colors"
          />
        </div>

        {/* Filter dropdown */}
        <div className="flex items-center gap-2 w-full md:w-auto justify-end">
          <Filter className="w-3.5 h-3.5 text-slate-400" />
          <select
            value={failureFilter}
            onChange={(e) => setFailureFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-sky-500"
          >
            <option value="">All Failure Classes</option>
            <option value="TEMPORARY_BANK_FAILURE">Temporary Bank Failure</option>
            <option value="PAYMENT_METHOD_FAILURE">Payment Method Failure</option>
            <option value="CUSTOMER_ABANDONMENT">Customer Abandonment</option>
            <option value="INSUFFICIENT_FUNDS">Insufficient Funds</option>
            <option value="UNKNOWN">Unknown</option>
          </select>
        </div>

      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-slate-950 text-slate-400 font-semibold uppercase tracking-wider border-b border-slate-800">
            <tr>
              <th className="px-5 py-3">Payment ID & Customer</th>
              <th className="px-5 py-3">Amount</th>
              <th className="px-5 py-3">Root Cause Diagnosis</th>
              <th className="px-5 py-3">Method & Bank</th>
              <th className="px-5 py-3">Status</th>
              <th className="px-5 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {isLoading ? (
              <tr>
                <td colSpan={6} className="text-center py-10 text-slate-500">
                  Loading recovery transactions...
                </td>
              </tr>
            ) : filteredPayments.length === 0 ? (
              <tr>
                <td colSpan={6} className="text-center py-10 text-slate-500">
                  No payment records matching search query.
                </td>
              </tr>
            ) : (
              filteredPayments.map((p) => (
                <tr key={p.payment_id} className="hover:bg-slate-800/40 transition-colors">
                  
                  {/* Payment & Customer */}
                  <td className="px-5 py-3">
                    <div className="font-mono font-bold text-slate-200">{p.payment_id}</div>
                    <div className="text-[11px] text-slate-500">{p.customer_id}</div>
                  </td>

                  {/* Amount */}
                  <td className="px-5 py-3 font-bold text-slate-100">
                    ₹{p.amount.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                  </td>

                  {/* Failure Class */}
                  <td className="px-5 py-3">
                    {getCauseBadge(p.failure_class)}
                  </td>

                  {/* Method & Bank */}
                  <td className="px-5 py-3 text-slate-400">
                    <span className="uppercase font-medium text-slate-300">{p.payment_method}</span> ({p.bank})
                  </td>

                  {/* Status */}
                  <td className="px-5 py-3">
                    {getStatusBadge(p.status, p.recovered)}
                  </td>

                  {/* Actions */}
                  <td className="px-5 py-3 text-right space-x-1.5">
                    <button
                      onClick={() => onOpenAudit(p.payment_id)}
                      className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded transition-colors inline-flex items-center gap-1"
                      title="View Audit Trail Timeline"
                    >
                      <History className="w-3.5 h-3.5" />
                    </button>

                    <button
                      onClick={() => onSelectPayment(p.payment_id)}
                      className="px-2.5 py-1 rounded text-xs font-semibold bg-sky-600/20 hover:bg-sky-600/30 text-sky-400 border border-sky-500/30 transition-colors inline-flex items-center gap-1"
                    >
                      Inspect & Recover
                      <ArrowRight className="w-3 h-3" />
                    </button>
                  </td>

                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

    </div>
  );
};
