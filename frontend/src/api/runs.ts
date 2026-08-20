import { api } from "./client";
import type {
    CreateRunResponse,
    ExecuteRunResponse,
    ReconciliationResponse,
    Run,
    RunHistoryResponse,
} from "../types/api";

export async function createRun(projectId: string): Promise<CreateRunResponse> {
    const response = await api.post<CreateRunResponse>(
        `/projects/${projectId}/runs`,
    );

    return response.data;
}

export async function executeRun(
    projectId: string,
    runId: string,
): Promise<ExecuteRunResponse> {
    const response = await api.post<ExecuteRunResponse>(
        `/projects/${projectId}/runs/${runId}/execute`,
    );

    return response.data;
}

export async function getProjectRuns(
    projectId: string,
): Promise<RunHistoryResponse> {
    const response = await api.get<RunHistoryResponse>(
        `/projects/${projectId}/runs`,
    );

    return response.data;
}

export async function getRun(projectId: string, runId: string): Promise<Run> {
    const response = await api.get<Run>(`/projects/${projectId}/runs/${runId}`);

    return response.data;
}

export async function getReconciliation(
    projectId: string,
    runId: string,
): Promise<ReconciliationResponse> {
    const response = await api.get(
        `/projects/${projectId}/runs/${runId}/reconciliation`,
    );

    return response.data;
}

export async function resolveReconciliation(
    projectId: string,
    runId: string,
    reconciliationId: string,
) {
    const response = await api.post(
        `/projects/${projectId}/runs/${runId}/reconciliation/${reconciliationId}/resolve`,
    );

    return response.data;
}
