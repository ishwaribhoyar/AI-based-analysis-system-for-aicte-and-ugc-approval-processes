'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
    Home, Upload, BarChart3, GitCompare, Shield, FileText, Sparkles, TrendingUp, Target
} from 'lucide-react';

const navItems = [
    { href: '/', label: 'Home', icon: Home },
    { href: '/compare', label: 'Compare', icon: GitCompare },
    { href: '/analytics/multi-year', label: 'Trends', icon: TrendingUp },
    { href: '/analytics/prediction', label: 'Forecast', icon: Target },
];

export default function Navbar() {
    const pathname = usePathname();

    // Don't show navbar on home page
    if (pathname === '/') return null;

    return (
        <nav className="fixed top-0 left-0 right-0 z-50 bg-white/90 backdrop-blur-lg border-b border-gray-100 shadow-sm">
            <div className="container mx-auto px-4">
                <div className="flex items-center justify-between h-16">
                    {/* Logo */}
                    <Link href="/" className="flex items-center gap-2">
                        <div className="w-9 h-9 bg-gradient-to-br from-primary to-primary-light rounded-xl flex items-center justify-center">
                            <Sparkles className="w-5 h-5 text-white" />
                        </div>
                        <span className="font-bold text-gray-800 hidden sm:block">Smart Approval AI</span>
                    </Link>

                    {/* Nav Links */}
                    <div className="flex items-center gap-1">
                        {navItems.map((item) => {
                            const isActive = pathname === item.href;
                            const Icon = item.icon;
                            return (
                                <Link
                                    key={item.href}
                                    href={item.href}
                                    className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all ${isActive
                                        ? 'bg-primary text-white'
                                        : 'text-gray-600 hover:bg-gray-100'
                                        }`}
                                >
                                    <Icon className="w-4 h-4" />
                                    <span className="hidden sm:block">{item.label}</span>
                                </Link>
                            );
                        })}

                        {/* Dynamic links based on current batch context */}
                        {pathname.includes('dashboard') && (
                            <>
                                <Link
                                    href={`/unified-report${pathname.includes('batch_id') ? `?batch_id=${new URLSearchParams(window.location.search).get('batch_id')}` : ''}`}
                                    className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium text-gray-600 hover:bg-lavender-50 hover:text-lavender transition-all"
                                >
                                    <FileText className="w-4 h-4" />
                                    <span className="hidden sm:block">Report</span>
                                </Link>
                            </>
                        )}
                    </div>
                </div>
            </div>
        </nav>
    );
}
