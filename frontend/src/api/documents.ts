import { api } from "./client";
import type { DocumentUploadResponse, DocumentsResponse } from "../types/api";

export async function getDocuments(
    projectId: string,
): Promise<DocumentsResponse> {
    const response = await api.get<DocumentsResponse>(
        `/projects/${projectId}/documents`,
    );

    return response.data;
}

export async function uploadDocument(
    projectId: string,
    file: File,
): Promise<DocumentUploadResponse> {
    const formData = new FormData();

    formData.append("file", file);

    const response = await api.post<DocumentUploadResponse>(
        `/projects/${projectId}/documents`,
        formData,
    );

    return response.data;
}

export async function deleteDocument(projectId: string, documentId: string) {
    await api.delete(`/projects/${projectId}/documents/${documentId}`);
}
