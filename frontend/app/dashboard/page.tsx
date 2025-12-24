'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { dashboardApi, reportApi } from '@/lib/api';
import type { DashboardResponse } from '@/lib/api';
import toast from 'react-hot-toast';
import {
  AlertTriangle, CheckCircle, XCircle,
  Download, X, BarChart3, Home,
  TrendingUp, Shield, FileText, ChevronRight
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import type { BlockWithData, BlockCard } from '@/lib/api';
import KPIDetailsModal from '@/components/KPIDetailsModal';
import Chatbot from '@/components/Chatbot';

function DashboardPageContent() {
  const searchParams = useSearchParams();
  const batchId = searchParams.get('batch_id') || '';

  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedBlock, setSelectedBlock] = useState<BlockWithData | BlockCard | null>(null);
  const [kpiModalOpen, setKpiModalOpen] = useState(false);
  const [selectedKpi, setSelectedKpi] = useState<string>('');

  useEffect(() => {
    if (!batchId) return;

    const fetchDashboard = async () => {
      try {
        const data = await dashboardApi.get(batchId);
        setDashboard(data);
      } catch (err) {
        const error = err as { response?: { data?: { detail?: string } } };
        toast.error(error.response?.data?.detail || 'Failed to load dashboard');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboard();
  }, [batchId]);

  const handleDownloadReport = async () => {
    if (!batchId) return;

    try {
      toast.loading('Generating report...');
      await reportApi.generate(batchId);

      const blob = await reportApi.download(batchId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `report_${batchId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.dismiss();
      toast.success('Report downloaded!');
    } catch {
      toast.dismiss();
      toast.error('Failed to download report');
    }
  };

  const getKpiStyle = (value: number | null) => {
    if (value === null) return 'kpi-warning';
    if (value >= 80) return 'kpi-excellent';
    if (value >= 50) return 'kpi-good';
    return 'kpi-warning';
  };

  const getSeverityStyle = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'high': return 'bg-red-50 border-red-200 text-red-700';
      case 'medium': return 'bg-accent-50 border-accent-200 text-accent-dark';
      case 'low': return 'bg-yellow-50 border-yellow-200 text-yellow-700';
      default: return 'bg-gray-50 border-gray-200 text-gray-700';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-soft flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4 bg-primary-100 rounded-2xl flex items-center justify-center animate-pulse">
            <BarChart3 className="w-8 h-8 text-primary" />
          </div>
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (!dashboard) {
    return (
      <div className="min-h-screen bg-gradient-soft flex items-center justify-center">
        <div className="text-center bg-white rounded-3xl shadow-soft-lg p-12">
          <XCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
          <p className="text-gray-600 mb-6">Failed to load dashboard</p>
          <a href="/" className="btn-primary inline-flex items-center gap-2">
            <Home className="w-4 h-4" />
            Go Home
          </a>
        </div>
      </div>
    );
  }

  // Prepare trend data for chart
  const trendChartData = (dashboard.trend_data || []).reduce((acc: Record<string, number | string>[], point) => {
    if (!point || !point.year || !point.kpi_name) return acc;
    const existing = acc.find((item) => item.year === point.year);
    if (existing) {
      existing[point.kpi_name] = point.value;
    } else {
      acc.push({ year: point.year, [point.kpi_name]: point.value });
    }
    return acc;
  }, []);

  return (
    <div className="min-h-screen bg-gradient-soft py-8 relative">
      {/* Decorative Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="shape-blob w-96 h-96 bg-primary-100 top-0 right-0 translate-x-1/3 -translate-y-1/3 opacity-40" />
        <div className="shape-blob w-72 h-72 bg-secondary-50 bottom-1/4 left-0 -translate-x-1/2 opacity-40" />
      </div>

      <div className="container mx-auto px-4 max-w-7xl relative z-10">
        {/* Header */}
        <div className="bg-white rounded-3xl shadow-soft-lg p-6 mb-8 border border-gray-100">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <div className="w-10 h-10 bg-gradient-to-br from-primary to-primary-light rounded-xl flex items-center justify-center">
                  <BarChart3 className="w-5 h-5 text-white" />
                </div>
                <h1 className="text-2xl md:text-3xl font-bold text-gray-800">Evaluation Dashboard</h1>
              </div>
              <p className="text-gray-500">
                Mode: <span className="font-semibold text-primary uppercase">{dashboard.mode}</span> •
                Batch: <span className="font-mono text-sm bg-gray-100 px-2 py-1 rounded-lg ml-1">{dashboard.batch_id.slice(-12)}</span>
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <a
                href="/compare"
                className="inline-flex items-center gap-2 px-4 py-2 bg-secondary-50 text-secondary border border-secondary rounded-xl font-medium hover:bg-secondary hover:text-white transition-all"
              >
                <TrendingUp className="w-4 h-4" />
                Compare
              </a>
            </div>
          </div>
        </div>

        {/* KPI Cards */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          {dashboard.kpi_cards.map((kpi) => {
            // Map KPI name to endpoint key
            const kpiKeyMap: Record<string, string> = {
              'FSR Score': 'fsr',
              'Infrastructure Score': 'infrastructure',
              'Placement Index': 'placement',
              'Lab Compliance': 'lab',
              'Overall Score': 'overall',
              'AICTE Overall Score': 'overall',
              'UGC Overall Score': 'overall',
            };
            const kpiKey = kpiKeyMap[kpi.name] || 'overall';

            return (
              <div
                key={kpi.name}
                className={`card-static p-6 cursor-pointer hover:shadow-glow-teal transition-all ${getKpiStyle(kpi.value)}`}
                onClick={() => {
                  setSelectedKpi(kpiKey);
                  setKpiModalOpen(true);
                }}
              >
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-gray-700 font-medium">{kpi.name}</h3>
                  <div className="flex items-center gap-2">
                    <ChevronRight className="w-4 h-4 text-gray-400" />
                    <div className={`w-3 h-3 rounded-full ${kpi.value === null ? 'bg-gray-400' :
                      kpi.value >= 80 ? 'bg-secondary' :
                        kpi.value >= 50 ? 'bg-primary' : 'bg-accent'
                      }`} />
                  </div>
                </div>
                {kpi.value !== null ? (
                  <div className="text-4xl font-bold text-gray-800 mb-2">
                    {kpi.value.toFixed(1)}
                    <span className="text-lg text-gray-500 font-normal ml-1">/ 100</span>
                  </div>
                ) : (
                  <div className="text-xl font-medium text-gray-500">Insufficient Data</div>
                )}
                <p className="text-sm text-gray-500">{kpi.label}</p>
                <p className="text-xs text-primary mt-2">Click for details →</p>
              </div>
            );
          })}
        </div>

        {/* Sufficiency Card */}
        <div className="bg-white rounded-3xl shadow-soft-lg p-8 mb-8 border border-gray-100">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-gradient-to-br from-secondary to-secondary-light rounded-xl flex items-center justify-center">
              <FileText className="w-5 h-5 text-white" />
            </div>
            <h2 className="text-xl font-bold text-gray-800">Document Sufficiency</h2>
          </div>

          <div className="flex flex-col md:flex-row items-center gap-8">
            {/* Progress Circle */}
            <div className="relative w-40 h-40 flex-shrink-0">
              <svg className="w-full h-full transform -rotate-90">
                <circle
                  cx="80"
                  cy="80"
                  r="70"
                  stroke="#E5E7EB"
                  strokeWidth="12"
                  fill="none"
                />
                <circle
                  cx="80"
                  cy="80"
                  r="70"
                  stroke={
                    dashboard.sufficiency.percentage >= 80 ? '#059669' :
                      dashboard.sufficiency.percentage >= 50 ? '#0D9488' : '#F97316'
                  }
                  strokeWidth="12"
                  fill="none"
                  strokeLinecap="round"
                  strokeDasharray={`${dashboard.sufficiency.percentage * 4.4} 440`}
                  className="transition-all duration-1000"
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-3xl font-bold text-gray-800">
                  {dashboard.sufficiency.percentage.toFixed(0)}%
                </span>
                <span className="text-sm text-gray-500">Complete</span>
              </div>
            </div>

            <div className="flex-1">
              <div className="flex items-center gap-4 mb-4">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-secondary" />
                  <span className="text-gray-700">
                    <strong>{dashboard.sufficiency.present_count}</strong> present
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <XCircle className="w-5 h-5 text-gray-400" />
                  <span className="text-gray-700">
                    <strong>{dashboard.sufficiency.required_count - dashboard.sufficiency.present_count}</strong> missing
                  </span>
                </div>
              </div>

              {dashboard.sufficiency.missing_blocks.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-2">Missing Blocks:</p>
                  <div className="flex flex-wrap gap-2">
                    {dashboard.sufficiency.missing_blocks.map((block) => (
                      <span key={block} className="px-3 py-1 bg-red-50 text-red-700 rounded-full text-sm border border-red-200">
                        {block}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Compliance Flags */}
        {dashboard.compliance_flags.length > 0 && (
          <div className="bg-white rounded-3xl shadow-soft-lg p-8 mb-8 border border-gray-100">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-gradient-to-br from-accent to-accent-light rounded-xl flex items-center justify-center">
                <Shield className="w-5 h-5 text-white" />
              </div>
              <h2 className="text-xl font-bold text-gray-800">Compliance Flags</h2>
              <span className="px-3 py-1 bg-accent-50 text-accent rounded-full text-sm font-medium">
                {dashboard.compliance_flags.length} issue{dashboard.compliance_flags.length > 1 ? 's' : ''}
              </span>
            </div>

            <div className="space-y-4">
              {dashboard.compliance_flags.map((flag, index) => (
                <div key={index} className={`p-5 rounded-2xl border ${getSeverityStyle(flag.severity)}`}>
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <AlertTriangle className="w-5 h-5" />
                        <h3 className="font-semibold">{flag.title}</h3>
                      </div>
                      <p className="text-sm opacity-90 mb-2">{flag.reason}</p>
                      {flag.recommendation && (
                        <p className="text-sm italic opacity-80">
                          💡 {flag.recommendation}
                        </p>
                      )}
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase ${flag.severity === 'high' ? 'bg-red-200 text-red-800' :
                      flag.severity === 'medium' ? 'bg-orange-200 text-orange-800' :
                        'bg-yellow-200 text-yellow-800'
                      }`}>
                      {flag.severity}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Trend Chart */}
        {trendChartData.length > 0 && (
          <div className="bg-white rounded-3xl shadow-soft-lg p-8 mb-8 border border-gray-100">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-gradient-to-br from-lavender to-lavender-light rounded-xl flex items-center justify-center">
                <TrendingUp className="w-5 h-5 text-white" />
              </div>
              <h2 className="text-xl font-bold text-gray-800">Trend Analysis</h2>
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={trendChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis dataKey="year" stroke="#6B7280" />
                <YAxis stroke="#6B7280" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'white',
                    borderRadius: '12px',
                    border: '1px solid #E5E7EB',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                  }}
                />
                <Legend />
                {Object.keys(trendChartData[0] || {}).filter(key => key !== 'year').map((kpi, index) => (
                  <Line
                    key={kpi}
                    type="monotone"
                    dataKey={kpi}
                    stroke={['#0D9488', '#059669', '#F97316', '#8B5CF6'][index % 4]}
                    strokeWidth={3}
                    dot={{ fill: ['#0D9488', '#059669', '#F97316', '#8B5CF6'][index % 4], strokeWidth: 2, r: 4 }}
                    activeDot={{ r: 6 }}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Information Blocks */}
        <div className="bg-white rounded-3xl shadow-soft-lg p-8 mb-8 border border-gray-100">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-gradient-to-br from-primary to-secondary rounded-xl flex items-center justify-center">
              <FileText className="w-5 h-5 text-white" />
            </div>
            <h2 className="text-xl font-bold text-gray-800">Information Blocks</h2>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {dashboard.block_cards.map((block) => (
              <div
                key={block.block_id}
                className={`p-5 rounded-2xl cursor-pointer transition-all duration-300 hover:shadow-soft-lg border-2 ${block.is_present
                  ? block.is_invalid
                    ? 'bg-red-50 border-red-200 hover:border-red-300'
                    : block.is_low_quality
                      ? 'bg-yellow-50 border-yellow-200 hover:border-yellow-300'
                      : 'bg-secondary-50 border-secondary-light hover:border-secondary'
                  : 'bg-gray-50 border-gray-200 hover:border-gray-300'
                  }`}
                onClick={() => {
                  const blockWithData = dashboard.blocks.find((b) => b.block_id === block.block_id);
                  setSelectedBlock(blockWithData || block);
                }}
              >
                <div className="flex items-start justify-between mb-3">
                  <h3 className="font-semibold text-gray-800 flex-1">{block.block_name}</h3>
                  {block.is_present ? (
                    block.is_invalid ? (
                      <XCircle className="w-5 h-5 text-red-500" />
                    ) : block.is_low_quality ? (
                      <AlertTriangle className="w-5 h-5 text-yellow-500" />
                    ) : (
                      <CheckCircle className="w-5 h-5 text-secondary" />
                    )
                  ) : (
                    <XCircle className="w-5 h-5 text-gray-400" />
                  )}
                </div>
                <div className="space-y-1 text-sm text-gray-600">
                  <p>Fields: <span className="font-medium">{block.extracted_fields_count}</span></p>
                  <p>Confidence: <span className="font-medium">{(block.confidence * 100).toFixed(0)}%</span></p>
                  {block.is_outdated && (
                    <p className="text-accent font-medium">⚠️ Outdated</p>
                  )}
                </div>
                <div className="flex items-center justify-end mt-3 text-primary text-sm font-medium">
                  View Details <ChevronRight className="w-4 h-4" />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Block Detail Modal */}
        {selectedBlock && (
          <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={() => setSelectedBlock(null)}>
            <div className="bg-white rounded-3xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
              <div className="sticky top-0 bg-white border-b border-gray-100 p-6 flex justify-between items-center rounded-t-3xl">
                <h2 className="text-2xl font-bold text-gray-800">{selectedBlock.block_name}</h2>
                <button
                  onClick={() => setSelectedBlock(null)}
                  className="w-10 h-10 rounded-xl bg-gray-100 hover:bg-gray-200 flex items-center justify-center transition-colors"
                >
                  <X className="w-5 h-5 text-gray-600" />
                </button>
              </div>
              <div className="p-6">
                <div className="mb-6">
                  <h3 className="font-semibold text-gray-700 mb-3">Status</h3>
                  <div className="flex flex-wrap gap-2">
                    {selectedBlock.is_present && (
                      <span className="px-4 py-2 bg-secondary-50 text-secondary rounded-xl text-sm font-medium">
                        ✓ Present
                      </span>
                    )}
                    {selectedBlock.is_outdated && (
                      <span className="px-4 py-2 bg-accent-50 text-accent rounded-xl text-sm font-medium">
                        📅 Outdated
                      </span>
                    )}
                    {selectedBlock.is_low_quality && (
                      <span className="px-4 py-2 bg-yellow-50 text-yellow-700 rounded-xl text-sm font-medium">
                        ⚠️ Low Quality
                      </span>
                    )}
                    {selectedBlock.is_invalid && (
                      <span className="px-4 py-2 bg-red-50 text-red-700 rounded-xl text-sm font-medium">
                        ✗ Invalid
                      </span>
                    )}
                  </div>
                </div>
                {selectedBlock.evidence_snippet && (
                  <div className="mb-6">
                    <h3 className="font-semibold text-gray-700 mb-3">Evidence</h3>
                    <div className="bg-gray-50 p-5 rounded-2xl border border-gray-100">
                      <p className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
                        {selectedBlock.evidence_snippet}
                      </p>
                      {selectedBlock.evidence_page && (
                        <p className="text-xs text-gray-500 mt-3">📄 Page: {selectedBlock.evidence_page}</p>
                      )}
                    </div>
                  </div>
                )}
                {'data' in selectedBlock && selectedBlock.data && (
                  <div>
                    <h3 className="font-semibold text-gray-700 mb-3">Extracted Data</h3>
                    <div className="bg-gray-50 p-5 rounded-2xl border border-gray-100 overflow-x-auto">
                      <pre className="text-sm text-gray-700 font-mono">
                        {JSON.stringify(selectedBlock.data, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

      </div>

      {/* Chatbot */}
      {batchId && <Chatbot batchId={batchId} currentPage="dashboard" />}

      {/* KPI Details Modal */}
      <KPIDetailsModal
        isOpen={kpiModalOpen}
        onClose={() => setKpiModalOpen(false)}
        batchId={batchId}
        kpiName={selectedKpi}
      />
    </div>
  );
}

export default function DashboardPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gradient-soft flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4 bg-primary-100 rounded-2xl flex items-center justify-center animate-pulse">
            <BarChart3 className="w-8 h-8 text-primary" />
          </div>
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    }>
      <DashboardPageContent />
    </Suspense>
  );
}
