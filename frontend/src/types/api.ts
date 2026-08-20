export interface Project {
    id: string;
    name: string;
    description: string | null;
    created_at: string;
    updated_at: string;
}

export interface CreateProjectRequest {
    name: string;
    description?: string | null;
}

export interface UpdateProjectRequest {
    name?: string;
    description?: string | null;
}

export interface DocumentUploadResponse {
    id: string;
    filename: string;
    mime_type: string | null;
    content_hash: string;
    blocks: number;
}

export type StageStatus =
    | "pending"
    | "running"
    | "completed"
    | "failed"
    | "skipped"
    | "escalated";

export type StageName =
    | "ingest"
    | "extract"
    | "analyze"
    | "reconcile"
    | "review"
    | "commit";

export interface StageRun {
    stage: StageName;
    status: StageStatus;
    attempt: number;
    message?: string | null;
    details?: Record<string, unknown>;
    started_at?: string | null;
    completed_at?: string | null;
    error?: string | null;
}

export interface Run {
    run_id: string;
    project_id: string;
    status: string;
    current_stage: StageName;
    stages: StageRun[];
}

export interface CreateRunResponse {
    run_id: string;
    project_id: string;
    status: string;
    current_stage: StageName;
}

export interface ExecuteRunResponse {
    run_id: string;
    decision: string;
    message: string;
    data: Record<string, unknown>;
}

export interface RunHistoryItem {
    run_id: string;
    status: string;
    current_stage: string;
    created_at: string;
}

export interface RunHistoryResponse {
    project_id: string;
    runs: RunHistoryItem[];
}

export interface FindingSource {
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
    review_decision: "approve" | "reject" | null;
    source: FindingSource | null;
}

export interface ReviewResponse {
    run_id: string;
    status: string;
    findings: Finding[];
}

export interface Document {
    id: string;
    filename: string;
    mime_type: string | null;
    content_hash: string;
    document_type: string | null;
    created_at: string;
}

export interface DocumentsResponse {
    documents: Document[];
}

export interface ReconciliationConflict {
    id: string;
    conflict_type: string;
    status: string;
    description: string;
}

export interface ReconciliationResponse {
    run_id: string;
    conflicts: ReconciliationConflict[];
}
