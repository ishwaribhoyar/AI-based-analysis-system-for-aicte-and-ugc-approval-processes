'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { dashboardApi, type DashboardResponse, type BlockWithData } from '@/lib/api';
import toast from 'react-hot-toast';
import {
    ArrowLeft, FileText, Table, Sheet, ChevronDown, ChevronRight,
    RefreshCw, Eye
} from 'lucide-react';

const FILE_ICONS: Record<string, string> = {
    'PDF': '📄',
    'EXCEL': '📊',
    'CSV': '📋',
    'WORD': '📝',
};

function DocumentViewerContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const batchId = searchParams.get('batch_id') || '';

    const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [expandedBlocks, setExpandedBlocks] = useState<Set<string>>(new Set());

    useEffect(() => {
        if (batchId) {
            fetchDashboard();
        }
    }, [batchId]);

    const fetchDashboard = async () => {
        try {
            const data = await dashboardApi.get(batchId);
            setDashboard(data);
        } catch (err) {
            console.error(err);
            toast.error('Failed to load documents');
        } finally {
            setLoading(false);
        }
    };

    const toggleBlock = (blockId: string) => {
        setExpandedBlocks(prev => {
            const next = new Set(prev);
            if (next.has(blockId)) {
                next.delete(blockId);
            } else {
                next.add(blockId);
            }
            return next;
        });
    };

    const renderDataTable = (data: Record<string, unknown>) => {
        const entries = Object.entries(data).filter(([k, v]) =>
            v !== null && v !== '' && k !== 'evidence' && !k.endsWith('_num')
        );

        if (entries.length === 0) {
            return <p className="text-gray-500 italic">No data extracted</p>;
        }

        return (
            <table className="w-full text-sm">
                <thead>
                    <tr className="border-b border-gray-200">
                        <th className="text-left py-2 px-3 font-semibold text-gray-700">Field</th>
                        <th className="text-left py-2 px-3 font-semibold text-gray-700">Value</th>
                    </tr>
                </thead>
                <tbody>
                    {entries.map(([key, value]) => (
                        <tr key={key} className="border-b border-gray-50 hover:bg-gray-50">
                            <td className="py-2 px-3 text-gray-600 font-medium">
                                {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                            </td>
                            <td className="py-2 px-3 text-gray-800">
                                {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        );
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-soft flex items-center justify-center">
                <RefreshCw className="w-8 h-8 text-primary animate-spin" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-soft py-8">
            <div className="container mx-auto px-4 max-w-6xl">
                {/* Header */}
                <div className="flex items-center gap-4 mb-8">
                    <button onClick={() => router.back()} className="p-2 bg-white rounded-xl shadow-soft hover:shadow-soft-lg transition-all">
                        <ArrowLeft className="w-5 h-5 text-gray-600" />
                    </button>
                    <div>
                        <h1 className="text-3xl font-bold text-gray-800">Document Viewer</h1>
                        <p className="text-gray-600">Extracted data from all uploaded documents</p>
                    </div>
                </div>

                {/* Summary Stats */}
                <div className="grid md:grid-cols-4 gap-4 mb-8">
                    <div className="bg-white rounded-2xl p-4 shadow-soft">
                        <p className="text-sm text-gray-500">Total Documents</p>
                        <p className="text-2xl font-bold text-primary">{dashboard?.total_documents || 0}</p>
                    </div>
                    <div className="bg-white rounded-2xl p-4 shadow-soft">
                        <p className="text-sm text-gray-500">Blocks Extracted</p>
                        <p className="text-2xl font-bold text-gray-800">{dashboard?.blocks?.length || 0}</p>
                    </div>
                    <div className="bg-white rounded-2xl p-4 shadow-soft">
                        <p className="text-sm text-gray-500">Mode</p>
                        <p className="text-2xl font-bold text-primary uppercase">{dashboard?.mode || 'unknown'}</p>
                    </div>
                    <div className="bg-white rounded-2xl p-4 shadow-soft">
                        <p className="text-sm text-gray-500">Sufficiency</p>
                        <p className="text-2xl font-bold text-gray-800">{dashboard?.sufficiency?.percentage?.toFixed(0) || 0}%</p>
                    </div>
                </div>

                {/* Blocks as Collapsible Sections */}
                <div className="space-y-4">
                    {dashboard?.blocks?.map((block: BlockWithData) => {
                        const isExpanded = expandedBlocks.has(block.block_id);
                        const fieldCount = Object.keys(block.data || {}).filter(k =>
                            block.data[k] !== null && block.data[k] !== '' && k !== 'evidence'
                        ).length;

                        return (
                            <div key={block.block_id} className="bg-white rounded-2xl shadow-soft overflow-hidden">
                                {/* Block Header */}
                                <button
                                    onClick={() => toggleBlock(block.block_id)}
                                    className="w-full p-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
                                >
                                    <div className="flex items-center gap-3">
                                        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${block.is_present ? 'bg-primary-100' : 'bg-gray-100'
                                            }`}>
                                            <FileText className={`w-5 h-5 ${block.is_present ? 'text-primary' : 'text-gray-400'}`} />
                                        </div>
                                        <div className="text-left">
                                            <h3 className="font-semibold text-gray-800">{block.block_name}</h3>
                                            <p className="text-sm text-gray-500">
                                                {fieldCount} fields extracted
                                                {block.source_doc && ` • Source: ${block.source_doc}`}
                                            </p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        {/* Status badges */}
                                        {block.is_outdated && (
                                            <span className="px-2 py-1 bg-yellow-100 text-yellow-700 text-xs rounded-full">Outdated</span>
                                        )}
                                        {block.is_low_quality && (
                                            <span className="px-2 py-1 bg-orange-100 text-orange-700 text-xs rounded-full">Low Quality</span>
                                        )}
                                        {block.is_invalid && (
                                            <span className="px-2 py-1 bg-red-100 text-red-700 text-xs rounded-full">Invalid</span>
                                        )}
                                        <span className="text-sm text-gray-500">
                                            {(block.confidence * 100).toFixed(0)}% conf
                                        </span>
                                        {isExpanded ? (
                                            <ChevronDown className="w-5 h-5 text-gray-400" />
                                        ) : (
                                            <ChevronRight className="w-5 h-5 text-gray-400" />
                                        )}
                                    </div>
                                </button>

                                {/* Block Content */}
                                {isExpanded && (
                                    <div className="border-t border-gray-100 p-4">
                                        {block.data && Object.keys(block.data).length > 0 ? (
                                            renderDataTable(block.data)
                                        ) : (
                                            <p className="text-gray-500 italic text-center py-4">No data available for this block</p>
                                        )}

                                        {/* Evidence snippet if available */}
                                        {block.evidence_snippet && (
                                            <div className="mt-4 p-3 bg-gray-50 rounded-xl">
                                                <p className="text-xs text-gray-500 mb-1">Evidence (Page {block.evidence_page || 1}):</p>
                                                <p className="text-sm text-gray-700 line-clamp-3">{block.evidence_snippet}</p>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>

                {/* No blocks message */}
                {(!dashboard?.blocks || dashboard.blocks.length === 0) && (
                    <div className="bg-white rounded-3xl shadow-soft-lg p-12 text-center">
                        <Eye className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                        <h3 className="text-xl font-semibold text-gray-700">No Documents Processed</h3>
                        <p className="text-gray-500 mt-2">Upload documents to see extracted data here.</p>
                    </div>
                )}
            </div>
        </div>
    );
}

export default function DocumentViewerPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen bg-gradient-soft flex items-center justify-center">
                <RefreshCw className="w-8 h-8 text-primary animate-spin" />
            </div>
        }>
            <DocumentViewerContent />
        </Suspense>
    );
}
