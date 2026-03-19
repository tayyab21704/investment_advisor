"use client";

import { useState } from "react";
import { signIn } from "next-auth/react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Loader2, ArrowRight, TrendingUp } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const res = await signIn("credentials", {
        redirect: false,
        email,
        password,
      });

      if (res?.error) {
        setError("Invalid email or password");
      } else {
        router.push("/");
      }
    } catch (err) {
      setError("An unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignIn = () => {
    signIn("google", { callbackUrl: "/" });
  };

  return (
    <div className="flex min-h-screen bg-bg-base font-sans">
      {/* Left Column - Form */}
      <div className="w-full lg:w-1/2 flex flex-col justify-center items-center p-8 sm:p-12 xl:p-24 relative z-10">
        <div className="w-full max-w-md">
          <div className="mb-10 lg:text-left text-center">
            <h1 className="text-4xl font-bold tracking-tight text-text-primary mb-3">Welcome Back</h1>
            <p className="text-text-secondary text-base">Enter your credentials to access the Council</p>
          </div>

          <div className="bg-[#111111] border border-border-strong rounded-2xl p-6 shadow-2xl backdrop-blur-sm">
            <form onSubmit={handleSubmit} className="space-y-5">
              {error && (
                <div className="p-3 bg-red-dim border border-red/20 rounded-lg text-red text-sm text-center">
                  {error}
                </div>
              )}
              
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-text-secondary uppercase tracking-widest pl-1">Email</label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-[#1A1A1A] border-2 border-border-default rounded-xl px-4 py-3 text-text-primary placeholder:text-text-muted focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all"
                  placeholder="investor@example.com"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-text-secondary uppercase tracking-widest pl-1">Password</label>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-[#1A1A1A] border-2 border-border-default rounded-xl px-4 py-3 text-text-primary placeholder:text-text-muted focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all"
                  placeholder="••••••••"
                />
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-[#CBCDFF] text-black font-bold rounded-xl py-3.5 flex items-center justify-center gap-2 hover:bg-[#9B9EEA] transition-colors shadow-lg disabled:opacity-70"
                >
                  {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : "Sign In"}
                </button>
              </div>
            </form>

            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-border-default"></div>
              </div>
              <div className="relative flex justify-center text-xs px-2">
                  <span className="bg-bg-surface px-3 text-text-muted font-medium tracking-wider">OR CONTINUE WITH</span>
              </div>
            </div>

            <button
              onClick={handleGoogleSignIn}
              type="button"
              className="w-full bg-bg-base border border-border-default text-text-primary font-medium rounded-xl py-3.5 flex items-center justify-center gap-3 hover:bg-bg-elevated transition-colors"
            >
              <svg viewBox="0 0 24 24" className="w-5 h-5" aria-hidden="true">
                <path d="M12.0003 4.75C13.7703 4.75 15.3553 5.36002 16.6053 6.54998L20.0303 3.125C17.9502 1.19 15.2353 0 12.0003 0C7.31028 0 3.25527 2.69 1.28027 6.60998L5.27028 9.70498C6.21525 6.86002 8.87028 4.75 12.0003 4.75Z" fill="#EA4335" />
                <path d="M23.658 12.2764C23.658 11.4222 23.58 10.5966 23.4344 9.7998H12V14.4589H18.5367C18.2543 15.969 17.3887 17.269 16.126 18.1158L20.103 21.2014C22.4277 19.0583 23.658 15.9472 23.658 12.2764Z" fill="#4285F4" />
                <path d="M12.0003 24.0001C15.2403 24.0001 17.9653 22.935 19.9453 21.095L15.9653 18.0099C14.8953 18.725 13.5603 19.12 12.0003 19.12C8.87028 19.12 6.21525 17.0099 5.27028 14.1649L1.28027 17.2599C3.25527 21.1799 7.31028 24.0001 12.0003 24.0001Z" fill="#34A853" />
                <path d="M5.27025 14.1649C5.03025 13.4399 4.89525 12.7249 4.89525 11.9999C4.89525 11.2749 5.03025 10.5599 5.27025 9.83492L1.28025 6.73993C0.465249 8.35493 0 10.1299 0 11.9999C0 13.8699 0.465249 15.6449 1.28025 17.2599L5.27025 14.1649Z" fill="#FBBC05" />
              </svg>
              Google
            </button>
          </div>

          <p className="text-center text-text-secondary text-sm mt-8">
            Don't have an account?{" "}
            <Link href="/register" className="text-text-primary font-medium hover:text-primary transition-colors inline-flex items-center gap-1 group">
              Register now
              <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
            </Link>
          </p>
        </div>
      </div>

      {/* Right Column - Info / Graphic */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden bg-bg-surface items-center justify-center p-12">
        {/* Abstract Background Elements */}
        <div className="absolute top-0 right-0 w-full h-full bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-blue-dim via-bg-surface to-bg-surface opacity-80" />
        <div className="absolute bottom-[-20%] left-[-10%] w-[60%] h-[60%] bg-pink-dim blur-[120px] rounded-full pointer-events-none" />
        
        {/* Content Wrapper */}
        <div className="relative z-10 max-w-lg">
          <div className="inline-flex items-center justify-center p-3 sm:p-4 bg-primary/10 rounded-2xl mb-6 border border-primary/20 backdrop-blur-sm">
            <TrendingUp className="w-8 h-8 text-primary" />
          </div>
          <h2 className="text-4xl md:text-5xl font-bold text-text-primary tracking-tight leading-tight mb-6">
            Investment Advisor
          </h2>
          <p className="text-lg md:text-xl text-text-secondary leading-relaxed mb-8">
            The autonomous multi-agent AI system for Indian equity markets. Harness the power of intelligent data processing and seamless portfolio management all in one secure platform.
          </p>
          
          {/* Feature List */}
          <div className="space-y-4 text-text-secondary">
            <div className="flex items-start gap-4 p-4 rounded-xl border border-border-default/50 bg-bg-base/30 backdrop-blur-md">
              <div className="w-8 h-8 rounded-full bg-green/10 flex items-center justify-center shrink-0 mt-0.5">
                <div className="w-3 h-3 rounded-full bg-green"></div>
              </div>
              <div>
                <h4 className="text-text-primary font-medium mb-1">Automated Research</h4>
                <p className="text-sm">Continuous scanning and analysis of market fundamentals and technicals.</p>
              </div>
            </div>
            <div className="flex items-start gap-4 p-4 rounded-xl border border-border-default/50 bg-bg-base/30 backdrop-blur-md">
              <div className="w-8 h-8 rounded-full bg-blue/10 flex items-center justify-center shrink-0 mt-0.5">
                <div className="w-3 h-3 rounded-full bg-blue"></div>
              </div>
              <div>
                <h4 className="text-text-primary font-medium mb-1">Tailored Portfolios</h4>
                <p className="text-sm">Personalized investment strategies based on your unique risk profile and financial goals.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
