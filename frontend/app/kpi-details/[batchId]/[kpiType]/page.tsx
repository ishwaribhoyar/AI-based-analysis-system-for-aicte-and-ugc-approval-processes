'use client';

import { useState, useEffect, Suspense } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { dashboardApi, type KPIDetailsResponse, type KPIBreakdown } from '@/lib/api';
import toast from 'react-hot-toast';
import {
    ArrowLeft, RefreshCw, CheckCircle, XCircle, AlertTriangle,
    Calculator, FileText, TrendingUp
} from 'lucide-react';

const KPI_MAP: Record<string, string> = {
    'fsr': 'fsr',
    'fsr_score': 'fsr',
    'infrastructure': 'infrastructure',
    'infrastructure_score': 'infrastructure',
    'placement': 'placement',
    'placement_index': 'placement',
    'lab': 'lab_compliance',
    'lab_compliance': 'lab_compliance',
    'lab_compliance_index': 'lab_compliance',
    'overall': 'overall',
    'overall_score': 'overall',
};

function KPIDetailsPage() {
    const router = useRouter();
    const params = useParams();
    const batchId = params?.batchId as string;
    const kpiType = params?.kpiType as string;

    const [details, setDetails] = useState<KPIDetailsResponse | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (batchId) {
            fetchDetails();
        }
    }, [batchId]);

    const fetchDetails = async () => {
        setLoading(true);
        try {
            const data = await dashboardApi.getKpiDetails(batchId);
            setDetails(data);
        } catch (err) {
            console.error(err);
            toast.error('Failed to load KPI details');
        } finally {
            setLoading(false);
        }
    };

    // Get the specific KPI breakdown
    const normalizedType = KPI_MAP[kpiType?.toLowerCase() || ''] || 'overall';
    const kpiBreakdown: KPIBreakdown | null = details
        ? (details as Record<string, KPIBreakdown | null>)[normalizedType]
        : null;

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-soft flex items-center justify-center">
                <RefreshCw className="w-8 h-8 text-primary animate-spin" />
            </div>
        );
    }

    if (!kpiBreakdown) {
        return (
            <div className="min-h-screen bg-gradient-soft flex items-center justify-center">
                <div className="text-center">
                    <XCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
                    <h2 className="text-xl font-semibold text-gray-800">KPI Not Found</h2>
                    <p className="text-gray-600 mt-2">The requested KPI details are not available.</p>
                    <button onClick={() => router.back()} className="mt-4 px-4 py-2 bg-primary text-white rounded-xl">
                        Go Back
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-soft py-8">
            <div className="container mx-auto px-4 max-w-5xl">
                {/* Header */}
                <div className="flex items-center gap-4 mb-8">
                    <button onClick={() => router.back()} className="p-2 bg-white rounded-xl shadow-soft hover:shadow-soft-lg transition-all">
                        <ArrowLeft className="w-5 h-5 text-gray-600" />
                    </button>
                    <div>
                        <h1 className="text-3xl font-bold text-gray-800">{kpiBreakdown.kpi_name}</h1>
                        <p className="text-gray-600">{details?.institution_name} • {details?.mode.toUpperCase()}</p>
                    </div>
                </div>

                {/* Score Summary */}
                <div className="bg-white rounded-3xl shadow-soft-lg p-6 mb-8">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-500">Final Score</p>
                            <p className="text-4xl font-bold text-primary">{kpiBreakdown.final_score.toFixed(1)}</p>
                            <p className="text-sm text-gray-500 mt-1">
                                Data Quality:
                                <span className={`ml-2 px-2 py-0.5 rounded text-xs font-medium ${kpiBreakdown.data_quality === 'complete' ? 'bg-green-100 text-green-700' :
                                        kpiBreakdown.data_quality === 'partial' ? 'bg-yellow-100 text-yellow-700' :
                                            'bg-red-100 text-red-700'
                                    }`}>
                                    {kpiBreakdown.data_quality.toUpperCase()}
                                </span>
                            </p>
                        </div>
                        <div className="w-24 h-24 rounded-full border-8 border-primary flex items-center justify-center">
                            <span className="text-2xl font-bold text-primary">{kpiBreakdown.final_score.toFixed(0)}</span>
                        </div>
                    </div>
                </div>

                {/* Missing Parameters Warning */}
                {kpiBreakdown.missing_parameters.length > 0 && (
                    <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 mb-6">
                        <div className="flex items-start gap-3">
                            <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                            <div>
                                <h3 className="font-semibold text-amber-800">Missing Parameters</h3>
                                <p className="text-sm text-amber-700 mt-1">
                                    The following parameters were not found in the documents:
                                </p>
                                <ul className="mt-2 flex flex-wrap gap-2">
                                    {kpiBreakdown.missing_parameters.map(p => (
                                        <li key={p} className="px-2 py-1 bg-amber-100 text-amber-800 rounded text-xs font-medium">
                                            {p.replace(/_/g, ' ')}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        </div>
                    </div>
                )}

                {/* Raw Parameter Table */}
                <div className="bg-white rounded-3xl shadow-soft-lg p-6 mb-8">
                    <h2 className="text-xl font-semibold text-gray-800 mb-4 flex items-center gap-2">
                        <FileText className="w-6 h-6 text-primary" />
                        Parameter Breakdown
                    </h2>
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b-2 border-gray-100">
                                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Parameter</th>
                                    <th className="text-right py-3 px-4 font-semibold text-gray-700">Raw Value</th>
                                    <th className="text-right py-3 px-4 font-semibold text-gray-700">Normalized</th>
                                    <th className="text-right py-3 px-4 font-semibold text-gray-700">Weight</th>
                                    <th className="text-right py-3 px-4 font-semibold text-gray-700">Score</th>
                                    <th className="text-right py-3 px-4 font-semibold text-gray-700">Contribution</th>
                                    <th className="text-center py-3 px-4 font-semibold text-gray-700">Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {kpiBreakdown.parameters.map((param, idx) => (
                                    <tr key={idx} className={`border-b border-gray-50 ${param.missing ? 'bg-red-50' : ''}`}>
                                        <td className="py-3 px-4 font-medium text-gray-800">{param.display_name}</td>
                                        <td className="py-3 px-4 text-right text-gray-600">
                                            {param.raw_value !== null ? String(param.raw_value) : <span className="text-gray-400">—</span>}
                                            {param.unit && <span className="text-xs text-gray-400 ml-1">{param.unit}</span>}
                                        </td>
                                        <td className="py-3 px-4 text-right text-gray-600">
                                            {param.normalized_value !== null ? param.normalized_value.toFixed(2) : <span className="text-gray-400">—</span>}
                                        </td>
                                        <td className="py-3 px-4 text-right text-gray-600">
                                            {(param.weight * 100).toFixed(0)}%
                                        </td>
                                        <td className="py-3 px-4 text-right font-medium text-gray-800">
                                            {param.score.toFixed(1)}
                                        </td>
                                        <td className="py-3 px-4 text-right font-semibold text-primary">
                                            {param.contribution.toFixed(2)}
                                        </td>
                                        <td className="py-3 px-4 text-center">
                                            {param.missing ? (
                                                <XCircle className="w-5 h-5 text-red-500 mx-auto" />
                                            ) : (
                                                <CheckCircle className="w-5 h-5 text-green-500 mx-auto" />
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Formula Steps */}
                <div className="bg-white rounded-3xl shadow-soft-lg p-6 mb-8">
                    <h2 className="text-xl font-semibold text-gray-800 mb-4 flex items-center gap-2">
                        <Calculator className="w-6 h-6 text-primary" />
                        Computation Steps
                    </h2>
                    <div className="space-y-4">
                        {kpiBreakdown.formula_steps.map((step) => (
                            <div key={step.step_number} className="flex items-start gap-4 p-4 bg-gray-50 rounded-xl">
                                <div className="w-8 h-8 bg-primary text-white rounded-full flex items-center justify-center font-bold flex-shrink-0">
                                    {step.step_number}
                                </div>
                                <div className="flex-1">
                                    <p className="font-medium text-gray-800">{step.description}</p>
                                    <code className="block mt-2 text-sm bg-gray-100 text-gray-700 p-2 rounded font-mono">
                                        {step.formula}
                                    </code>
                                    {step.result !== null && (
                                        <p className="mt-2 text-sm text-gray-600">
                                            Result: <span className="font-semibold text-primary">{step.result}</span>
                                        </p>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Formula Text */}
                <div className="bg-gradient-to-r from-primary to-primary-light rounded-3xl p-6 text-white">
                    <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                        <TrendingUp className="w-6 h-6" />
                        Complete Formula
                    </h2>
                    <code className="block bg-white/20 p-4 rounded-xl font-mono text-lg">
                        {kpiBreakdown.formula_text}
                    </code>
                    <p className="text-sm mt-4 opacity-80">
                        Confidence: {(kpiBreakdown.confidence * 100).toFixed(0)}%
                    </p>
                </div>
            </div>
        </div>
    );
}

export default function Page() {
    return (
        <Suspense fallback={
            <div className="min-h-screen bg-gradient-soft flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-3 border-primary border-t-transparent" />
            </div>
        }>
            <KPIDetailsPage />
        </Suspense>
    );
}
