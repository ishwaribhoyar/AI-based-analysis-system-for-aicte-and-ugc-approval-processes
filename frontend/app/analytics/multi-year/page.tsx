'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter } from 'next/navigation';
import { analyticsApi, batchApi, type MultiYearAnalyticsResponse, type BatchResponse } from '@/lib/api';
import toast from 'react-hot-toast';
import {
    TrendingUp, TrendingDown, Minus, ArrowLeft, RefreshCw,
    BarChart3, LineChart as LineChartIcon, Check, Calendar
} from 'lucide-react';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
    ResponsiveContainer, BarChart, Bar
} from 'recharts';

const CHART_COLORS = ['#0D9488', '#F97316', '#8B5CF6', '#059669', '#EC4899'];

const formatMetricName = (key: string): string => {
    const map: Record<string, string> = {
        'fsr_score': 'FSR Score',
        'infrastructure_score': 'Infrastructure',
        'placement_index': 'Placement Index',
        'lab_compliance_index': 'Lab Compliance',
        'overall_score': 'Overall Score',
    };
    return map[key] || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
};

const TrendIcon = ({ direction }: { direction: string }) => {
    if (direction === 'up') return <TrendingUp className="w-5 h-5 text-green-500" />;
    if (direction === 'down') return <TrendingDown className="w-5 h-5 text-red-500" />;
    return <Minus className="w-5 h-5 text-gray-400" />;
};

