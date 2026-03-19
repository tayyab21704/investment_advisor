"use client";

import { useState, useEffect } from "react";
import { useSession } from "next-auth/react";
import { Loader2, Save, User as UserIcon } from "lucide-react";

// Helper component for styled inputs
const InputField = ({ label, type, field, value, onChange, symbol = "", placeholder = "" }: any) => (
  <div className="space-y-1.5">
    <label className="text-[11px] font-semibold text-text-secondary uppercase tracking-widest pl-1">{label}</label>
    <div className="relative">
      {symbol && <span className="absolute left-4 top-[14px] text-text-muted text-sm">{symbol}</span>}
      <input
        type={type}
        required
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(field, e.target.value)}
        className={`w-full bg-bg-base border border-border-default rounded-xl py-3 text-sm text-text-primary placeholder:text-text-muted/60 focus:outline-none focus:border-border-accent focus:ring-1 focus:ring-border-accent transition-all ${symbol ? 'pl-9 pr-4' : 'px-4'}`}
      />
    </div>
  </div>
);

export default function ProfilePage() {
  const { data: session, status } = useSession();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [formData, setFormData] = useState({
    name: "",
    behavioral_risk_score: 5,
    financial_risk_score: 5,
    actual_risk_capacity: 5,
    monthly_income: 0,
    monthly_expenses: 0,
    monthly_surplus: 0,
    existing_debt: 0,
    debt_to_income_ratio: 0,
    liquidity_required_pct: 20.0,
    max_single_asset_pct: 15.0,
    max_high_risk_allocation_pct: 40.0,
    investment_horizon_years: 10
  });

  useEffect(() => {
    const fetchProfile = async () => {
      if (status === "loading") return;

      const token = (session as any)?.backendToken;
      if (!token) {
        setError("Not authenticated. Please log in again.");
        setLoading(false);
        return;
      }

      try {
        const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
        const res = await fetch(`${apiBase}/api/auth/profile`, {
          headers: {
            "Authorization": `Bearer ${token}`
          }
        });

        if (!res.ok) throw new Error("Failed to load profile");

        const data = await res.json();
        setFormData({
          name: data.name || "",
          behavioral_risk_score: data.behavioral_risk_score || 5,
          financial_risk_score: data.financial_risk_score || 5,
          actual_risk_capacity: data.actual_risk_capacity || 5,
          monthly_income: data.monthly_income || 0,
          monthly_expenses: data.monthly_expenses || 0,
          monthly_surplus: data.monthly_surplus || 0,
          existing_debt: data.existing_debt || 0,
          debt_to_income_ratio: data.debt_to_income_ratio || 0.0,
          liquidity_required_pct: data.liquidity_required_pct || 20.0,
          max_single_asset_pct: data.max_single_asset_pct || 15.0,
          max_high_risk_allocation_pct: data.max_high_risk_allocation_pct || 40.0,
          investment_horizon_years: data.investment_horizon_years || 10
        });
      } catch (err: any) {
        setError(err.message || "Could not load user profile");
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, [session, status]);

  const updateForm = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    setSuccess("");

    try {
      const token = (session as any)?.backendToken;
      if (!token) throw new Error("Not authenticated");

      const payload = {
        name: formData.name,
        behavioral_risk_score: parseInt(formData.behavioral_risk_score.toString()),
        financial_risk_score: parseInt(formData.financial_risk_score.toString()),
        actual_risk_capacity: parseInt(formData.actual_risk_capacity.toString()),
        monthly_income: parseFloat(formData.monthly_income.toString()),
        monthly_expenses: parseFloat(formData.monthly_expenses.toString()),
        monthly_surplus: parseFloat(formData.monthly_surplus.toString()),
        existing_debt: parseFloat(formData.existing_debt.toString()),
        debt_to_income_ratio: parseFloat(formData.debt_to_income_ratio.toString()),
        liquidity_required_pct: parseFloat(formData.liquidity_required_pct.toString()),
        max_single_asset_pct: parseFloat(formData.max_single_asset_pct.toString()),
        max_high_risk_allocation_pct: parseFloat(formData.max_high_risk_allocation_pct.toString()),
        investment_horizon_years: parseInt(formData.investment_horizon_years.toString())
      };

      const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const res = await fetch(`${apiBase}/api/auth/profile`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${(session as any)?.backendToken}`
        },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Failed to update profile");
      }

      setSuccess("Profile updated successfully!");
      setTimeout(() => setSuccess(""), 4000);
    } catch (err: any) {
      setError(err.message || "An unexpected error occurred");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6 lg:p-10 pb-24">
      <div className="mb-8 border-b border-border-subtle pb-6 flex items-center gap-4">
        <div className="w-12 h-12 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center">
          <UserIcon className="w-6 h-6 text-primary" />
        </div>
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-text-primary">Your Profile</h1>
          <p className="text-text-secondary mt-1">Manage your financial details and risk preferences</p>
        </div>
      </div>

      <form onSubmit={handleSave} className="space-y-10">
        
        {/* Alerts */}
        {error && (
          <div className="p-4 bg-red-dim border border-red/20 rounded-xl text-red text-sm">
            {error}
          </div>
        )}
        {success && (
          <div className="p-4 bg-green-dim border border-green/20 rounded-xl text-green text-sm flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-green" />
            {success}
          </div>
        )}

        {/* Basic Info */}
        <div className="bg-bg-surface border border-border-subtle rounded-3xl p-6 sm:p-8">
          <h2 className="text-sm font-bold text-text-primary mb-6 pb-2 border-b border-border-default/40 uppercase tracking-widest text-primary">
            Basic Information
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-5">
            <InputField label="Full Name" type="text" field="name" value={formData.name} onChange={updateForm} />
            <div className="space-y-1.5 opacity-60 pointer-events-none">
              <label className="text-[11px] font-semibold text-text-secondary uppercase tracking-widest pl-1">Email (Read Only)</label>
              <input type="email" value={session?.user?.email || ""} readOnly className="w-full bg-bg-base border border-border-default rounded-xl px-4 py-3 text-sm text-text-primary" />
            </div>
          </div>
        </div>

        {/* Financial Data */}
        <div className="bg-bg-surface border border-border-subtle rounded-3xl p-6 sm:p-8">
          <h2 className="text-sm font-bold text-text-primary mb-6 pb-2 border-b border-border-default/40 uppercase tracking-widest text-primary">
            Financial Profile
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-5">
            <InputField label="Monthly Income" type="number" field="monthly_income" value={formData.monthly_income} onChange={updateForm} symbol="₹" />
            <InputField label="Monthly Expenses" type="number" field="monthly_expenses" value={formData.monthly_expenses} onChange={updateForm} symbol="₹" />
            <InputField label="Monthly Surplus" type="number" field="monthly_surplus" value={formData.monthly_surplus} onChange={updateForm} symbol="₹" />
            <InputField label="Existing Debt" type="number" field="existing_debt" value={formData.existing_debt} onChange={updateForm} symbol="₹" />
            <div className="md:col-span-2">
              <InputField label="Debt to Income Ratio" type="number" field="debt_to_income_ratio" value={formData.debt_to_income_ratio} onChange={updateForm} />
            </div>
          </div>
        </div>

        {/* Risk & Constraints */}
        <div className="bg-bg-surface border border-border-subtle rounded-3xl p-6 sm:p-8">
          <h2 className="text-sm font-bold text-text-primary mb-6 pb-2 border-b border-border-default/40 uppercase tracking-widest text-primary">
            Investment Constraints & Risk
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-x-6 gap-y-5 mb-8">
            <InputField label="Behavioral Risk" type="number" field="behavioral_risk_score" value={formData.behavioral_risk_score} onChange={updateForm} />
            <InputField label="Financial Risk" type="number" field="financial_risk_score" value={formData.financial_risk_score} onChange={updateForm} />
            <InputField label="Risk Capacity" type="number" field="actual_risk_capacity" value={formData.actual_risk_capacity} onChange={updateForm} />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-5">
            <InputField label="Liquidity Reqd (%)" type="number" field="liquidity_required_pct" value={formData.liquidity_required_pct} onChange={updateForm} />
            <InputField label="Max Single Asset (%)" type="number" field="max_single_asset_pct" value={formData.max_single_asset_pct} onChange={updateForm} />
            <InputField label="Max High Risk (%)" type="number" field="max_high_risk_allocation_pct" value={formData.max_high_risk_allocation_pct} onChange={updateForm} />
            <InputField label="Horizon (Years)" type="number" field="investment_horizon_years" value={formData.investment_horizon_years} onChange={updateForm} />
          </div>
        </div>

        <div className="flex justify-end pt-4">
          <button
            type="submit"
            disabled={saving}
            className="bg-primary text-black font-bold rounded-xl px-8 py-3.5 flex items-center justify-center gap-2 hover:bg-primary-hover transition-colors shadow-lg disabled:opacity-70 disabled:cursor-not-allowed"
          >
            {saving ? <Loader2 className="w-5 h-5 animate-spin" /> : <><Save className="w-5 h-5"/> Save Profile</>}
          </button>
        </div>
      </form>
    </div>
  );
}
