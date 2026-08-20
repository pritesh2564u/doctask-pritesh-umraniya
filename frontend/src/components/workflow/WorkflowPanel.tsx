import { useState } from "react";

import {
    AlertCircle,
    Check,
    ChevronDown,
    Circle,
    Clock,
    Loader2,
    Play,
    X,
} from "lucide-react";

import { useCreateRun, useExecuteRun, useRun } from "../../hooks/useRun";
import type { StageStatus } from "../../types/api";
import UsageSummary from "./UsageSummary";

interface WorkflowPanelProps {
    projectId: string;
    onRunCreated?: (runId: string) => void;
}

const stageLabels = {
    ingest: "Ingest",
    extract: "Extract",
    analyze: "Analyze",
    reconcile: "Reconcile",
    review: "Review",
    commit: "Commit",
} as const;

function StageIcon({ status }: { status: StageStatus }) {
    if (status === "completed") {
        return (
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-100">
                <Check size={16} className="text-emerald-600" />
            </div>
        );
    }

    if (status === "running") {
        return (
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100">
                <Loader2 size={16} className="animate-spin text-blue-600" />
            </div>
        );
    }

    if (status === "failed") {
        return (
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-red-100">
                <X size={16} className="text-red-600" />
            </div>
        );
    }

    if (status === "escalated") {
        return (
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-amber-100">
                <AlertCircle size={16} className="text-amber-600" />
            </div>
        );
    }

    if (status === "skipped") {
        return (
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-100">
                <Circle size={14} className="text-slate-400" />
            </div>
        );
    }

    return (
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-100">
            <Clock size={16} className="text-slate-400" />
        </div>
    );
}

function formatStatus(status: StageStatus) {
    switch (status) {
        case "completed":
            return "Completed";

        case "running":
            return "Running";

        case "failed":
            return "Failed";

        case "skipped":
            return "Skipped";

        case "escalated":
            return "Needs attention";

        case "pending":
            return "Pending";

        default:
            return status;
    }
}

function formatDetailKey(key: string) {
    return key
        .replace(/_/g, " ")
        .replace(/\b\w/g, (character) => character.toUpperCase());
}

function formatDetailValue(value: unknown) {
    if (value === null || value === undefined) {
        return "None";
    }

    if (typeof value === "boolean") {
        return value ? "Yes" : "No";
    }

    if (typeof value === "string" || typeof value === "number") {
        return String(value);
    }

    return JSON.stringify(value, null, 2);
}

