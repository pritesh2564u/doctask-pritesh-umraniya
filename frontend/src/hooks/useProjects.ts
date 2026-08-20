import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { createProject, getProjects } from "../api/projects";
import type { CreateProjectRequest } from "../types/api";

export function useProjects() {
    return useQuery({
        queryKey: ["projects"],
        queryFn: getProjects,
    });
}

export function useCreateProject() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: CreateProjectRequest) => createProject(data),

        onSuccess: () => {
            queryClient.invalidateQueries({
                queryKey: ["projects"],
            });
        },
    });
}
