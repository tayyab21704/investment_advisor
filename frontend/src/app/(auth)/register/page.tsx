"use client";

import { useState } from "react";
import { signIn } from "next-auth/react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Loader2, ArrowRight, CheckCircle2, ShieldCheck } from "lucide-react";

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
        className={`w-full bg-[#1A1A1A] border-2 border-border-default rounded-xl py-2.5 text-sm text-text-primary placeholder:text-text-muted/60 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all ${symbol ? 'pl-9 pr-4' : 'px-4'}`}
      />
    </div>
  </div>
);

export default function RegisterPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Form State
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    behavioral_risk_score: "5",
    financial_risk_score: "5",
    actual_risk_capacity: "5",
    monthly_income: "",
    monthly_expenses: "",
    monthly_surplus: "",
    existing_debt: "",
    debt_to_income_ratio: "",
    liquidity_required_pct: "20.0",
    max_single_asset_pct: "15.0",
    max_high_risk_allocation_pct: "40.0",
    investment_horizon_years: "10"
  });

  const updateForm = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      if (!formData.name || !formData.email || !formData.password || !formData.monthly_income || !formData.monthly_expenses || !formData.monthly_surplus || !formData.existing_debt || !formData.debt_to_income_ratio) {
        throw new Error("Please fill out all the fields.");
      }

      const payload = {
        name: formData.name,
        email: formData.email,
        password: formData.password,
        behavioral_risk_score: parseInt(formData.behavioral_risk_score),
        financial_risk_score: parseInt(formData.financial_risk_score),
        actual_risk_capacity: parseInt(formData.actual_risk_capacity),
        monthly_income: parseFloat(formData.monthly_income),
        monthly_expenses: parseFloat(formData.monthly_expenses),
        monthly_surplus: parseFloat(formData.monthly_surplus),
        existing_debt: parseFloat(formData.existing_debt),
        debt_to_income_ratio: parseFloat(formData.debt_to_income_ratio),
        liquidity_required_pct: parseFloat(formData.liquidity_required_pct),
        max_single_asset_pct: parseFloat(formData.max_single_asset_pct),
        max_high_risk_allocation_pct: parseFloat(formData.max_high_risk_allocation_pct),
        investment_horizon_years: parseInt(formData.investment_horizon_years)
      };

      const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const res = await fetch(`${apiBase}/api/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Registration failed");
      }

      // Automatically sign in upon successful registration
      const signInRes = await signIn("credentials", {
        redirect: false,
        email: formData.email,
        password: formData.password,
      });

      if (signInRes?.error) {
        setError("Account created, but automatic login failed. Please sign in manually.");
        setTimeout(() => router.push("/login"), 3000);
      } else {
        router.push("/");
      }

    } catch (err: any) {
      setError(err.message || "An unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-bg-base font-sans">
      
      {/* Left Column - Form */}
      <div className="w-full xl:w-7/12 flex flex-col items-center py-12 px-6 sm:px-12 relative z-10 min-h-screen">
        <div className="w-full max-w-2xl">
          <div className="mb-8 xl:text-left text-center">
            <h1 className="text-3xl font-bold tracking-tight text-text-primary mb-2">Join the Council</h1>
            <p className="text-text-secondary text-base">Create your portfolio and begin your investment journey</p>
          </div>

          <div className="bg-[#111111] border border-border-strong rounded-3xl p-6 sm:p-8 shadow-2xl relative">
            {error && (
              <div className="mb-6 p-4 bg-red-dim border border-red/20 rounded-xl text-red text-sm text-center flex items-center justify-center gap-2">
                <ShieldCheck className="w-4 h-4" />
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-8">
              
              {/* Account Information */}
              <div>
                <h2 className="text-[10px] font-bold text-text-primary mb-3 pb-2 border-b border-border-default/40 uppercase tracking-widest text-[#CBCDFF]">
                  Account Details
                </h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-5 gap-y-3">
                  <InputField label="Full Name" type="text" field="name" value={formData.name} onChange={updateForm} placeholder="John Doe" />
                  <InputField label="Email Address" type="email" field="email" value={formData.email} onChange={updateForm} placeholder="investor@example.com" />
                  <div className="sm:col-span-2">
                    <InputField label="Password" type="password" field="password" value={formData.password} onChange={updateForm} placeholder="••••••••" />
                  </div>
                </div>
              </div>

              {/* Risk Metrics */}
              <div>
                <h2 className="text-[10px] font-bold text-text-primary mb-3 pb-2 border-b border-border-default/40 uppercase tracking-widest text-[#CBCDFF]">
                  Risk Metrics
                </h2>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-x-5 gap-y-3">
                  <InputField label="Behavioral Risk" type="number" field="behavioral_risk_score" value={formData.behavioral_risk_score} onChange={updateForm} placeholder="1-10" />
                  <InputField label="Financial Risk" type="number" field="financial_risk_score" value={formData.financial_risk_score} onChange={updateForm} placeholder="1-10" />
                  <InputField label="Actual Risk Cap." type="number" field="actual_risk_capacity" value={formData.actual_risk_capacity} onChange={updateForm} placeholder="1-10" />
                </div>
              </div>

              {/* Financial Data */}
              <div>
                <h2 className="text-[10px] font-bold text-text-primary mb-3 pb-2 border-b border-border-default/40 uppercase tracking-widest text-[#CBCDFF]">
                  Financial Data
                </h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-5 gap-y-3">
                  <InputField label="Monthly Income" type="number" field="monthly_income" value={formData.monthly_income} onChange={updateForm} symbol="₹" placeholder="100000" />
                  <InputField label="Monthly Expenses" type="number" field="monthly_expenses" value={formData.monthly_expenses} onChange={updateForm} symbol="₹" placeholder="60000" />
                  <InputField label="Monthly Surplus" type="number" field="monthly_surplus" value={formData.monthly_surplus} onChange={updateForm} symbol="₹" placeholder="40000" />
                  <InputField label="Existing Debt" type="number" field="existing_debt" value={formData.existing_debt} onChange={updateForm} symbol="₹" placeholder="500000" />
                  <div className="sm:col-span-2">
                    <InputField label="Debt/Income Ratio" type="number" field="debt_to_income_ratio" value={formData.debt_to_income_ratio} onChange={updateForm} placeholder="0.2" />
                  </div>
                </div>
              </div>

              {/* Investment Constraints */}
              <div>
                <h2 className="text-[10px] font-bold text-text-primary mb-3 pb-2 border-b border-border-default/40 uppercase tracking-widest text-[#CBCDFF]">
                  Investment Constraints
                </h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-5 gap-y-3">
                  <InputField label="Liquidity Reqd (%)" type="number" field="liquidity_required_pct" value={formData.liquidity_required_pct} onChange={updateForm} placeholder="20" />
                  <InputField label="Max Single Asset (%)" type="number" field="max_single_asset_pct" value={formData.max_single_asset_pct} onChange={updateForm} placeholder="15" />
                  <InputField label="Max High Risk (%)" type="number" field="max_high_risk_allocation_pct" value={formData.max_high_risk_allocation_pct} onChange={updateForm} placeholder="40" />
                  <InputField label="Horizon (Years)" type="number" field="investment_horizon_years" value={formData.investment_horizon_years} onChange={updateForm} placeholder="10" />
                </div>
              </div>

              <div className="pt-2 mt-6">
                <button type="submit" disabled={loading} className="w-full bg-[#CBCDFF] text-black font-bold rounded-xl py-4 flex items-center justify-center gap-2 hover:bg-[#9B9EEA] transition-colors shadow-lg disabled:opacity-70 disabled:cursor-not-allowed">
                  {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <><CheckCircle2 className="w-5 h-5"/> Complete Registration</>}
                </button>
              </div>

            </form>
          </div>

          <p className="text-center text-text-muted text-sm mt-6 pb-8">
            Already have an account?{" "}
            <Link href="/login" className="text-[#CBCDFF] font-medium hover:text-[#9B9EEA] transition-colors inline-flex items-center gap-1 group">
               Log in
               <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
            </Link>
          </p>
        </div>
      </div>

      {/* Right Column - Info / Graphic */}
      <div className="hidden xl:flex xl:w-5/12 relative overflow-hidden bg-bg-surface items-center justify-center p-12 border-l border-border-subtle sticky top-0 h-screen">
        <div className="absolute top-[-10%] right-[-10%] w-[60%] h-[60%] bg-blue-dim blur-[100px] rounded-full pointer-events-none" />
        <div className="absolute bottom-10 left-10 w-[40%] h-[40%] bg-green-dim blur-[80px] rounded-full pointer-events-none" />
        
        <div className="relative z-10 max-w-sm">
          <div className="mb-8">
            <h2 className="text-4xl font-bold text-text-primary tracking-tight leading-tight mb-4">
              Your autonomous AI investing engine.
            </h2>
            <p className="text-lg text-text-secondary leading-relaxed mb-8">
              Register now to set up your financial profile and start generating expertly curated portfolio recommendations instantly.
            </p>
          </div>

          <div className="space-y-6">
            <div className="flex gap-4 p-5 rounded-2xl bg-bg-base/40 border border-border-default/30 shadow-sm">
              <ShieldCheck className="w-6 h-6 text-primary shrink-0" />
              <div>
                <h4 className="font-semibold text-text-primary mb-1">Secure & Encrypted</h4>
                <p className="text-sm text-text-secondary">Your sensitive financial details stay local to your system context.</p>
              </div>
            </div>
          </div>
        </div>
      </div>

    </div>
  );
}
