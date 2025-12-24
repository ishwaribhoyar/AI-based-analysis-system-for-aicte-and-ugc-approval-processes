'use client';

import { useState, useEffect } from 'react';
import { X, Calculator, FileText, AlertTriangle, CheckCircle } from 'lucide-react';
import { kpiDetailsApi, type KPIDetailedResponse } from '@/lib/api';

interface KPIDetailsModalProps {
    isOpen: boolean;
    onClose: () => void;
    batchId: string;
    kpiName: string;
}

export default function KPIDetailsModal({ isOpen, onClose, batchId, kpiName }: KPIDetailsModalProps) {
    const [data, setData] = useState<KPIDetailedResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (isOpen && batchId && kpiName) {
            fetchKPIDetails();
        }
    }, [isOpen, batchId, kpiName]);

    const fetchKPIDetails = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await kpiDetailsApi.get(batchId, kpiName);
            setData(response);
        } catch (err) {
            setError('Failed to load KPI details');
            console.error('Error fetching KPI details:', err);
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
            <div className="bg-white rounded-3xl shadow-2xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-gray-100 bg-gradient-to-r from-primary to-primary-light text-white">
                    <div>
                        <h2 className="text-2xl font-bold">{data?.kpi_name || 'KPI Details'}</h2>
                        <p className="text-white/80 text-sm mt-1">Real-time backend computation</p>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-white/20 rounded-full transition-colors">
                        <X className="w-6 h-6" />
                    </button>
                </div>

                {/* Content */}
                <div className="overflow-y-auto max-h-[calc(90vh-120px)] p-6">
                    {loading ? (
                        <div className="flex items-center justify-center py-12">
                            <div className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin" />
                        </div>
                    ) : error ? (
                        <div className="text-center py-12 text-red-500">
                            <AlertTriangle className="w-12 h-12 mx-auto mb-4" />
                            <p>{error}</p>
                        </div>
                    ) : data ? (
                        <div className="space-y-8">
                            {/* Score Summary */}
                            <div className="flex items-center gap-6">
                                <div className="w-24 h-24 rounded-full border-8 border-primary flex items-center justify-center">
                                    <span className="text-3xl font-bold text-primary">
                                        {data.score !== null ? data.score.toFixed(0) : '—'}
                                    </span>
                                </div>
                                <div className="flex-1">
                                    <p className="text-gray-600">
                                        {data.score !== null 
                                            ? `${data.kpi_name} is ${data.score.toFixed(2)}/100`
                                            : 'Insufficient data to calculate score'}
                                    </p>
                                    {data.included_kpis && (
                                        <div className="flex gap-2 mt-2">
                                            <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-medium">
                                                Included: {data.included_kpis.join(', ')}
                                            </span>
                                        </div>
                                    )}
                                    {data.excluded_kpis && data.excluded_kpis.length > 0 && (
                                        <div className="flex gap-2 mt-2">
                                            <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs">
                                                {data.excluded_kpis[0]}
                                            </span>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Formula */}
                            <div className="bg-gray-50 rounded-2xl p-4">
                                <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                                    <Calculator className="w-5 h-5 text-primary" />
                                    Formula
                                </h3>
                                <code className="block bg-gray-100 p-3 rounded-xl font-mono text-sm text-gray-700">
                                    {data.formula}
                                </code>
                            </div>

                            {/* Parameter Table */}
                            <div>
                                <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                                    <FileText className="w-5 h-5 text-primary" />
                                    Parameter Contributions
                                </h3>
                                <div className="overflow-x-auto">
                                    <table className="w-full text-sm">
                                        <thead>
                                            <tr className="border-b-2 border-gray-100">
                                                <th className="text-left py-3 px-3 font-semibold text-gray-700">Parameter</th>
                                                <th className="text-right py-3 px-3 font-semibold text-gray-700">Extracted</th>
                                                <th className="text-right py-3 px-3 font-semibold text-gray-700">Norm</th>
                                                <th className="text-right py-3 px-3 font-semibold text-gray-700">Weight</th>
                                                <th className="text-right py-3 px-3 font-semibold text-gray-700">Contrib</th>
                                                <th className="text-left py-3 px-3 font-semibold text-gray-700">Evidence</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {data.parameters.map((param, idx) => (
                                                <tr key={idx} className={`border-b border-gray-50 ${param.missing ? 'bg-red-50' : ''}`}>
                                                    <td className="py-3 px-3 font-medium text-gray-800">{param.display_name}</td>
                                                    <td className="py-3 px-3 text-right text-gray-600">
                                                        {param.extracted !== null && param.extracted !== undefined 
                                                            ? `${param.extracted}${param.unit ? ` ${param.unit}` : ''}` 
                                                            : <span className="text-gray-400">—</span>}
                                                    </td>
                                                    <td className="py-3 px-3 text-right text-gray-500">{String(param.norm)}{param.unit ? ` ${param.unit}` : ''}</td>
                                                    <td className="py-3 px-3 text-right text-gray-600">{(param.weight * 100).toFixed(0)}%</td>
                                                    <td className="py-3 px-3 text-right font-semibold text-primary">
                                                        {param.contrib !== null && param.contrib !== undefined ? param.contrib.toFixed(2) : '—'}
                                                    </td>
                                                    <td className="py-3 px-3 text-gray-500 text-xs max-w-[200px] truncate">
                                                        {param.evidence?.snippet ? (
                                                            <span title={param.evidence.snippet}>
                                                                📄 p.{param.evidence.page || '?'}: {param.evidence.snippet.slice(0, 50)}...
                                                            </span>
                                                        ) : '—'}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>

                            {/* Calculation Steps */}
                            <div>
                                <h3 className="font-semibold text-gray-800 mb-3">Step-by-Step Calculation</h3>
                                <div className="space-y-2">
                                    {data.calculation_steps.map((step) => (
                                        <div key={step.step} className="flex items-start gap-3 p-3 bg-gray-50 rounded-xl">
                                            <div className="w-7 h-7 bg-primary text-white rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0">
                                                {step.step}
                                            </div>
                                            <div className="flex-1">
                                                <p className="text-sm font-medium text-gray-800">{step.description}</p>
                                                <code className="text-xs text-gray-500 font-mono">{step.formula}</code>
                                                {step.result !== null && step.result !== undefined && (
                                                    <span className="ml-2 text-sm text-primary font-semibold">= {step.result}</span>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Missing Parameters Warning */}
                            {data.parameters.some(p => p.missing) && (
                                <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4">
                                    <h3 className="font-semibold text-amber-800 flex items-center gap-2">
                                        <AlertTriangle className="w-5 h-5" />
                                        Missing Parameters
                                    </h3>
                                    <p className="text-sm text-amber-700 mt-2">
                                        {data.parameters.filter(p => p.missing).map(p => p.display_name).join(', ')}
                                    </p>
                                </div>
                            )}
                        </div>
                    ) : null}
                </div>
            </div>
        </div>
    );
}
