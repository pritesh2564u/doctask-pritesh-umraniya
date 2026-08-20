import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { deleteProject, getProject, updateProject } from "../api/projects";

export function useProject(projectId: string) {
    return useQuery({
        queryKey: ["projects", projectId],
        queryFn: () => getProject(projectId),
        enabled: Boolean(projectId),
    });
}

export function useUpdateProject(projectId: string) {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: { name: string; description: string | null }) =>
            updateProject(projectId, data),

        onSuccess: async () => {
            await queryClient.invalidateQueries({
                queryKey: ["projects", projectId],
            });

            await queryClient.invalidateQueries({
                queryKey: ["projects"],
            });
        },
    });
}

export function useDeleteProject() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (projectId: string) => deleteProject(projectId),

        onSuccess: async (_, projectId) => {
            await queryClient.invalidateQueries({
                queryKey: ["projects"],
            });

            queryClient.removeQueries({
                queryKey: ["projects", projectId],
            });
        },
    });
}
