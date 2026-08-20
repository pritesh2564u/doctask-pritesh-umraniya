import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { createRun, executeRun, getRun, getProjectRuns } from "../api/runs";

export function useCreateRun(projectId: string) {
    return useMutation({
        mutationFn: () => createRun(projectId),
    });
}

export function useExecuteRun(projectId: string) {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (runId: string) => executeRun(projectId, runId),

        onSuccess: (_, runId) => {
            queryClient.invalidateQueries({
                queryKey: ["projects", projectId, "runs", runId],
            });
        },
    });
}

export function useRun(projectId: string, runId: string | null) {
    return useQuery({
        queryKey: ["projects", projectId, "runs", runId],

        queryFn: () => getRun(projectId, runId!),

        enabled: Boolean(projectId && runId),

        refetchInterval: (query) => {
            const data = query.state.data;

            if (!data) {
                return 2000;
            }

            /*
             * Keep polling while waiting for human review.
             */
            if (
                data.status === "escalated" &&
                data.current_stage === "review"
            ) {
                return 2000;
            }

            /*
             * Stop only at terminal states.
             */
            if (data.status === "completed" || data.status === "failed") {
                return false;
            }

            return 2000;
        },
    });
}

export function useProjectRuns(projectId: string) {
    return useQuery({
        queryKey: ["projects", projectId, "runs"],
        queryFn: () => getProjectRuns(projectId),
        enabled: Boolean(projectId),
    });
}
