import { Coins, Database, Gauge, Hash } from "lucide-react";

import type { RunUsage } from "../../types/api";

interface UsageSummaryProps {
    usage: RunUsage;
}

function formatCost(value: number) {
    if (value === 0) {
        return "$0.00";
    }

    if (value < 0.01) {
        return `$${value.toFixed(6)}`;
    }

    return `$${value.toFixed(4)}`;
}

export default function UsageSummary({ usage }: UsageSummaryProps) {
    return (
        <div className="mt-6">
            <div className="mb-3">
                <h3 className="text-sm font-semibold text-slate-900">
                    Usage & cost
                </h3>

                <p className="mt-0.5 text-xs text-slate-500">
                    Estimated LLM usage for this workflow run.
                </p>
            </div>

            <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                    <div className="flex items-center gap-2 text-slate-500">
                        <Hash size={15} />
                        <span className="text-xs font-medium">
                            Total tokens
                        </span>
                    </div>

                    <p className="mt-2 text-lg font-semibold text-slate-900">
                        {usage.total_tokens.toLocaleString()}
                    </p>
                </div>

                <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                    <div className="flex items-center gap-2 text-slate-500">
                        <Database size={15} />
                        <span className="text-xs font-medium">
                            Input tokens
                        </span>
                    </div>

                    <p className="mt-2 text-lg font-semibold text-slate-900">
                        {usage.input_tokens.toLocaleString()}
                    </p>
                </div>

                <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                    <div className="flex items-center gap-2 text-slate-500">
                        <Gauge size={15} />
                        <span className="text-xs font-medium">
                            Output tokens
                        </span>
                    </div>

                    <p className="mt-2 text-lg font-semibold text-slate-900">
                        {usage.output_tokens.toLocaleString()}
                    </p>
                </div>

                <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                    <div className="flex items-center gap-2 text-slate-500">
                        <Coins size={15} />
                        <span className="text-xs font-medium">
                            Estimated cost
                        </span>
                    </div>

                    <p className="mt-2 text-lg font-semibold text-slate-900">
                        {formatCost(usage.estimated_cost_usd)}
                    </p>
                </div>
            </div>
        </div>
    );
}
