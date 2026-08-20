import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { getReview, reviewFinding, resumeWorkflow } from "../api/reviews";

export function useReview(runId: string | null) {
    return useQuery({
        queryKey: ["runs", runId, "review"],
        queryFn: () => getReview(runId!),
        enabled: Boolean(runId),

        /*
         * Refresh the review endpoint while the run is active.
         *
         * This allows findings to appear automatically when
         * the backend reaches the review stage.
         */
        refetchInterval: 2000,
    });
}

export function useReviewFinding(runId: string) {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({
            findingId,
            decision,
        }: {
            findingId: string;
            decision: "approve" | "reject";
        }) => reviewFinding(runId, findingId, decision),

        onSuccess: async () => {
            await queryClient.invalidateQueries({
                queryKey: ["runs", runId, "review"],
            });

            await queryClient.invalidateQueries({
                queryKey: ["projects"],
            });
        },
    });
}

export function useResumeWorkflow(projectId: string, runId: string) {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: () => resumeWorkflow(projectId, runId),

        onSuccess: async () => {
            await queryClient.invalidateQueries({
                queryKey: ["runs", runId, "review"],
            });

            await queryClient.invalidateQueries({
                queryKey: ["projects", projectId, "runs", runId],
            });

            await queryClient.invalidateQueries({
                queryKey: ["projects"],
            });
        },
    });
}