export default function WorkflowPanel({
    projectId,
    onRunCreated,
}: WorkflowPanelProps) {
    const createRunMutation = useCreateRun(projectId);
    const executeRunMutation = useExecuteRun(projectId);

    const [expandedStage, setExpandedStage] = useState<string | null>(null);

    const runId = createRunMutation.data?.run_id ?? null;

    const runQuery = useRun(projectId, runId);

    async function handleRunWorkflow() {
        try {
            const run = await createRunMutation.mutateAsync();

            onRunCreated?.(run.run_id);

            await executeRunMutation.mutateAsync(run.run_id);
        } catch {
            // Mutation errors are displayed below.
        }
    }

    const run = runQuery.data;

    const isRunning =
        createRunMutation.isPending ||
        executeRunMutation.isPending ||
        run?.status === "running";

    const canRun =
        !isRunning &&
        run?.status !== "completed" &&
        run?.status !== "escalated";

    return (
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-start justify-between gap-6">
                <div>
                    <h2 className="font-semibold text-slate-900">Workflow</h2>

                    <p className="mt-1 text-sm text-slate-500">
                        Process project documents through the intelligence
                        pipeline.
                    </p>
                </div>

                <button
                    type="button"
                    onClick={handleRunWorkflow}
                    disabled={!canRun}
                    className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
                >
                    {isRunning ? (
                        <>
                            <Loader2 size={16} className="animate-spin" />
                            Running...
                        </>
                    ) : (
                        <>
                            <Play size={16} />
                            Run workflow
                        </>
                    )}
                </button>
            </div>

            {/* Error */}
            {(createRunMutation.isError ||
                executeRunMutation.isError ||
                runQuery.isError) && (
                <div className="mt-6 rounded-lg border border-red-200 bg-red-50 p-4">
                    <div className="flex items-start gap-3">
                        <AlertCircle
                            size={18}
                            className="mt-0.5 shrink-0 text-red-600"
                        />

                        <div>
                            <p className="text-sm font-medium text-red-800">
                                Workflow failed to load
                            </p>

                            <p className="mt-1 text-sm text-red-600">
                                Please try again.
                            </p>
                        </div>
                    </div>
                </div>
            )}

            {/* Workflow hasn't started */}
            {!run && !createRunMutation.isError && (
                <div className="mt-6 rounded-xl border border-slate-200 bg-slate-50 p-8 text-center">
                    <Play size={28} className="mx-auto text-slate-400" />

                    <h3 className="mt-3 font-medium text-slate-900">
                        Workflow not started
                    </h3>

                    <p className="mt-1 text-sm text-slate-500">
                        Upload your documents and run the workflow when you're
                        ready.
                    </p>
                </div>
            )}

            {/* Workflow stages */}
            {run && (
                <div className="mt-6">
                    {run.usage && <UsageSummary usage={run.usage} />}

                    <div className="mt-6">
                        <div className="overflow-hidden rounded-xl border border-slate-200">
                            {run.stages.map((stage, index) => {
                                const isLast = index === run.stages.length - 1;

                                const hasUsage =
                                    (stage.total_tokens ?? 0) > 0 ||
                                    (stage.duration_ms ?? 0) > 0 ||
                                    (stage.estimated_cost_usd ?? 0) > 0;

                                const hasDetails =
                                    Boolean(stage.message) ||
                                    Boolean(
                                        stage.details &&
                                        Object.keys(stage.details).length > 0,
                                    ) ||
                                    Boolean(stage.error) ||
                                    Boolean(stage.started_at) ||
                                    Boolean(stage.completed_at) ||
                                    hasUsage;

                                const isExpanded =
                                    expandedStage === stage.stage;

                                return (
                                    <div
                                        key={stage.stage}
                                        className={
                                            !isLast
                                                ? "border-b border-slate-100"
                                                : ""
                                        }
                                    >
                                        {/* Stage header */}
                                        <button
                                            type="button"
                                            disabled={!hasDetails}
                                            onClick={() => {
                                                if (!hasDetails) {
                                                    return;
                                                }

                                                setExpandedStage(
                                                    isExpanded
                                                        ? null
                                                        : stage.stage,
                                                );
                                            }}
                                            className={`flex w-full items-center gap-4 px-5 py-4 text-left ${
                                                hasDetails
                                                    ? "cursor-pointer transition hover:bg-slate-50"
                                                    : "cursor-default"
                                            }`}
                                        >
                                            <StageIcon status={stage.status} />

                                            <div className="min-w-0 flex-1">
                                                <p className="text-sm font-medium text-slate-900">
                                                    {stageLabels[stage.stage]}
                                                </p>

                                                <p className="mt-0.5 text-xs capitalize text-slate-500">
                                                    {stage.status}

                                                    {stage.attempt > 0 &&
                                                        ` · Attempt ${stage.attempt}`}
                                                </p>
                                            </div>

                                            <span
                                                className={`text-xs font-medium ${
                                                    stage.status === "completed"
                                                        ? "text-emerald-600"
                                                        : stage.status ===
                                                            "running"
                                                          ? "text-blue-600"
                                                          : stage.status ===
                                                              "failed"
                                                            ? "text-red-600"
                                                            : stage.status ===
                                                                "escalated"
                                                              ? "text-amber-600"
                                                              : "text-slate-500"
                                                }`}
                                            >
                                                {formatStatus(stage.status)}
                                            </span>

                                            {hasDetails && (
                                                <ChevronDown
                                                    size={18}
                                                    className={`shrink-0 text-slate-400 transition-transform ${
                                                        isExpanded
                                                            ? "rotate-180"
                                                            : ""
                                                    }`}
                                                />
                                            )}
                                        </button>

                                        {/* Stage details */}
                                        {isExpanded && (
                                            <div className="border-t border-slate-100 bg-slate-50 px-5 py-5 pl-[68px]">
                                                {/* Message */}
                                                {stage.message && (
                                                    <div>
                                                        <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                                                            Result
                                                        </p>

                                                        <p className="mt-1 text-sm leading-6 text-slate-700">
                                                            {stage.message}
                                                        </p>
                                                    </div>
                                                )}

                                                {/* Details */}
                                                {stage.details &&
                                                    Object.keys(stage.details)
                                                        .length > 0 && (
                                                        <div className="mt-5">
                                                            <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                                                                Stage details
                                                            </p>

                                                            <div className="mt-3 space-y-3">
                                                                {Object.entries(
                                                                    stage.details,
                                                                ).map(
                                                                    ([
                                                                        key,
                                                                        value,
                                                                    ]) => (
                                                                        <div
                                                                            key={
                                                                                key
                                                                            }
                                                                            className="rounded-lg border border-slate-200 bg-white p-3"
                                                                        >
                                                                            <p className="text-xs font-medium text-slate-500">
                                                                                {formatDetailKey(
                                                                                    key,
                                                                                )}
                                                                            </p>

                                                                            {typeof value ===
                                                                                "string" ||
                                                                            typeof value ===
                                                                                "number" ||
                                                                            typeof value ===
                                                                                "boolean" ||
                                                                            value ===
                                                                                null ? (
                                                                                <p className="mt-1 text-sm text-slate-700">
                                                                                    {formatDetailValue(
                                                                                        value,
                                                                                    )}
                                                                                </p>
                                                                            ) : (
                                                                                <pre className="mt-2 overflow-x-auto whitespace-pre-wrap break-words rounded-md bg-slate-50 p-3 text-xs leading-5 text-slate-600">
                                                                                    {formatDetailValue(
                                                                                        value,
                                                                                    )}
                                                                                </pre>
                                                                            )}
                                                                        </div>
                                                                    ),
                                                                )}
                                                            </div>
                                                        </div>
                                                    )}

                                                {/* Error */}
                                                {stage.error && (
                                                    <div className="mt-5 rounded-lg border border-red-200 bg-red-50 p-4">
                                                        <p className="text-xs font-semibold uppercase tracking-wide text-red-600">
                                                            Error
                                                        </p>

                                                        <p className="mt-1 text-sm leading-6 text-red-700">
                                                            {stage.error}
                                                        </p>
                                                    </div>
                                                )}

                                                {hasUsage && (
                                                    <div className="mt-5">
                                                        <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                                                            Usage & cost
                                                        </p>

                                                        <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
                                                            <div className="rounded-lg border border-slate-200 bg-white p-3">
                                                                <p className="text-xs font-medium text-slate-500">
                                                                    Duration
                                                                </p>

                                                                <p className="mt-1 text-sm font-semibold text-slate-800">
                                                                    {stage.duration_ms !=
                                                                    null
                                                                        ? `${(stage.duration_ms / 1000).toFixed(2)}s`
                                                                        : "—"}
                                                                </p>
                                                            </div>

                                                            <div className="rounded-lg border border-slate-200 bg-white p-3">
                                                                <p className="text-xs font-medium text-slate-500">
                                                                    Input
                                                                </p>

                                                                <p className="mt-1 text-sm font-semibold text-slate-800">
                                                                    {(
                                                                        stage.input_tokens ??
                                                                        0
                                                                    ).toLocaleString()}
                                                                </p>
                                                            </div>

                                                            <div className="rounded-lg border border-slate-200 bg-white p-3">
                                                                <p className="text-xs font-medium text-slate-500">
                                                                    Output
                                                                </p>

                                                                <p className="mt-1 text-sm font-semibold text-slate-800">
                                                                    {(
                                                                        stage.output_tokens ??
                                                                        0
                                                                    ).toLocaleString()}
                                                                </p>
                                                            </div>

                                                            <div className="rounded-lg border border-slate-200 bg-white p-3">
                                                                <p className="text-xs font-medium text-slate-500">
                                                                    Cost
                                                                </p>

                                                                <p className="mt-1 text-sm font-semibold text-slate-800">
                                                                    {stage.estimated_cost_usd
                                                                        ? `$${stage.estimated_cost_usd.toFixed(6)}`
                                                                        : "$0.00"}
                                                                </p>
                                                            </div>
                                                        </div>
                                                    </div>
                                                )}

                                                {/* Timing */}
                                                {(stage.started_at ||
                                                    stage.completed_at) && (
                                                    <div className="mt-5 flex flex-wrap gap-x-6 gap-y-2 text-xs text-slate-400">
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
                            })}
                        </div>

                        {run.status === "completed" && (
                            <div className="mt-4 rounded-lg border border-emerald-200 bg-emerald-50 p-4">
                                <p className="text-sm font-medium text-emerald-800">
                                    Workflow completed successfully.
                                </p>
                            </div>
                        )}

                        {run.status === "escalated" && (
                            <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-4">
                                <p className="text-sm font-medium text-amber-800">
                                    Human review is required before the workflow
                                    can continue.
                                </p>
                            </div>
                        )}

                        {run.status === "failed" && (
                            <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-4">
                                <p className="text-sm font-medium text-red-800">
                                    The workflow failed. Please review the stage
                                    status and try again.
                                </p>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </section>
    );
}
