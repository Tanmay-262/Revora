'use client';

import React from 'react';
import { X, History, ShieldCheck, Zap, AlertTriangle, CheckCircle2, UserCheck } from 'lucide-react';

interface AuditTrailModalProps {
  isOpen: boolean;
  onClose: () => void;
  paymentId: string;
  auditLogs: any[];
}

export const AuditTrailModal: React.FC<AuditTrailModalProps> = ({
  isOpen,
  onClose,
  paymentId,
  auditLogs
}) => {
  if (!isOpen) return null;

  const getEventIcon = (type: string) => {
    switch (type) {
      case 'PAYMENT_FAILURE_DETECTED':
        return <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />;
      case 'RISK_SCORE_CALCULATED':
        return <Zap className="w-3.5 h-3.5 text-sky-400" />;
      case 'ROOT_CAUSE_IDENTIFIED':
        return <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />;
      case 'POLICY_CHECK':
        return <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />;
      case 'PAYMENT_RECOVERED':
        return <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />;
      case 'HUMAN_APPROVAL_ESCALATED':
        return <UserCheck className="w-3.5 h-3.5 text-indigo-400" />;
      default:
        return <History className="w-3.5 h-3.5 text-slate-400" />;
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/75 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="w-full max-w-lg bg-slate-900 border border-slate-800 rounded-xl text-slate-100 p-5 shadow-2xl max-h-[85vh] flex flex-col justify-between">
        
        <div>
          {/* Header */}
          <div className="flex items-center justify-between pb-3.5 border-b border-slate-800 mb-5">
            <div className="flex items-center gap-2">
              <History className="w-4 h-4 text-sky-400" />
              <div>
                <h3 className="text-sm font-bold font-mono">Audit Trail: {paymentId}</h3>
                <p className="text-[11px] text-slate-400">Immutable decision & execution event timeline</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-1 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Vertical Timeline */}
          <div className="overflow-y-auto max-h-[55vh] pr-2 space-y-4">
            {auditLogs.length === 0 ? (
              <p className="text-xs text-slate-500 text-center py-6">No audit events recorded yet.</p>
            ) : (
              auditLogs.map((log, idx) => (
                <div key={idx} className="relative pl-5 border-l border-slate-800 last:border-l-0 pb-1">
                  
                  {/* Icon Node */}
                  <div className="absolute -left-2.5 top-0 w-5 h-5 rounded-full bg-slate-950 border border-slate-700 flex items-center justify-center shadow-xs">
                    {getEventIcon(log.event_type)}
                  </div>

                  <div className="bg-slate-950 border border-slate-800 rounded-lg p-3">
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="font-bold text-slate-200">{log.event_type}</span>
                      <span className="text-slate-500 text-[10px] font-mono">
                        {new Date(log.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400 font-medium">Actor: {log.actor}</div>
                    {log.reason && (
                      <p className="text-[11px] text-slate-300 mt-1 bg-slate-900 p-2 rounded border border-slate-800">
                        {log.reason}
                      </p>
                    )}
                  </div>

                </div>
              ))
            )}
          </div>
        </div>

        <div className="pt-3.5 border-t border-slate-800 mt-4 text-right">
          <button
            onClick={onClose}
            className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg transition-colors"
          >
            Close Audit Trail
          </button>
        </div>

      </div>
    </div>
  );
};
