'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { batchApi } from '@/lib/api';
import toast from 'react-hot-toast';
import { FileText, GraduationCap, Sparkles, Shield, BarChart3, CheckCircle, Layers } from 'lucide-react';

export default function HomePage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [selectedMode, setSelectedMode] = useState<'aicte' | 'ugc' | 'mixed' | null>(null);

  const handleModeSelect = async (mode: 'aicte' | 'ugc' | 'mixed') => {
    setLoading(true);
    setSelectedMode(mode);
    try {
      const batch = await batchApi.create({ mode });
      toast.success(`${mode.toUpperCase()} batch created!`);
      router.push(`/upload?batch_id=${batch.batch_id}`);
    } catch (err: any) {
      console.error('Batch creation error:', err);
      let errorMessage = 'Failed to create batch';
      
      if (err.response) {
        // Server responded with error
        errorMessage = err.response.data?.detail || err.response.data?.message || `Server error: ${err.response.status}`;
      } else if (err.request) {
        // Request made but no response
        errorMessage = 'No response from server. Please check if the backend is running.';
      } else if (err.code === 'ECONNABORTED') {
        errorMessage = 'Request timed out. Please try again.';
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      toast.error(errorMessage);
      setSelectedMode(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-soft relative overflow-hidden">
      {/* Decorative Background Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="shape-blob w-96 h-96 bg-primary-100 top-0 right-0 translate-x-1/2 -translate-y-1/2" />
        <div className="shape-blob w-80 h-80 bg-secondary-50 bottom-0 left-0 -translate-x-1/2 translate-y-1/2" />
        <div className="shape-blob w-64 h-64 bg-accent-50 top-1/2 left-1/4 opacity-30" />
      </div>

      <div className="container mx-auto px-4 py-12 relative z-10">
        {/* Header */}
        <div className="text-center mb-12 animate-fade-in">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/80 backdrop-blur-sm rounded-full shadow-soft mb-6 border border-primary-100">
            <Sparkles className="w-4 h-4 text-primary" />
            <span className="text-sm font-medium text-primary-dark">AI-Powered Document Analysis</span>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold text-gray-800 mb-4">
            Smart Approval{' '}
            <span className="bg-gradient-to-r from-primary to-primary-light bg-clip-text text-transparent">
              AI
            </span>
          </h1>
          <p className="text-lg text-gray-600 max-w-xl mx-auto">
            Intelligent Document Analysis & Performance Indicators for UGC & AICTE Reviewers
          </p>
        </div>

        {/* Features Row */}
        <div className="flex flex-wrap justify-center gap-4 mb-12">
          {[
            { icon: Shield, label: 'Compliance Check', color: 'text-primary' },
            { icon: BarChart3, label: 'KPI Analysis', color: 'text-secondary' },
            { icon: CheckCircle, label: 'Auto Validation', color: 'text-accent' },
          ].map((feature, index) => (
            <div
              key={index}
              className="flex items-center gap-2 px-4 py-2 bg-white/70 backdrop-blur-sm rounded-full shadow-soft border border-gray-100"
            >
              <feature.icon className={`w-4 h-4 ${feature.color}`} />
              <span className="text-gray-700 font-medium text-sm">{feature.label}</span>
            </div>
          ))}
        </div>

        {/* Mode Selection Cards - 3 Column Grid */}
        <div className="max-w-6xl mx-auto grid md:grid-cols-3 gap-6">
          {/* AICTE Card */}
          <div
            onClick={() => !loading && handleModeSelect('aicte')}
            className={`group relative bg-white rounded-3xl shadow-soft-lg p-6 cursor-pointer transition-all duration-300 hover:shadow-soft-xl hover:-translate-y-1 border border-gray-100 ${loading && selectedMode === 'aicte' ? 'ring-2 ring-primary ring-offset-2' : ''} ${loading && selectedMode !== 'aicte' ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            <div className="flex items-center justify-between mb-4">
              <div className="w-14 h-14 bg-gradient-to-br from-primary-50 to-primary-100 rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                <GraduationCap className="w-7 h-7 text-primary" />
              </div>
              <div className="px-2 py-1 bg-primary-50 rounded-full">
                <span className="text-xs font-semibold text-primary">Technical</span>
              </div>
            </div>

            <h2 className="text-xl font-bold text-gray-800 mb-2">AICTE Mode</h2>
            <p className="text-gray-600 text-sm mb-4">
              Technical education institutions evaluation
            </p>

            <div className="bg-primary-50/50 rounded-xl p-3 mb-4">
              <p className="text-xs font-semibold text-primary-dark mb-2 flex items-center gap-1">
                <span className="w-4 h-4 bg-primary rounded-full flex items-center justify-center text-white text-xs">10</span>
                Blocks Extracted
              </p>
              <div className="grid grid-cols-2 gap-1 text-xs text-gray-600">
                <div className="flex items-center gap-1"><div className="w-1 h-1 rounded-full bg-primary" />Faculty</div>
                <div className="flex items-center gap-1"><div className="w-1 h-1 rounded-full bg-primary" />Infrastructure</div>
                <div className="flex items-center gap-1"><div className="w-1 h-1 rounded-full bg-primary" />Placements</div>
                <div className="flex items-center gap-1"><div className="w-1 h-1 rounded-full bg-primary" />+7 more</div>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-primary font-semibold text-sm group-hover:translate-x-1 transition-transform">Start →</span>
              {loading && selectedMode === 'aicte' && (
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-primary border-t-transparent" />
              )}
            </div>
          </div>

          {/* UGC Card */}
          <div
            onClick={() => !loading && handleModeSelect('ugc')}
            className={`group relative bg-white rounded-3xl shadow-soft-lg p-6 cursor-pointer transition-all duration-300 hover:shadow-soft-xl hover:-translate-y-1 border border-gray-100 ${loading && selectedMode === 'ugc' ? 'ring-2 ring-accent ring-offset-2' : ''} ${loading && selectedMode !== 'ugc' ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            <div className="flex items-center justify-between mb-4">
              <div className="w-14 h-14 bg-gradient-to-br from-accent-50 to-orange-100 rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                <FileText className="w-7 h-7 text-accent" />
              </div>
              <div className="px-2 py-1 bg-accent-50 rounded-full">
                <span className="text-xs font-semibold text-accent">Higher Ed</span>
              </div>
            </div>

            <h2 className="text-xl font-bold text-gray-800 mb-2">UGC Mode</h2>
            <p className="text-gray-600 text-sm mb-4">
              Higher education institutions assessment
            </p>

            <div className="bg-accent-50/50 rounded-xl p-3 mb-4">
              <p className="text-xs font-semibold text-orange-700 mb-2 flex items-center gap-1">
                <span className="w-4 h-4 bg-accent rounded-full flex items-center justify-center text-white text-xs">9</span>
                Blocks Extracted
              </p>
              <div className="grid grid-cols-2 gap-1 text-xs text-gray-600">
                <div className="flex items-center gap-1"><div className="w-1 h-1 rounded-full bg-accent" />Governance</div>
                <div className="flex items-center gap-1"><div className="w-1 h-1 rounded-full bg-accent" />Research</div>
                <div className="flex items-center gap-1"><div className="w-1 h-1 rounded-full bg-accent" />IQAC</div>
                <div className="flex items-center gap-1"><div className="w-1 h-1 rounded-full bg-accent" />+6 more</div>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-accent font-semibold text-sm group-hover:translate-x-1 transition-transform">Start →</span>
              {loading && selectedMode === 'ugc' && (
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-accent border-t-transparent" />
              )}
            </div>
          </div>

          {/* Mixed AICTE + UGC Card */}
          <div
            onClick={() => !loading && handleModeSelect('mixed')}
            className={`group relative bg-white rounded-3xl shadow-soft-lg p-6 cursor-pointer transition-all duration-300 hover:shadow-soft-xl hover:-translate-y-1 border border-gray-100 ${loading && selectedMode === 'mixed' ? 'ring-2 ring-purple-400 ring-offset-2' : ''} ${loading && selectedMode !== 'mixed' ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            <div className="flex items-center justify-between mb-4">
              <div className="w-14 h-14 bg-gradient-to-br from-purple-50 to-purple-100 rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                <Layers className="w-7 h-7 text-purple-500" />
              </div>
              <div className="px-2 py-1 bg-purple-50 rounded-full">
                <span className="text-xs font-semibold text-purple-600">Combined</span>
              </div>
            </div>

            <h2 className="text-xl font-bold text-gray-800 mb-2">Mixed Mode</h2>
            <p className="text-gray-600 text-sm mb-4">
              Combined AICTE + UGC unified evaluation
            </p>

            <div className="bg-purple-50/50 rounded-xl p-3 mb-4">
              <p className="text-xs font-semibold text-purple-700 mb-2 flex items-center gap-1">
                <span className="w-4 h-4 bg-purple-500 rounded-full flex items-center justify-center text-white text-xs">19</span>
                All Blocks Combined
              </p>
              <div className="grid grid-cols-2 gap-1 text-xs text-gray-600">
                <div className="flex items-center gap-1"><div className="w-1 h-1 rounded-full bg-purple-500" />All AICTE</div>
                <div className="flex items-center gap-1"><div className="w-1 h-1 rounded-full bg-purple-500" />All UGC</div>
                <div className="flex items-center gap-1"><div className="w-1 h-1 rounded-full bg-purple-500" />Unified Report</div>
                <div className="flex items-center gap-1"><div className="w-1 h-1 rounded-full bg-purple-500" />Cross-check</div>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-purple-600 font-semibold text-sm group-hover:translate-x-1 transition-transform">Start →</span>
              {loading && selectedMode === 'mixed' && (
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-purple-500 border-t-transparent" />
              )}
            </div>
          </div>
        </div>

        {/* Footer Info */}
        <div className="max-w-2xl mx-auto mt-12 text-center">
          <p className="text-gray-500 text-sm">
            Select a mode to begin evaluating institutional documents with AI-powered analysis
          </p>
        </div>
      </div>
    </div>
  );
}
