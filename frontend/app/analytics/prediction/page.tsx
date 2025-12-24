'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter } from 'next/navigation';
import { analyticsApi, batchApi, type PredictionResponse, type BatchResponse } from '@/lib/api';
import toast from 'react-hot-toast';
import {
    TrendingUp, TrendingDown, Minus, ArrowLeft, RefreshCw,
    BarChart3, Target, AlertTriangle, CheckCircle, Lightbulb, Download, Check
} from 'lucide-react';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
    ResponsiveContainer, ReferenceLine
} from 'recharts';

const CHART_COLORS = {
    actual: '#0D9488',
    predicted: '#F97316',
};

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

function PredictionPage() {
    const router = useRouter();
    const [allBatches, setAllBatches] = useState<BatchResponse[]>([]);
    const [selectedBatches, setSelectedBatches] = useState<string[]>([]);
    const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [loadingBatches, setLoadingBatches] = useState(true);
    const [selectedMetric, setSelectedMetric] = useState('overall_score');

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

    const fetchPrediction = async () => {
        if (selectedBatches.length === 0) {
            toast.error('Select at least one batch');
            return;
        }
        setLoading(true);
        try {
            const data = await analyticsApi.predict(selectedBatches, 5);
            setPrediction(data);

            if (!data.has_enough_data) {
                toast.error(data.error_message || 'Not enough data for prediction');
            }
        } catch (err) {
            console.error(err);
            toast.error('Failed to generate predictions');
        } finally {
            setLoading(false);
        }
    };

    const downloadJSON = () => {
        if (!prediction) return;
        const blob = new Blob([JSON.stringify(prediction, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `prediction_${Date.now()}.json`;
        a.click();
    };

    // Prepare chart data for selected metric - sorted by year
    const chartData = prediction && prediction.forecasts[selectedMetric] ? (() => {
        const forecast = prediction.forecasts[selectedMetric];
        if (!forecast) return [];
        
        const data: Array<{ year: string | number; actual: number | null; predicted: number | null }> = [];

        // Extract year number for sorting
        const extractYearNum = (yearStr: string | number): number => {
            const str = String(yearStr);
            const match = str.match(/(\d{4})/);
            return match ? parseInt(match[1], 10) : 0;
        };

        // Historical data
        if (forecast.historical_values && Array.isArray(forecast.historical_values)) {
            forecast.historical_values.forEach(v => {
                if (v && v.year && v.value !== null && v.value !== undefined) {
                    data.push({
                        year: v.year,
                        actual: v.value as number,
                        predicted: null,
                    });
                }
            });
        }

        // Predicted data
        if (forecast.predicted_values && Array.isArray(forecast.predicted_values)) {
            forecast.predicted_values.forEach(v => {
                if (v && v.year && v.value !== null && v.value !== undefined) {
                    data.push({
                        year: v.year,
                        actual: null,
                        predicted: v.value as number,
                    });
                }
            });
        }

        // Sort by year (chronological order)
        data.sort((a, b) => {
            const yearA = extractYearNum(a.year);
            const yearB = extractYearNum(b.year);
            return yearA - yearB;
        });

        // Add connecting point between historical and predicted
        if (data.length > 0) {
            // Find the last historical point and first predicted point
            let lastHistoricalIdx = -1;
            let firstPredictedIdx = -1;
            
            for (let i = 0; i < data.length; i++) {
                if (data[i].actual !== null && lastHistoricalIdx === -1) {
                    lastHistoricalIdx = i;
                }
                if (data[i].predicted !== null && firstPredictedIdx === -1) {
                    firstPredictedIdx = i;
                }
            }
            
            // If there's a gap, add a connecting point
            if (lastHistoricalIdx >= 0 && firstPredictedIdx >= 0 && firstPredictedIdx > lastHistoricalIdx + 1) {
                const lastHistorical = data[lastHistoricalIdx];
                const firstPredicted = data[firstPredictedIdx];
                
                // Check if years are consecutive
                const lastYear = extractYearNum(lastHistorical.year);
                const firstYear = extractYearNum(firstPredicted.year);
                
                if (firstYear === lastYear + 1) {
                    // Years are consecutive, add connecting point
                    data.splice(firstPredictedIdx, 0, {
                        year: lastHistorical.year,
                        actual: lastHistorical.actual,
                        predicted: lastHistorical.actual, // Connect the lines
                    });
                }
            }
        }

        return data;
    })() : [];

    return (
        <div className="min-h-screen bg-gradient-soft py-8">
            <div className="container mx-auto px-4 max-w-7xl">
                {/* Header */}
                <div className="flex items-center gap-4 mb-8">
                    <button onClick={() => router.push('/')} className="p-2 bg-white rounded-xl shadow-soft hover:shadow-soft-lg transition-all">
                        <ArrowLeft className="w-5 h-5 text-gray-600" />
                    </button>
                    <div>
                        <h1 className="text-3xl font-bold text-gray-800">5-Year Prediction</h1>
                        <p className="text-gray-600">Statistical forecasting based on historical trends</p>
                    </div>
                </div>

                {/* Selection Panel */}
                <div className="bg-white rounded-3xl shadow-soft-lg p-6 mb-8">
                    <h2 className="text-xl font-semibold text-gray-800 mb-4">Select Historical Data</h2>
                    <p className="text-sm text-gray-500 mb-4">Minimum 3 years of data required for accurate predictions</p>

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
                        onClick={fetchPrediction}
                        disabled={selectedBatches.length === 0 || loading}
                        className="w-full md:w-auto px-6 py-3 bg-gradient-to-r from-accent to-orange-500 text-white rounded-xl font-medium hover:shadow-glow-coral disabled:opacity-50 transition-all"
                    >
                        {loading ? <RefreshCw className="w-5 h-5 animate-spin inline mr-2" /> : <Target className="w-5 h-5 inline mr-2" />}
                        Generate 5-Year Forecast
                    </button>
                </div>

                {/* Error State */}
                {prediction && !prediction.has_enough_data && (
                    <div className="bg-red-50 border border-red-200 rounded-2xl p-6 mb-8 text-center">
                        <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-3" />
                        <h3 className="font-semibold text-red-800 text-lg">Insufficient Data</h3>
                        <p className="text-red-600 mt-2">{prediction.error_message}</p>
                        <p className="text-sm text-red-500 mt-2">Select more batches covering at least 3 different years.</p>
                    </div>
                )}

                {/* Prediction Results */}
                {prediction && prediction.has_enough_data && (
                    <>
                        {/* Summary */}
                        <div className="grid md:grid-cols-3 gap-4 mb-8">
                            <div className="bg-white rounded-2xl p-4 shadow-soft">
                                <p className="text-sm text-gray-500">Institution</p>
                                <p className="text-lg font-bold text-gray-800 truncate">{prediction.institution_name}</p>
                            </div>
                            <div className="bg-white rounded-2xl p-4 shadow-soft">
                                <p className="text-sm text-gray-500">Historical Data</p>
                                <p className="text-lg font-bold text-primary">{prediction.historical_years.length} years</p>
                            </div>
                            <div className="bg-white rounded-2xl p-4 shadow-soft">
                                <p className="text-sm text-gray-500">Forecasting</p>
                                <p className="text-lg font-bold text-accent">{prediction.prediction_years.length} years ahead</p>
                            </div>
                        </div>

                        {/* Metric Selector */}
                        <div className="bg-white rounded-3xl shadow-soft-lg p-6 mb-8">
                            <div className="flex flex-wrap gap-2 mb-6">
                                {Object.keys(prediction.forecasts).map(metric => (
                                    <button
                                        key={metric}
                                        onClick={() => setSelectedMetric(metric)}
                                        className={`px-4 py-2 rounded-xl font-medium transition-all ${selectedMetric === metric
                                                ? 'bg-primary text-white'
                                                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                            }`}
                                    >
                                        {formatMetricName(metric)}
                                    </button>
                                ))}
                            </div>

                            {/* Forecast Chart */}
                            <h2 className="text-xl font-semibold text-gray-800 mb-4 flex items-center gap-2">
                                <BarChart3 className="w-6 h-6 text-primary" />
                                {formatMetricName(selectedMetric)} Forecast
                            </h2>
                            <div className="flex items-center gap-6 mb-4 text-sm">
                                <span className="flex items-center gap-2">
                                    <div className="w-4 h-1 bg-[#0D9488] rounded" />
                                    Historical (Actual)
                                </span>
                                <span className="flex items-center gap-2">
                                    <div className="w-4 h-1 bg-[#F97316] rounded" style={{ borderStyle: 'dashed' }} />
                                    Predicted
                                </span>
                            </div>
                            {chartData.length > 0 ? (
                                <ResponsiveContainer width="100%" height={400}>
                                    <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                                        <XAxis 
                                            dataKey="year" 
                                            tick={{ fill: '#6B7280', fontSize: 12 }}
                                            type="category"
                                            allowDuplicatedCategory={false}
                                        />
                                        <YAxis 
                                            domain={[0, 100]} 
                                            tick={{ fill: '#6B7280', fontSize: 12 }}
                                            label={{ value: 'Score', angle: -90, position: 'insideLeft' }}
                                        />
                                        <Tooltip 
                                            formatter={(value: number, name: string) => [
                                                value !== null ? value.toFixed(2) : 'N/A',
                                                name === 'actual' ? 'Historical' : 'Predicted'
                                            ]}
                                            labelFormatter={(label) => `Year: ${label}`}
                                        />
                                        <Legend />
                                        {prediction.historical_years && prediction.historical_years.length > 0 && (
                                            <ReferenceLine
                                                x={prediction.historical_years[prediction.historical_years.length - 1]}
                                                stroke="#9CA3AF"
                                                strokeDasharray="5 5"
                                                strokeWidth={2}
                                                label={{ value: 'Now', position: 'top', fill: '#6B7280', fontSize: 12 }}
                                            />
                                        )}
                                        <Line
                                            type="monotone"
                                            dataKey="actual"
                                            name="Historical"
                                            stroke={CHART_COLORS.actual}
                                            strokeWidth={3}
                                            dot={{ r: 5, fill: CHART_COLORS.actual, strokeWidth: 2 }}
                                            activeDot={{ r: 7 }}
                                            connectNulls={false}
                                        />
                                        <Line
                                            type="monotone"
                                            dataKey="predicted"
                                            name="Predicted"
                                            stroke={CHART_COLORS.predicted}
                                            strokeWidth={3}
                                            strokeDasharray="8 4"
                                            dot={{ r: 5, fill: CHART_COLORS.predicted, strokeWidth: 2 }}
                                            activeDot={{ r: 7 }}
                                            connectNulls={false}
                                        />
                                    </LineChart>
                                </ResponsiveContainer>
                            ) : (
                                <div className="text-center py-12 text-gray-500">
                                    <p>No forecast data available for this metric</p>
                                    <p className="text-sm mt-2">Ensure you have at least 3 years of historical data</p>
                                </div>
                            )}
                        </div>

                        {/* Metric Details */}
                        <div className="grid md:grid-cols-2 gap-6 mb-8">
                            {Object.entries(prediction.forecasts).map(([metric, forecast]) => (
                                <div key={metric} className="bg-white rounded-2xl shadow-soft p-5">
                                    <div className="flex items-center justify-between mb-3">
                                        <h3 className="font-semibold text-gray-800">{forecast.display_name}</h3>
                                        <TrendIcon direction={forecast.trend_direction} />
                                    </div>
                                    <div className="flex items-center gap-4 mb-3">
                                        <div className="flex-1">
                                            <p className="text-xs text-gray-500">Confidence</p>
                                            <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                                                <div
                                                    className="bg-primary h-2 rounded-full"
                                                    style={{ width: `${(forecast.confidence * 100).toFixed(0)}%` }}
                                                />
                                            </div>
                                        </div>
                                        <span className="text-sm font-medium text-gray-600">
                                            {(forecast.confidence * 100).toFixed(0)}%
                                        </span>
                                    </div>
                                    <p className="text-sm text-gray-600">{forecast.explanation}</p>
                                </div>
                            ))}
                        </div>

                        {/* Insights */}
                        <div className="grid md:grid-cols-3 gap-6 mb-8">
                            {/* Growth Areas */}
                            {prediction.growth_areas.length > 0 && (
                                <div className="bg-green-50 rounded-2xl p-5">
                                    <h3 className="font-semibold text-green-800 mb-3 flex items-center gap-2">
                                        <TrendingUp className="w-5 h-5" /> Growth Areas
                                    </h3>
                                    <ul className="space-y-2">
                                        {prediction.growth_areas.map((area, i) => (
                                            <li key={i} className="text-sm text-green-700">{area}</li>
                                        ))}
                                    </ul>
                                </div>
                            )}

                            {/* Decline Warnings */}
                            {prediction.decline_warnings.length > 0 && (
                                <div className="bg-red-50 rounded-2xl p-5">
                                    <h3 className="font-semibold text-red-800 mb-3 flex items-center gap-2">
                                        <AlertTriangle className="w-5 h-5" /> Decline Warnings
                                    </h3>
                                    <ul className="space-y-2">
                                        {prediction.decline_warnings.map((warning, i) => (
                                            <li key={i} className="text-sm text-red-700">{warning}</li>
                                        ))}
                                    </ul>
                                </div>
                            )}

                            {/* Recommendations */}
                            {prediction.recommendations.length > 0 && (
                                <div className="bg-blue-50 rounded-2xl p-5">
                                    <h3 className="font-semibold text-blue-800 mb-3 flex items-center gap-2">
                                        <Lightbulb className="w-5 h-5" /> Recommendations
                                    </h3>
                                    <ul className="space-y-2">
                                        {prediction.recommendations.map((rec, i) => (
                                            <li key={i} className="text-sm text-blue-700">{rec}</li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </div>

                        {/* Export */}
                        <div className="flex justify-center gap-4">
                            <button
                                onClick={downloadJSON}
                                className="px-6 py-3 bg-gray-100 text-gray-700 rounded-xl font-medium hover:bg-gray-200 transition-all flex items-center gap-2"
                            >
                                <Download className="w-5 h-5" />
                                Download Forecast JSON
                            </button>
                        </div>
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
            <PredictionPage />
        </Suspense>
    );
}
