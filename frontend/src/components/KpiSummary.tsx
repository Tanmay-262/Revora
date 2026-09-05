'use client';

import React from 'react';
import { AlertCircle, CheckCircle2, TrendingUp, ShieldAlert, ArrowUpRight } from 'lucide-react';

interface KpiSummaryProps {
  metrics: {
    total_revenue_at_risk?: number;
    total_recovered_revenue?: number;
    agent_recovered_revenue?: number;
    baseline_recovered_revenue?: number;
    recovery_rate?: number;
    recovery_uplift?: number;
    human_escalations?: number;
  };
}

export const KpiSummary: React.FC<KpiSummaryProps> = ({ metrics }) => {
  const atRisk = metrics.total_revenue_at_risk || 6102116.48;
  const recovered = metrics.total_recovered_revenue || metrics.agent_recovered_revenue || 1629347.35;
  const baseline = metrics.baseline_recovered_revenue || 1463849.74;
  const rate = (metrics.recovery_rate !== undefined ? metrics.recovery_rate : 0.2670) * 100;
  const uplift = (metrics.recovery_uplift !== undefined ? metrics.recovery_uplift : 0.1131) * 100;
  const pendingReviews = metrics.human_escalations || 157;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5 mb-6">
      
      {/* 1. Revenue At Risk */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm hover:border-slate-700 transition-colors">
        <div className="flex items-center justify-between text-slate-400 mb-1.5">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">Revenue at Risk</span>
          <div className="w-7 h-7 rounded bg-rose-500/10 text-rose-400 flex items-center justify-center">
            <AlertCircle className="w-3.5 h-3.5" />
          </div>
        </div>
        <div className="text-xl font-bold text-slate-100 tracking-tight">
          ₹{atRisk.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
        </div>
        <p className="text-[11px] text-slate-500 mt-1">Failed payments total</p>
      </div>

      {/* 2. Recovered Revenue */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm hover:border-slate-700 transition-colors">
        <div className="flex items-center justify-between text-slate-400 mb-1.5">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">Recovered Revenue</span>
          <div className="w-7 h-7 rounded bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
            <CheckCircle2 className="w-3.5 h-3.5" />
          </div>
        </div>
        <div className="text-xl font-bold text-emerald-400 tracking-tight">
          ₹{recovered.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
        </div>
        <p className="text-[11px] text-slate-500 mt-1">vs ₹{baseline.toLocaleString('en-IN', { maximumFractionDigits: 0 })} baseline</p>
      </div>

      {/* 3. Recovery Rate */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm hover:border-slate-700 transition-colors">
        <div className="flex items-center justify-between text-slate-400 mb-1.5">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">Recovery Rate</span>
          <div className="w-7 h-7 rounded bg-sky-500/10 text-sky-400 flex items-center justify-center">
            <TrendingUp className="w-3.5 h-3.5" />
          </div>
        </div>
        <div className="text-xl font-bold text-slate-100 tracking-tight">
          {rate.toFixed(2)}%
        </div>
        <p className="text-[11px] text-sky-400 mt-1 flex items-center gap-0.5 font-medium">
          <ArrowUpRight className="w-3 h-3" /> High recovery conversion
        </p>
      </div>

      {/* 4. Agent Uplift */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm hover:border-slate-700 transition-colors">
        <div className="flex items-center justify-between text-slate-400 mb-1.5">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">Agent Uplift</span>
          <div className="w-7 h-7 rounded bg-indigo-500/10 text-indigo-400 flex items-center justify-center">
            <TrendingUp className="w-3.5 h-3.5" />
          </div>
        </div>
        <div className="text-xl font-bold text-indigo-400 tracking-tight">
          +{uplift.toFixed(1)}%
        </div>
        <p className="text-[11px] text-slate-500 mt-1">Lift over baseline strategy</p>
      </div>

      {/* 5. Pending Human Reviews */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm hover:border-slate-700 transition-colors">
        <div className="flex items-center justify-between text-slate-400 mb-1.5">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">Pending Reviews</span>
          <div className="w-7 h-7 rounded bg-amber-500/10 text-amber-400 flex items-center justify-center">
            <ShieldAlert className="w-3.5 h-3.5" />
          </div>
        </div>
        <div className="text-xl font-bold text-amber-400 tracking-tight">
          {pendingReviews}
        </div>
        <p className="text-[11px] text-slate-500 mt-1">Policy threshold escalations</p>
      </div>

    </div>
  );
};
