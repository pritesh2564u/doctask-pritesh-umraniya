import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { getDocuments, uploadDocument, deleteDocument } from "../api/documents";

export function useDocuments(projectId: string) {
    return useQuery({
        queryKey: ["projects", projectId, "documents"],
        queryFn: () => getDocuments(projectId),
        enabled: Boolean(projectId),
    });
}

export function useUploadDocument(projectId: string) {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (file: File) => uploadDocument(projectId, file),

        onSuccess: () => {
            queryClient.invalidateQueries({
                queryKey: ["projects", projectId, "documents"],
            });
        },
    });
}

export function useDeleteDocument(projectId: string) {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (documentId: string) =>
            deleteDocument(projectId, documentId),

        onSuccess: async () => {
            await queryClient.invalidateQueries({
                queryKey: ["projects", projectId, "documents"],
            });

            await queryClient.invalidateQueries({
                queryKey: ["projects", projectId],
            });
        },
    });
}