function MultiYearAnalyticsPage() {
    const router = useRouter();
    const [allBatches, setAllBatches] = useState<BatchResponse[]>([]);
    const [selectedBatches, setSelectedBatches] = useState<string[]>([]);
    const [years, setYears] = useState(5);
    const [analytics, setAnalytics] = useState<MultiYearAnalyticsResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [loadingBatches, setLoadingBatches] = useState(true);

    useEffect(() => {
        const fetchBatches = async () => {
            try {
                const batches = await batchApi.list();
                const completed = batches.filter(b => b.status === 'completed' && b.total_documents >= 1);
                setAllBatches(completed);
            } catch (err) {
                console.error(err);
                toast.error('Failed to fetch batches');
            } finally {
                setLoadingBatches(false);
            }
        };
        fetchBatches();
    }, []);

    const toggleBatch = (batchId: string) => {
        setSelectedBatches(prev =>
            prev.includes(batchId)
                ? prev.filter(id => id !== batchId)
                : [...prev, batchId]
        );
    };

    const fetchAnalytics = async () => {
        if (selectedBatches.length === 0) {
            toast.error('Select at least one batch');
            return;
        }
        setLoading(true);
        try {
            const data = await analyticsApi.getMultiYear(selectedBatches, years);
            setAnalytics(data);
        } catch (err) {
            console.error(err);
            toast.error('Failed to fetch analytics');
        } finally {
            setLoading(false);
        }
    };

    // Prepare chart data
    const lineChartData = analytics?.available_years.map(year => {
        const point: Record<string, unknown> = { year };
        Object.entries(analytics.metrics).forEach(([kpi, values]) => {
            const val = values.find(v => v.year === year);
            point[formatMetricName(kpi)] = val?.value ?? null;
        });
        return point;
    }) || [];

    const barChartData = Object.entries(analytics?.trend_summary || {}).map(([kpi, trend]) => ({
        name: trend.display_name,
        average: trend.average || 0,
        min: trend.min_value || 0,
        max: trend.max_value || 0,
    }));

    return (
        <div className="min-h-screen bg-gradient-soft py-8">
            <div className="container mx-auto px-4 max-w-7xl">
                {/* Header */}
                <div className="flex items-center gap-4 mb-8">
                    <button onClick={() => router.push('/')} className="p-2 bg-white rounded-xl shadow-soft hover:shadow-soft-lg transition-all">
                        <ArrowLeft className="w-5 h-5 text-gray-600" />
                    </button>
                    <div>
                        <h1 className="text-3xl font-bold text-gray-800">Multi-Year Analytics</h1>
                        <p className="text-gray-600">Historical KPI trends and year-over-year analysis</p>
                    </div>
                </div>

                {/* Selection Panel */}
                <div className="bg-white rounded-3xl shadow-soft-lg p-6 mb-8">
                    <h2 className="text-xl font-semibold text-gray-800 mb-4">Select Data</h2>

                    {/* Year Selector */}
                    <div className="mb-6">
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            <Calendar className="w-4 h-4 inline mr-2" />
                            Years to Analyze: {years}
                        </label>
                        <input
                            type="range"
                            min="1"
                            max="10"
                            value={years}
                            onChange={e => setYears(parseInt(e.target.value))}
                            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary"
                        />
                        <div className="flex justify-between text-xs text-gray-500 mt-1">
                            <span>1 year</span>
                            <span>10 years</span>
                        </div>
                    </div>

                    {/* Batch Selector */}
                    {loadingBatches ? (
                        <div className="flex items-center justify-center py-8">
                            <RefreshCw className="w-6 h-6 text-primary animate-spin" />
                        </div>
                    ) : (
                        <div className="grid md:grid-cols-3 gap-3 mb-6">
                            {allBatches.map(batch => {
                                const isSelected = selectedBatches.includes(batch.batch_id);
                                return (
                                    <div
                                        key={batch.batch_id}
                                        onClick={() => toggleBatch(batch.batch_id)}
                                        className={`p-3 rounded-xl border cursor-pointer transition-all ${isSelected ? 'border-primary bg-primary-50' : 'border-gray-200 hover:border-primary-light'
                                            }`}
                                    >
                                        <div className="flex items-center justify-between">
                                            <div>
                                                <span className={`px-2 py-0.5 rounded text-xs font-semibold uppercase ${batch.mode === 'aicte' ? 'bg-primary-100 text-primary' : 'bg-accent-100 text-accent'
                                                    }`}>{batch.mode}</span>
                                                <p className="text-sm text-gray-700 mt-1">#{batch.batch_id.slice(-8)}</p>
                                            </div>
                                            <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${isSelected ? 'bg-primary border-primary' : 'border-gray-300'
                                                }`}>
                                                {isSelected && <Check className="w-3 h-3 text-white" />}
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}

                    <button
                        onClick={fetchAnalytics}
                        disabled={selectedBatches.length === 0 || loading}
                        className="w-full md:w-auto px-6 py-3 bg-gradient-to-r from-primary to-primary-light text-white rounded-xl font-medium hover:shadow-glow-teal disabled:opacity-50 transition-all"
                    >
                        {loading ? <RefreshCw className="w-5 h-5 animate-spin inline mr-2" /> : <BarChart3 className="w-5 h-5 inline mr-2" />}
                        Analyze Trends
                    </button>
                </div>

                {/* Results */}
                {analytics && (
                    <>
                        {/* Summary Cards */}
                        <div className="grid md:grid-cols-4 gap-4 mb-8">
                            <div className="bg-white rounded-2xl p-4 shadow-soft">
                                <p className="text-sm text-gray-500">Institution</p>
                                <p className="text-lg font-bold text-gray-800 truncate">{analytics.institution_name}</p>
                            </div>
                            <div className="bg-white rounded-2xl p-4 shadow-soft">
                                <p className="text-sm text-gray-500">Years Available</p>
                                <p className="text-lg font-bold text-primary">{analytics.available_years.length}</p>
                            </div>
                            <div className="bg-green-50 rounded-2xl p-4 shadow-soft">
                                <p className="text-sm text-green-700">Best Year</p>
                                <p className="text-lg font-bold text-green-800">{analytics.best_year || 'N/A'}</p>
                            </div>
                            <div className="bg-red-50 rounded-2xl p-4 shadow-soft">
                                <p className="text-sm text-red-700">Needs Improvement</p>
                                <p className="text-lg font-bold text-red-800">{analytics.worst_year || 'N/A'}</p>
                            </div>
                        </div>

                        {/* Trend Line Chart */}
                        <div className="bg-white rounded-3xl shadow-soft-lg p-6 mb-8">
                            <h2 className="text-xl font-semibold text-gray-800 mb-4 flex items-center gap-2">
                                <LineChartIcon className="w-6 h-6 text-primary" />
                                KPI Trends Over Time
                            </h2>
                            <ResponsiveContainer width="100%" height={400}>
                                <LineChart data={lineChartData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                                    <XAxis dataKey="year" tick={{ fill: '#6B7280', fontSize: 12 }} />
                                    <YAxis domain={[0, 100]} tick={{ fill: '#6B7280', fontSize: 12 }} />
                                    <Tooltip />
                                    <Legend />
                                    {Object.keys(analytics.metrics).map((kpi, idx) => (
                                        <Line
                                            key={kpi}
                                            type="monotone"
                                            dataKey={formatMetricName(kpi)}
                                            stroke={CHART_COLORS[idx % CHART_COLORS.length]}
                                            strokeWidth={2}
                                            dot={{ r: 4 }}
                                            activeDot={{ r: 6 }}
                                        />
                                    ))}
                                </LineChart>
                            </ResponsiveContainer>
                        </div>

                        {/* Summary Bar Chart */}
                        <div className="bg-white rounded-3xl shadow-soft-lg p-6 mb-8">
                            <h2 className="text-xl font-semibold text-gray-800 mb-4 flex items-center gap-2">
                                <BarChart3 className="w-6 h-6 text-primary" />
                                Average Performance by KPI
                            </h2>
                            <ResponsiveContainer width="100%" height={300}>
                                <BarChart data={barChartData} layout="vertical">
                                    <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                                    <XAxis type="number" domain={[0, 100]} />
                                    <YAxis dataKey="name" type="category" width={120} tick={{ fontSize: 12 }} />
                                    <Tooltip />
                                    <Bar dataKey="average" fill="#0D9488" radius={[0, 4, 4, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>

                        {/* Trend Summary */}
                        <div className="bg-white rounded-3xl shadow-soft-lg p-6 mb-8">
                            <h2 className="text-xl font-semibold text-gray-800 mb-4">Trend Analysis</h2>
                            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                                {Object.entries(analytics.trend_summary).map(([kpi, trend]) => (
                                    <div key={kpi} className="bg-gray-50 rounded-2xl p-4">
                                        <div className="flex items-center justify-between mb-2">
                                            <span className="font-medium text-gray-800">{trend.display_name}</span>
                                            <TrendIcon direction={trend.trend_direction} />
                                        </div>
                                        <div className="text-2xl font-bold text-primary mb-1">
                                            {trend.average?.toFixed(1) || 'N/A'}
                                        </div>
                                        <div className="text-xs text-gray-500">
                                            Range: {trend.min_value?.toFixed(1)} - {trend.max_value?.toFixed(1)}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Insights */}
                        {analytics.insights.length > 0 && (
                            <div className="bg-gradient-to-r from-primary to-primary-light rounded-3xl p-6 text-white">
                                <h2 className="text-xl font-semibold mb-4">Key Insights</h2>
                                <ul className="space-y-2">
                                    {analytics.insights.map((insight, i) => (
                                        <li key={i} className="flex items-start gap-2">
                                            <span className="text-lg">{insight}</span>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </>
                )}
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
            <MultiYearAnalyticsPage />
        </Suspense>
    );
}
