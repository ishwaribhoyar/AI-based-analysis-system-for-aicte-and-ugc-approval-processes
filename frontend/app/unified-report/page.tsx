'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { unifiedReportApi, reportApi, type UnifiedReportResponse } from '@/lib/api';
import toast from 'react-hot-toast';
import {
    FileText, Download, CheckCircle, XCircle, AlertTriangle,
    ArrowLeft, Award, Shield, TrendingUp, Building2
} from 'lucide-react';

function UnifiedReportPageContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const batchId = searchParams.get('batch_id') || '';

    const [report, setReport] = useState<UnifiedReportResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [downloading, setDownloading] = useState(false);

    useEffect(() => {
        if (!batchId) {
            router.push('/');
            return;
        }
        fetchReport();
    }, [batchId]);

    const fetchReport = async () => {
        try {
            const data = await unifiedReportApi.get(batchId);
            setReport(data);
        } catch (err) {
            console.error(err);
            toast.error('Failed to fetch unified report');
        } finally {
            setLoading(false);
        }
    };

    const handleDownload = async () => {
        setDownloading(true);
        try {
            await reportApi.generate(batchId, 'unified');
            const blob = await reportApi.download(batchId);
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `unified_report_${batchId}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            toast.success('Report downloaded!');
        } catch {
            toast.error('Failed to download report');
        } finally {
            setDownloading(false);
        }
    };

    const getSeverityColor = (severity: string) => {
        switch (severity.toLowerCase()) {
            case 'good': return 'bg-secondary-50 border-secondary text-secondary-dark';
            case 'critical': return 'bg-red-50 border-red-300 text-red-700';
            case 'warning': return 'bg-accent-50 border-accent text-accent-dark';
            default: return 'bg-gray-50 border-gray-300 text-gray-700';
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-soft flex items-center justify-center">
                <div className="text-center">
                    <div className="w-16 h-16 mx-auto mb-4 bg-lavender-50 rounded-2xl flex items-center justify-center animate-pulse">
                        <FileText className="w-8 h-8 text-lavender" />
                    </div>
                    <p className="text-gray-600">Loading unified report...</p>
                </div>
            </div>
        );
    }

    if (!report) {
        return (
            <div className="min-h-screen bg-gradient-soft flex items-center justify-center">
                <div className="text-center bg-white rounded-3xl shadow-soft-lg p-12">
                    <XCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
                    <p className="text-gray-600 mb-6">Failed to load unified report</p>
                    <button onClick={() => router.push('/')} className="btn-primary">Go Home</button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-soft py-8">
            <div className="container mx-auto px-4 max-w-6xl">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div className="flex items-center gap-4">
                        <button onClick={() => router.push(`/dashboard?batch_id=${batchId}`)} className="p-2 bg-white rounded-xl shadow-soft hover:shadow-soft-lg transition-all">
                            <ArrowLeft className="w-5 h-5 text-gray-600" />
                        </button>
                        <div>
                            <h1 className="text-3xl font-bold text-gray-800">Unified Evaluation Report</h1>
                            <p className="text-gray-600">AICTE + UGC Combined Assessment</p>
                        </div>
                    </div>
                    <button
                        onClick={handleDownload}
                        disabled={downloading}
                        className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-lavender to-lavender-light text-white rounded-xl font-medium hover:shadow-lg disabled:opacity-50 transition-all"
                    >
                        <Download className="w-5 h-5" />
                        {downloading ? 'Generating...' : 'Download PDF'}
                    </button>
                </div>

                {/* Institution Profile */}
                <div className="bg-white rounded-3xl shadow-soft-lg p-8 mb-8">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="w-12 h-12 bg-gradient-to-br from-primary to-secondary rounded-xl flex items-center justify-center">
                            <Building2 className="w-6 h-6 text-white" />
                        </div>
                        <div>
                            <h2 className="text-xl font-bold text-gray-800">
                                {report.institution_name || 'Institution Profile'}
                            </h2>
                            <p className="text-gray-500">Generated: {new Date(report.generated_at).toLocaleString()}</p>
                        </div>
                    </div>

                    <div className="grid md:grid-cols-4 gap-4">
                        <div className="bg-gray-50 rounded-2xl p-4">
                            <p className="text-sm text-gray-500">Mode</p>
                            <p className="text-lg font-bold text-gray-800 uppercase">
                                {(report.institution_profile as Record<string, unknown>)?.mode as string || 'N/A'}
                            </p>
                        </div>
                        <div className="bg-gray-50 rounded-2xl p-4">
                            <p className="text-sm text-gray-500">Documents</p>
                            <p className="text-lg font-bold text-gray-800">
                                {(report.institution_profile as Record<string, unknown>)?.processed_documents as number || 0} / {(report.institution_profile as Record<string, unknown>)?.total_documents as number || 0}
                            </p>
                        </div>
                        <div className="bg-gray-50 rounded-2xl p-4">
                            <p className="text-sm text-gray-500">Blocks Extracted</p>
                            <p className="text-lg font-bold text-gray-800">
                                {(report.institution_profile as Record<string, unknown>)?.blocks_extracted as number || 0} / {(report.institution_profile as Record<string, unknown>)?.total_blocks as number || 0}
                            </p>
                        </div>
                        <div className="bg-gray-50 rounded-2xl p-4">
                            <p className="text-sm text-gray-500">Classification</p>
                            <p className="text-lg font-bold text-primary uppercase">
                                {(report.classification as Record<string, unknown>)?.category as string || 'N/A'} - {(report.classification as Record<string, unknown>)?.subtype as string || 'N/A'}
                            </p>
                        </div>
                    </div>
                </div>

                {/* Score Cards */}
                <div className="grid md:grid-cols-2 gap-6 mb-8">
                    {/* AICTE Summary */}
                    {report.aicte_summary && (
                        <div className="bg-gradient-to-br from-primary-50 to-white rounded-3xl shadow-soft-lg p-6 border border-primary-100">
                            <div className="flex items-center gap-3 mb-4">
                                <div className="w-10 h-10 bg-primary rounded-xl flex items-center justify-center">
                                    <Award className="w-5 h-5 text-white" />
                                </div>
                                <h3 className="text-lg font-bold text-gray-800">AICTE Evaluation</h3>
                            </div>

                            <div className="text-4xl font-bold text-primary mb-4">
                                {report.aicte_summary.overall_score?.toFixed(1) || 'N/A'}
                                <span className="text-lg text-gray-500 font-normal">/100</span>
                            </div>

                            <div className="space-y-2 mb-4">
                                <div className="flex justify-between text-sm">
                                    <span className="text-gray-600">Sufficiency</span>
                                    <span className="font-medium">{report.aicte_summary.sufficiency_percentage.toFixed(0)}%</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span className="text-gray-600">Compliance Flags</span>
                                    <span className="font-medium">{report.aicte_summary.compliance_flags_count}</span>
                                </div>
                            </div>

                            {report.aicte_summary.missing_documents.length > 0 && (
                                <div className="pt-4 border-t border-primary-100">
                                    <p className="text-sm font-medium text-gray-700 mb-2">Missing:</p>
                                    <div className="flex flex-wrap gap-1">
                                        {report.aicte_summary.missing_documents.slice(0, 3).map((doc, idx) => (
                                            <span key={idx} className="px-2 py-1 bg-red-100 text-red-700 rounded text-xs">{doc}</span>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* UGC Summary */}
                    {report.ugc_summary && (
                        <div className="bg-gradient-to-br from-accent-50 to-white rounded-3xl shadow-soft-lg p-6 border border-accent-100">
                            <div className="flex items-center gap-3 mb-4">
                                <div className="w-10 h-10 bg-accent rounded-xl flex items-center justify-center">
                                    <Shield className="w-5 h-5 text-white" />
                                </div>
                                <h3 className="text-lg font-bold text-gray-800">UGC Evaluation</h3>
                            </div>

                            <div className="text-4xl font-bold text-accent mb-4">
                                {report.ugc_summary.overall_score?.toFixed(1) || 'N/A'}
                                <span className="text-lg text-gray-500 font-normal">/100</span>
                            </div>

                            <div className="space-y-2 mb-4">
                                <div className="flex justify-between text-sm">
                                    <span className="text-gray-600">Sufficiency</span>
                                    <span className="font-medium">{report.ugc_summary.sufficiency_percentage.toFixed(0)}%</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span className="text-gray-600">Compliance Flags</span>
                                    <span className="font-medium">{report.ugc_summary.compliance_flags_count}</span>
                                </div>
                            </div>

                            {report.ugc_summary.missing_documents.length > 0 && (
                                <div className="pt-4 border-t border-accent-100">
                                    <p className="text-sm font-medium text-gray-700 mb-2">Missing:</p>
                                    <div className="flex flex-wrap gap-1">
                                        {report.ugc_summary.missing_documents.slice(0, 3).map((doc, idx) => (
                                            <span key={idx} className="px-2 py-1 bg-red-100 text-red-700 rounded text-xs">{doc}</span>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>

                {/* Consolidated Scores */}
                <div className="bg-white rounded-3xl shadow-soft-lg p-8 mb-8">
                    <h2 className="text-xl font-bold text-gray-800 mb-6 flex items-center gap-3">
                        <TrendingUp className="w-6 h-6 text-lavender" />
                        Consolidated Scores
                    </h2>

                    <div className="grid md:grid-cols-2 gap-8">
                        <div>
                            <p className="text-sm text-gray-500 mb-2">Consolidated KPI Score</p>
                            <div className="flex items-end gap-2">
                                <span className="text-5xl font-bold text-gray-800">{report.consolidated_kpi_score.toFixed(1)}</span>
                                <span className="text-lg text-gray-500 mb-2">/100</span>
                            </div>
                            <div className="h-3 bg-gray-100 rounded-full overflow-hidden mt-3">
                                <div
                                    className="h-full bg-gradient-to-r from-primary to-secondary rounded-full"
                                    style={{ width: `${report.consolidated_kpi_score}%` }}
                                />
                            </div>
                        </div>

                        <div>
                            <p className="text-sm text-gray-500 mb-2">Approval Readiness</p>
                            <div className="flex items-end gap-2">
                                <span className="text-5xl font-bold text-gray-800">{report.approval_readiness_score.toFixed(1)}</span>
                                <span className="text-lg text-gray-500 mb-2">%</span>
                            </div>
                            <div className="h-3 bg-gray-100 rounded-full overflow-hidden mt-3">
                                <div
                                    className="h-full bg-gradient-to-r from-lavender to-lavender-light rounded-full"
                                    style={{ width: `${report.approval_readiness_score}%` }}
                                />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Final Recommendation */}
                <div className={`rounded-3xl p-8 mb-8 ${report.final_recommendation.includes('READY')
                        ? 'bg-secondary-50 border-2 border-secondary'
                        : report.final_recommendation.includes('CONDITIONAL')
                            ? 'bg-accent-50 border-2 border-accent'
                            : 'bg-red-50 border-2 border-red-300'
                    }`}>
                    <div className="flex items-center gap-4">
                        {report.final_recommendation.includes('READY') ? (
                            <CheckCircle className="w-12 h-12 text-secondary" />
                        ) : (
                            <AlertTriangle className="w-12 h-12 text-accent" />
                        )}
                        <div>
                            <h2 className="text-xl font-bold text-gray-800">Final Recommendation</h2>
                            <p className="text-gray-700">{report.final_recommendation}</p>
                        </div>
                    </div>
                </div>

                {/* Observations */}
                <div className="bg-white rounded-3xl shadow-soft-lg p-8 mb-8">
                    <h2 className="text-xl font-bold text-gray-800 mb-6">Unified Observations</h2>
                    <div className="space-y-3">
                        {report.unified_observations.map((obs, idx) => (
                            <div
                                key={idx}
                                className={`p-4 rounded-2xl border ${getSeverityColor(obs.severity)}`}
                            >
                                <div className="flex items-center gap-2 mb-1">
                                    <span className="text-xs font-semibold uppercase opacity-70">{obs.category}</span>
                                </div>
                                <p className="font-medium">{obs.observation}</p>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Missing Documents */}
                {report.all_missing_documents.length > 0 && (
                    <div className="bg-red-50 border-2 border-red-200 rounded-3xl p-6">
                        <h3 className="text-lg font-bold text-red-700 mb-4 flex items-center gap-2">
                            <XCircle className="w-5 h-5" />
                            All Missing Documents ({report.all_missing_documents.length})
                        </h3>
                        <div className="grid md:grid-cols-2 gap-2">
                            {report.all_missing_documents.map((doc, idx) => (
                                <div key={idx} className="flex items-center gap-2 text-red-600 text-sm">
                                    <XCircle className="w-4 h-4 flex-shrink-0" />
                                    {doc}
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

export default function UnifiedReportPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen bg-gradient-soft flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-3 border-lavender border-t-transparent" />
            </div>
        }>
            <UnifiedReportPageContent />
        </Suspense>
    );
}
