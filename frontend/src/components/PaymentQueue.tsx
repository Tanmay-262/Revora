'use client';

import React, { useState } from 'react';
import { Search, Filter, AlertTriangle, ArrowRight, ShieldAlert, CheckCircle2, History, X } from 'lucide-react';

interface PaymentQueueProps {
  payments: any[];
  onSelectPayment: (paymentId: string) => void;
  onQuickRecover: (paymentId: string) => void;
  onOpenAudit: (paymentId: string) => void;
  onSearch: (term: string, failureClass: string, statusFilter: string) => void;
  isLoading: boolean;
}

export const PaymentQueue: React.FC<PaymentQueueProps> = ({
  payments,
  onSelectPayment,
  onQuickRecover,
  onOpenAudit,
  onSearch,
  isLoading
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [failureFilter, setFailureFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  const handleSearchChange = (term: string) => {
    setSearchTerm(term);
    onSearch(term, failureFilter, statusFilter);
  };

  const handleFailureFilterChange = (fc: string) => {
    setFailureFilter(fc);
    onSearch(searchTerm, fc, statusFilter);
  };

  const handleStatusFilterChange = (st: string) => {
    setStatusFilter(st);
    onSearch(searchTerm, failureFilter, st);
  };

  const clearFilters = () => {
    setSearchTerm('');
    setFailureFilter('');
    setStatusFilter('');
    onSearch('', '', '');
  };

  const filteredPayments = payments.filter((p) => {
    const pId = String(p.payment_id || '').toLowerCase();
    const cId = String(p.customer_id || '').toLowerCase();
    const bank = String(p.bank || '').toLowerCase();
    const method = String(p.payment_method || '').toLowerCase();
    const fClass = String(p.failure_class || '').toLowerCase();
    const fCode = String(p.failure_code || '').toLowerCase();
    const sTerm = searchTerm.toLowerCase().trim();

    const matchesSearch = !sTerm || 
      pId.includes(sTerm) || 
      cId.includes(sTerm) || 
      bank.includes(sTerm) || 
      method.includes(sTerm) || 
      fClass.includes(sTerm) || 
      fCode.includes(sTerm);

    const matchesFailure = !failureFilter || p.failure_class === failureFilter;
    const matchesStatus = !statusFilter || (
      statusFilter === 'RECOVERED' ? (p.recovered || p.status === 'RECOVERED') :
      statusFilter === 'PENDING_APPROVAL' ? (p.status === 'PENDING_APPROVAL') :
      statusFilter === 'FAILED' ? (!p.recovered && p.status !== 'PENDING_APPROVAL') : true
    );

    return matchesSearch && matchesFailure && matchesStatus;
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
      
      {/* Dynamic Search & Filter Controls Bar */}
      <div className="p-4 border-b border-slate-800 flex flex-col md:flex-row items-center justify-between gap-3 bg-slate-900/60">
        
        {/* Real-time Search Input */}
        <div className="relative w-full md:w-80">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search payment ID or customer..."
            value={searchTerm}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-8 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500 transition-colors"
          />
          {searchTerm && (
            <button
              onClick={() => handleSearchChange('')}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* Filter Dropdowns */}
        <div className="flex flex-wrap items-center gap-2 w-full md:w-auto justify-end">
          <Filter className="w-3.5 h-3.5 text-slate-400" />
          
          <select
            value={failureFilter}
            onChange={(e) => handleFailureFilterChange(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-sky-500"
          >
            <option value="">All Failure Causes</option>
            <option value="TEMPORARY_BANK_FAILURE">Temporary Bank Failure</option>
            <option value="PAYMENT_METHOD_FAILURE">Payment Method Failure</option>
            <option value="CUSTOMER_ABANDONMENT">Customer Abandonment</option>
            <option value="INSUFFICIENT_FUNDS">Insufficient Funds</option>
            <option value="UNKNOWN">Unknown</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => handleStatusFilterChange(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-sky-500"
          >
            <option value="">All Statuses</option>
            <option value="FAILED">At Risk</option>
            <option value="PENDING_APPROVAL">Needs Approval</option>
            <option value="RECOVERED">Recovered</option>
          </select>

          {(searchTerm || failureFilter || statusFilter) && (
            <button
              onClick={clearFilters}
              className="px-2 py-1 text-[11px] font-semibold text-slate-400 hover:text-slate-200 bg-slate-800 rounded transition-colors"
            >
              Clear Filters
            </button>
          )}
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
                  <div className="flex items-center justify-center gap-2">
                    <div className="w-4 h-4 border-2 border-sky-400 border-t-transparent rounded-full animate-spin" />
                    Fetching payment records...
                  </div>
                </td>
              </tr>
            ) : filteredPayments.length === 0 ? (
              <tr>
                <td colSpan={6} className="text-center py-10 text-slate-500">
                  No payment records matching active search filters.
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
                    ₹{Number(p.amount || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 })}
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
