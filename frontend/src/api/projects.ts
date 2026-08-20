import { api } from "./client";
import type {
    CreateProjectRequest,
    Project,
    UpdateProjectRequest,
} from "../types/api";

export async function getProjects(): Promise<Project[]> {
    const response = await api.get<Project[]>("/projects");

    return response.data;
}

export async function getProject(projectId: string): Promise<Project> {
    const response = await api.get<Project>(`/projects/${projectId}`);

    return response.data;
}

export async function createProject(
    data: CreateProjectRequest,
): Promise<Project> {
    const response = await api.post<Project>("/projects", data);

    return response.data;
}

export async function updateProject(
    projectId: string,
    data: UpdateProjectRequest,
) {
    const response = await api.patch<Project>(`/projects/${projectId}`, data);

    return response.data;
}

export async function deleteProject(projectId: string) {
    await api.delete(`/projects/${projectId}`);
}
