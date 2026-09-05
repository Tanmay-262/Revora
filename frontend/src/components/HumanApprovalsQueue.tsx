'use client';

import React from 'react';
import { ShieldAlert, Check, X } from 'lucide-react';

interface HumanApprovalsQueueProps {
  payments: any[];
  onApprove: (paymentId: string) => void;
  onReject: (paymentId: string) => void;
  isProcessing: boolean;
}

export const HumanApprovalsQueue: React.FC<HumanApprovalsQueueProps> = ({
  payments,
  onApprove,
  onReject,
  isProcessing
}) => {
  const pendingItems = payments.filter((p) => p.status === 'PENDING_APPROVAL');

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
      <div className="flex items-center justify-between pb-4 border-b border-slate-800 mb-5">
        <div>
          <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-amber-400" />
            Human Operator Approval Queue
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Financial safety policy requires manual operator review before executing high-value or low-confidence actions.
          </p>
        </div>
        <span className="px-2.5 py-0.5 rounded text-xs font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
          {pendingItems.length} Escalations
        </span>
      </div>

      {pendingItems.length === 0 ? (
        <div className="text-center py-12 text-slate-500">
          <Check className="w-10 h-10 text-emerald-500/40 mx-auto mb-2" />
          <p className="text-xs font-semibold text-slate-300">All Escalations Resolved</p>
          <p className="text-[11px] text-slate-500 mt-0.5">No transactions currently pending operator approval.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
          {pendingItems.map((p) => (
            <div key={p.payment_id} className="bg-slate-950 border border-slate-800 rounded-lg p-4 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between border-b border-slate-800 pb-2.5 mb-2.5">
                  <div>
                    <span className="font-mono text-xs font-bold text-slate-200">{p.payment_id}</span>
                    <span className="block text-[11px] text-slate-500">{p.customer_id}</span>
                  </div>
                  <div className="text-right">
                    <span className="text-base font-bold text-emerald-400">
                      ₹{p.amount.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                    </span>
                    <span className="block text-[10px] text-slate-500 uppercase">{p.payment_method}</span>
                  </div>
                </div>

                <div className="bg-slate-900 p-2.5 rounded border border-slate-800 mb-3 space-y-1 text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Failure Class:</span>
                    <span className="font-semibold text-amber-400">{p.failure_class}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Escalation Rationale:</span>
                    <span className="font-medium text-slate-300">Amount exceeds ₹10,000 threshold</span>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2 pt-1">
                <button
                  onClick={() => onApprove(p.payment_id)}
                  disabled={isProcessing}
                  className="flex-1 py-2 rounded text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white transition-colors flex items-center justify-center gap-1 shadow-sm"
                >
                  <Check className="w-3.5 h-3.5" />
                  APPROVE
                </button>
                <button
                  onClick={() => onReject(p.payment_id)}
                  disabled={isProcessing}
                  className="flex-1 py-2 rounded text-xs font-bold bg-slate-800 hover:bg-slate-700 text-rose-400 border border-slate-700 transition-colors flex items-center justify-center gap-1"
                >
                  <X className="w-3.5 h-3.5" />
                  REJECT
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
