import {
    CheckCircle2,
    ChevronDown,
    Circle,
    Clock,
    AlertCircle,
} from "lucide-react";
import { useState } from "react";

interface StageRun {
    stage: string;
    status: string;
    attempt: number;
    message?: string | null;
    details?: Record<string, unknown>;
    started_at?: string | null;
    completed_at?: string | null;
    error?: string | null;
}

interface StageDetailsProps {
    stage: StageRun;
}

function formatStageName(stage: string) {
    return stage.charAt(0).toUpperCase() + stage.slice(1);
}

function formatKey(key: string) {
    return key
        .replace(/_/g, " ")
        .replace(/\b\w/g, (char) => char.toUpperCase());
}

function renderValue(value: unknown): React.ReactNode {
    if (value === null || value === undefined) {
        return null;
    }

    if (typeof value === "boolean") {
        return value ? "Yes" : "No";
    }

    if (typeof value === "string" || typeof value === "number") {
        return String(value);
    }

    if (Array.isArray(value)) {
        if (value.length === 0) {
            return "None";
        }

        return (
            <div className="space-y-2">
                {value.map((item, index) => (
                    <div
                        key={index}
                        className="rounded-lg border border-slate-200 bg-slate-50 p-3"
                    >
                        {typeof item === "object" && item !== null ? (
                            <pre className="whitespace-pre-wrap text-xs text-slate-600">
                                {JSON.stringify(item, null, 2)}
                            </pre>
                        ) : (
                            String(item)
                        )}
                    </div>
                ))}
            </div>
        );
    }

    if (typeof value === "object") {
        return (
            <pre className="whitespace-pre-wrap rounded-lg bg-slate-50 p-3 text-xs text-slate-600">
                {JSON.stringify(value, null, 2)}
            </pre>
        );
    }

    return String(value);
}

export default function StageDetails({ stage }: StageDetailsProps) {
    const [expanded, setExpanded] = useState(false);

    const status = stage.status.toLowerCase();

    const isCompleted = status === "completed";
    const isSkipped = status === "skipped";
    const isFailed = status === "failed";
    const isEscalated = status === "escalated";
    const isRunning = status === "running";

    const hasDetails =
        Boolean(stage.message) ||
        Boolean(stage.details && Object.keys(stage.details).length > 0) ||
        Boolean(stage.error);

    return (
        <div className="border-b border-slate-200 last:border-b-0">
            <button
                type="button"
                onClick={() => hasDetails && setExpanded(!expanded)}
                className={`flex w-full items-center gap-4 px-6 py-5 text-left ${
                    hasDetails
                        ? "cursor-pointer hover:bg-slate-50"
                        : "cursor-default"
                }`}
            >
                <div className="shrink-0">
                    {isCompleted && (
                        <CheckCircle2 size={24} className="text-emerald-500" />
                    )}

                    {isSkipped && (
                        <Circle size={24} className="text-slate-400" />
                    )}

                    {isFailed && (
                        <AlertCircle size={24} className="text-red-500" />
                    )}

                    {isEscalated && (
                        <AlertCircle size={24} className="text-amber-500" />
                    )}

                    {isRunning && <Clock size={24} className="text-blue-500" />}

                    {!isCompleted &&
                        !isSkipped &&
                        !isFailed &&
                        !isEscalated &&
                        !isRunning && (
                            <Circle size={24} className="text-slate-400" />
                        )}
                </div>

                <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-4">
                        <div>
                            <h3 className="font-semibold text-slate-900">
                                {formatStageName(stage.stage)}
                            </h3>

                            <p className="text-sm text-slate-500">
                                {formatStageName(stage.status)} · Attempt{" "}
                                {stage.attempt}
                            </p>
                        </div>

                        <div className="flex items-center gap-3">
                            <span
                                className={`text-sm font-medium ${
                                    isCompleted
                                        ? "text-emerald-600"
                                        : isSkipped
                                          ? "text-slate-500"
                                          : isFailed
                                            ? "text-red-600"
                                            : isEscalated
                                              ? "text-amber-600"
                                              : "text-blue-600"
                                }`}
                            >
                                {formatStageName(stage.status)}
                            </span>

                            {hasDetails && (
                                <ChevronDown
                                    size={20}
                                    className={`transition-transform ${
                                        expanded ? "rotate-180" : ""
                                    }`}
                                />
                            )}
                        </div>
                    </div>
                </div>
            </button>

            {expanded && hasDetails && (
                <div className="px-6 pb-6 pl-19">
                    {stage.message && (
                        <div className="mb-4">
                            <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-400">
                                Result
                            </p>

                            <p className="text-sm text-slate-700">
                                {stage.message}
                            </p>
                        </div>
                    )}

                    {stage.details && Object.keys(stage.details).length > 0 && (
                        <div>
                            <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-400">
                                Stage details
                            </p>

                            <div className="space-y-4">
                                {Object.entries(stage.details).map(
                                    ([key, value]) => (
                                        <div key={key}>
                                            <p className="mb-1 text-sm font-medium text-slate-700">
                                                {formatKey(key)}
                                            </p>

                                            <div className="text-sm text-slate-600">
                                                {renderValue(value)}
                                            </div>
                                        </div>
                                    ),
                                )}
                            </div>
                        </div>
                    )}

                    {stage.error && (
                        <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-3">
                            <p className="text-xs font-semibold uppercase tracking-wide text-red-600">
                                Error
                            </p>

                            <p className="mt-1 text-sm text-red-700">
                                {stage.error}
                            </p>
                        </div>
                    )}

                    {(stage.started_at || stage.completed_at) && (
                        <div className="mt-5 flex gap-6 text-xs text-slate-400">
                            {stage.started_at && (
                                <span>
                                    Started:{" "}
                                    {new Date(
                                        stage.started_at,
                                    ).toLocaleString()}
                                </span>
                            )}

                            {stage.completed_at && (
                                <span>
                                    Completed:{" "}
                                    {new Date(
                                        stage.completed_at,
                                    ).toLocaleString()}
                                </span>
                            )}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
