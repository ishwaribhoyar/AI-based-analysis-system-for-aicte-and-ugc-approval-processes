'use client';

import { useEffect, useState, Suspense } from 'react';
import { useParams } from 'next/navigation';
import { dashboardApi, reportApi } from '@/lib/api';
import type { DashboardResponse } from '@/lib/api';
import toast from 'react-hot-toast';
import Chatbot from '@/components/Chatbot';

function UnifiedReportContent() {
  const params = useParams();
  const batchId = params?.batchId as string;
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    if (!batchId) return;
    setLoading(true);
    dashboardApi
      .get(batchId)
      .then(setData)
      .catch(() => toast.error('Failed to load batch'))
      .finally(() => setLoading(false));
  }, [batchId]);

  const handleDownload = async () => {
    if (!batchId) return;
    setDownloading(true);
    try {
      toast.loading('Generating unified report...');
      await reportApi.generate(batchId, 'unified');
      const blob = await reportApi.download(batchId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `unified_report_${batchId}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      toast.dismiss();
      toast.success('Report ready');
    } catch {
      toast.dismiss();
      toast.error('Failed to download report');
    } finally {
      setDownloading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin h-10 w-10 border-2 border-blue-600 border-t-transparent rounded-full" />
      </div>
    );
  }

  if (!data) {
    return <div className="p-6 text-gray-700">Batch not found.</div>;
  }

  const classification = data.approval_classification;
  const readiness = data.approval_readiness;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-6 py-10 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-blue-900">Unified Report</h1>
            <p className="text-sm text-gray-600">Merged AICTE + UGC overview</p>
          </div>
          <button
            onClick={handleDownload}
            disabled={downloading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-60"
          >
            {downloading ? 'Preparing...' : 'Download'}
          </button>
        </div>

        <div className="grid md:grid-cols-2 gap-4">
          <div className="bg-white p-4 rounded-xl shadow border border-gray-100">
            <h3 className="text-md font-semibold text-blue-900">Classification</h3>
            <p className="text-sm text-gray-700">Category: {classification?.category ?? 'unknown'}</p>
            <p className="text-sm text-gray-700">Subtype: {classification?.subtype ?? 'unknown'}</p>
          </div>
          <div className="bg-white p-4 rounded-xl shadow border border-gray-100">
            <h3 className="text-md font-semibold text-blue-900">Approval Readiness</h3>
            <p className="text-sm text-gray-700">
              Score: {readiness?.approval_readiness_score ?? 'N/A'}%
            </p>
            <p className="text-sm text-gray-700">
              Missing: {readiness?.approval_missing_documents?.join(', ') || 'None'}
            </p>
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl shadow border border-gray-100 space-y-2">
          <h3 className="text-md font-semibold text-blue-900">KPIs</h3>
          <div className="grid md:grid-cols-2 gap-2 text-sm text-gray-700">
            {data.kpi_cards.map((kpi) => (
              <div key={kpi.name} className="border rounded-lg p-3 bg-gray-50">
                <p className="font-semibold text-gray-800">{kpi.name}</p>
                <p>{kpi.value ?? 'N/A'}</p>
              </div>
            ))}
          </div>
        </div>
        </div>

        {/* Chatbot */}
        {batchId && <Chatbot batchId={batchId} currentPage="unified-report" />}
      </div>
    );
  }

export default function UnifiedReportPage() {
  return (
    <Suspense fallback={<div className="p-6">Loading...</div>}>
      <UnifiedReportContent />
    </Suspense>
  );
}

