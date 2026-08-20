import { api } from "./client";

export interface ReviewSource {
    document_id: string;
    filename: string;
    chunk_id: string;
    start_page: number | null;
    end_page: number | null;
    start_paragraph: number | null;
    end_paragraph: number | null;
    start_line: number | null;
    end_line: number | null;
    quote: string;
}

export interface Finding {
    finding_id: string;
    title: string;
    description: string;
    status: string;
    review_decision: string | null;
    source: ReviewSource | null;
}

export interface ReviewResponse {
    run_id: string;
    status: string;
    findings: Finding[];
}

export interface ReviewDecisionResponse {
    finding_id: string;
    decision: string;
    status: string;
    message: string;
}

export async function getReview(runId: string): Promise<ReviewResponse> {
    const response = await api.get<ReviewResponse>(`/runs/${runId}/review`);

    return response.data;
}

export async function reviewFinding(
    runId: string,
    findingId: string,
    decision: "approve" | "reject",
): Promise<ReviewDecisionResponse> {
    const response = await api.post<ReviewDecisionResponse>(
        `/runs/${runId}/review/${findingId}`,
        {
            decision,
        },
    );

    return response.data;
}

export async function resumeWorkflow(projectId: string, runId: string) {
    const response = await api.post(
        `/projects/${projectId}/runs/${runId}/execute`,
    );

    return response.data;
}
