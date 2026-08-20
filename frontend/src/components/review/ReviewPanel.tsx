import { AlertCircle, Check, FileText, Loader2, X } from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { getReconciliation, resolveReconciliation } from "../../api/runs";

import { useReview, useReviewFinding } from "../../hooks/useReview";

interface ReviewPanelProps {
    projectId: string;
    runId: string;
}

function formatConflictDescription(description: string) {
    return description.replace(/Affected chunks:.*$/i, "").trim();
}

export default function ReviewPanel({ projectId, runId }: ReviewPanelProps) {
    const queryClient = useQueryClient();

    const reviewQuery = useReview(runId);

    const reviewMutation = useReviewFinding(runId);

    /*
     * Fetch reconciliation state.
     *
     * No polling.
     *
     * It will run once when this panel loads and will be
     * invalidated after a reconciliation is resolved.
     */
    const reconciliationQuery = useQuery({
        queryKey: ["reconciliation", projectId, runId],
        queryFn: () => getReconciliation(projectId, runId),
        enabled: Boolean(projectId && runId),
    });

    /*
     * Resolve one reconciliation conflict.
     */
    const resolveMutation = useMutation({
        mutationFn: (reconciliationId: string) =>
            resolveReconciliation(projectId, runId, reconciliationId),

        onSuccess: async () => {
            // Refresh reconciliation state.
            await queryClient.refetchQueries({
                queryKey: ["reconciliation", projectId, runId],
                type: "active",
            });

            // Immediately refresh workflow/run state.
            await queryClient.refetchQueries({
                queryKey: ["projects", projectId, "runs", runId],
                type: "active",
            });

            // Refresh review state.
            await queryClient.refetchQueries({
                queryKey: ["runs", runId, "review"],
                type: "active",
            });

            // Refresh project-level information.
            await queryClient.invalidateQueries({
                queryKey: ["projects"],
            });
        },
    });

    if (reviewQuery.isLoading) {
        return (
            <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <div className="flex items-center justify-center py-10">
                    <Loader2
                        size={22}
                        className="animate-spin text-slate-500"
                    />
                </div>
            </section>
        );
    }

    if (reviewQuery.isError) {
        return (
            <section className="rounded-2xl border border-red-200 bg-red-50 p-6">
                <div className="flex gap-3">
                    <AlertCircle size={20} className="shrink-0 text-red-600" />

                    <div>
                        <h2 className="font-semibold text-red-900">
                            Failed to load review
                        </h2>

                        <p className="mt-1 text-sm text-red-700">
                            Please try again.
                        </p>
                    </div>
                </div>
            </section>
        );
    }

    const findings = reviewQuery.data?.findings ?? [];

    const conflicts = reconciliationQuery.data?.conflicts ?? [];

    const openConflicts = conflicts.filter(
        (conflict) => conflict.status === "open",
    );

    const allReviewed =
        findings.length > 0 &&
        findings.every((finding) => finding.review_decision !== null);

    const isWorking = reviewMutation.isPending || resolveMutation.isPending;

    /*
     * Human review decision.
     */
    async function handleDecision(
        findingId: string,
        decision: "approve" | "reject",
    ) {
        try {
            /*
             * Save human decision.
             */
            await reviewMutation.mutateAsync({
                findingId,
                decision,
            });

            /*
             * Refresh persisted review state.
             */
            const latestReview = await reviewQuery.refetch();

            const latestFindings = latestReview.data?.findings ?? [];

            const everyFindingReviewed =
                latestFindings.length > 0 &&
                latestFindings.every(
                    (finding) => finding.review_decision !== null,
                );

            /*
             * Do NOT resume here.
             *
             * Reconciliation must also be checked.
             */
            if (!everyFindingReviewed) {
                return;
            }

            /*
             * Refresh reconciliation state.
             */
            await reconciliationQuery.refetch();
        } catch {
            // Mutation state is displayed below.
        }
    }

    /*
     * Resolve reconciliation conflict.
     */
    async function handleResolve(reconciliationId: string) {
        try {
            await resolveMutation.mutateAsync(reconciliationId);
        } catch {
            // Mutation state is displayed below.
        }
    }

    /*
     * Nothing to review.
     */
    if (findings.length === 0) {
        return (
            <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <div className="py-10 text-center">
                    <Check size={30} className="mx-auto text-emerald-500" />

                    <h2 className="mt-3 font-semibold text-slate-900">
                        No findings require review
                    </h2>

                    <p className="mt-1 text-sm text-slate-500">
                        There are currently no findings waiting for human
                        decisions.
                    </p>
                </div>
            </section>
        );
    }

    return (
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            {/* Header */}
            <div>
                <h2 className="font-semibold text-slate-900">
                    Review findings
                </h2>

                <p className="mt-1 text-sm text-slate-500">
                    Review the findings and approve or reject each one.
                </p>
            </div>

            {/* ------------------------------------------------ */}
            {/* Reconciliation */}
            {/* ------------------------------------------------ */}

            {allReviewed && reconciliationQuery.isLoading && (
                <div className="mt-5 flex items-center gap-3 rounded-xl border border-blue-200 bg-blue-50 px-4 py-3">
                    <Loader2 size={18} className="animate-spin text-blue-600" />

                    <div>
                        <p className="text-sm font-medium text-blue-900">
                            Checking reconciliation...
                        </p>

                        <p className="text-xs text-blue-700">
                            Checking whether any conflicts still need
                            resolution.
                        </p>
                    </div>
                </div>
            )}

            {allReviewed && reconciliationQuery.isError && (
                <div className="mt-5 flex items-center gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3">
                    <AlertCircle size={18} className="text-red-600" />

                    <div>
                        <p className="text-sm font-medium text-red-900">
                            Failed to load reconciliation
                        </p>

                        <p className="text-xs text-red-700">
                            Please refresh and try again.
                        </p>
                    </div>
                </div>
            )}

            {/* Open reconciliation conflicts */}

            {openConflicts.length > 0 && (
                <div className="mt-5 rounded-xl border border-amber-200 bg-amber-50 p-5">
                    <div className="flex items-start gap-3">
                        <AlertCircle
                            size={20}
                            className="mt-0.5 shrink-0 text-amber-600"
                        />

                        <div>
                            <h3 className="font-semibold text-amber-900">
                                Reconciliation required
                            </h3>

                            <p className="mt-1 text-sm text-amber-700">
                                Resolve all reconciliation conflicts before the
                                workflow can continue.
                            </p>
                        </div>
                    </div>

                    <div className="mt-4 space-y-3">
                        {openConflicts.map((conflict) => {
                            const resolving =
                                resolveMutation.isPending &&
                                resolveMutation.variables === conflict.id;

                            return (
                                <div
                                    key={conflict.id}
                                    className="rounded-lg border border-amber-200 bg-white p-4"
                                >
                                    <div className="flex items-start justify-between gap-4">
                                        <div>
                                            <span className="inline-flex rounded-full bg-amber-100 px-2.5 py-1 text-xs font-medium text-amber-700">
                                                {conflict.conflict_type.replaceAll(
                                                    "_",
                                                    " ",
                                                )}
                                            </span>

                                            <p className="mt-3 text-sm leading-6 text-slate-700">
                                                {formatConflictDescription(
                                                    conflict.description,
                                                )}
                                            </p>
                                        </div>

                                        <button
                                            type="button"
                                            disabled={resolveMutation.isPending}
                                            onClick={() =>
                                                handleResolve(conflict.id)
                                            }
                                            className="inline-flex shrink-0 items-center gap-2 rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
                                        >
                                            {resolving ? (
                                                <Loader2
                                                    size={16}
                                                    className="animate-spin"
                                                />
                                            ) : (
                                                <Check size={16} />
                                            )}

                                            {resolving
                                                ? "Resolving..."
                                                : "Resolve conflict"}
                                        </button>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* All conflicts resolved */}

            {allReviewed &&
                !reconciliationQuery.isLoading &&
                openConflicts.length === 0 && (
                    <div className="mt-5 flex items-center gap-3 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3">
                        <Check size={18} className="text-emerald-600" />

                        <div>
                            <p className="text-sm font-medium text-emerald-900">
                                Review and reconciliation completed
                            </p>

                            <p className="text-xs text-emerald-700">
                                All findings and conflicts have been resolved.
                                The workflow can continue.
                            </p>
                        </div>
                    </div>
                )}

            {/* Resolve error */}

            {resolveMutation.isError && (
                <div className="mt-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3">
                    <p className="text-sm font-medium text-red-800">
                        Failed to resolve reconciliation conflict.
                    </p>

                    <p className="mt-1 text-xs text-red-600">
                        Please try again.
                    </p>
                </div>
            )}

            {/* Review mutation error */}

            {reviewMutation.isError && (
                <div className="mt-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3">
                    <p className="text-sm font-medium text-red-800">
                        Failed to save review decision.
                    </p>

                    <p className="mt-1 text-xs text-red-600">
                        Please try again.
                    </p>
                </div>
            )}

            {/* ------------------------------------------------ */}
            {/* Findings */}
            {/* ------------------------------------------------ */}

            <div className="mt-6 space-y-4">
                {findings.map((finding) => {
                    const reviewed = finding.review_decision !== null;

                    const currentFinding =
                        reviewMutation.isPending &&
                        reviewMutation.variables?.findingId ===
                            finding.finding_id;

                    return (
                        <article
                            key={finding.finding_id}
                            className="rounded-xl border border-slate-200 p-5"
                        >
                            <div className="flex items-start justify-between gap-4">
                                <div>
                                    <h3 className="font-medium text-slate-900">
                                        {finding.title}
                                    </h3>

                                    <p className="mt-2 text-sm leading-6 text-slate-600">
                                        {finding.description}
                                    </p>
                                </div>

                                <span
                                    className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-medium ${
                                        reviewed
                                            ? finding.review_decision ===
                                              "approve"
                                                ? "bg-emerald-100 text-emerald-700"
                                                : "bg-red-100 text-red-700"
                                            : "bg-amber-100 text-amber-700"
                                    }`}
                                >
                                    {reviewed
                                        ? finding.review_decision
                                        : finding.status}
                                </span>
                            </div>

                            {finding.source && (
                                <div className="mt-5 rounded-lg bg-slate-50 p-4">
                                    <div className="flex items-start gap-3">
                                        <FileText
                                            size={18}
                                            className="mt-0.5 shrink-0 text-slate-500"
                                        />

                                        <div>
                                            <p className="text-sm font-medium text-slate-800">
                                                {finding.source.filename}
                                            </p>

                                            {(finding.source.start_page !==
                                                null ||
                                                finding.source.end_page !==
                                                    null) && (
                                                <p className="mt-1 text-xs text-slate-500">
                                                    Page{" "}
                                                    {finding.source
                                                        .start_page ??
                                                        finding.source.end_page}
                                                    {finding.source.end_page &&
                                                    finding.source.end_page !==
                                                        finding.source
                                                            .start_page
                                                        ? `–${finding.source.end_page}`
                                                        : ""}
                                                </p>
                                            )}
                                        </div>
                                    </div>

                                    <blockquote className="mt-4 border-l-2 border-slate-300 pl-4 text-sm leading-6 text-slate-600">
                                        {finding.source.quote}
                                    </blockquote>
                                </div>
                            )}

                            {!reviewed && (
                                <div className="mt-5 flex justify-end gap-3">
                                    <button
                                        type="button"
                                        disabled={isWorking}
                                        onClick={() =>
                                            handleDecision(
                                                finding.finding_id,
                                                "reject",
                                            )
                                        }
                                        className="inline-flex items-center gap-2 rounded-lg border border-slate-300 px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
                                    >
                                        {currentFinding &&
                                        reviewMutation.variables?.decision ===
                                            "reject" ? (
                                            <Loader2
                                                size={16}
                                                className="animate-spin"
                                            />
                                        ) : (
                                            <X size={16} />
                                        )}
                                        Reject
                                    </button>

                                    <button
                                        type="button"
                                        disabled={isWorking}
                                        onClick={() =>
                                            handleDecision(
                                                finding.finding_id,
                                                "approve",
                                            )
                                        }
                                        className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
                                    >
                                        {currentFinding &&
                                        reviewMutation.variables?.decision ===
                                            "approve" ? (
                                            <Loader2
                                                size={16}
                                                className="animate-spin"
                                            />
                                        ) : (
                                            <Check size={16} />
                                        )}
                                        Approve
                                    </button>
                                </div>
                            )}
                        </article>
                    );
                })}
            </div>

            {/* Waiting for review */}

            {!allReviewed && (
                <div className="mt-5 rounded-lg bg-amber-50 px-4 py-3">
                    <p className="text-sm text-amber-800">
                        All findings must be approved or rejected before the
                        workflow can continue.
                    </p>
                </div>
            )}
        </section>
    );
}
