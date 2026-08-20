import {
    Edit3,
    FileText,
    Loader2,
    Save,
    Trash2,
    Upload,
    X,
    History,
    ChevronRight,
} from "lucide-react";

import { useRef, useState, type ChangeEvent } from "react";

import { Link, useNavigate, useParams } from "react-router-dom";

import WorkflowPanel from "../components/workflow/WorkflowPanel";
import ReviewPanel from "../components/review/ReviewPanel";

import {
    useDeleteDocument,
    useDocuments,
    useUploadDocument,
} from "../hooks/useDocuments";

import {
    useDeleteProject,
    useUpdateProject,
    useProject,
} from "../hooks/useProject";

import { useProjectRuns } from "../hooks/useRun";

export default function Project() {
    const navigate = useNavigate();

    const [activeRunId, setActiveRunId] = useState<string | null>(null);

    const { projectId } = useParams<{
        projectId: string;
    }>();

    const fileInputRef = useRef<HTMLInputElement>(null);

    const [selectedFileName, setSelectedFileName] = useState<string | null>(
        null,
    );

    // --------------------------------------------------
    // Edit project state
    // --------------------------------------------------

    const [isEditOpen, setIsEditOpen] = useState(false);

    const [editName, setEditName] = useState("");

    const [editDescription, setEditDescription] = useState("");

    // --------------------------------------------------
    // Delete project state
    // --------------------------------------------------

    const [isDeleteProjectOpen, setIsDeleteProjectOpen] = useState(false);

    // --------------------------------------------------
    // Delete document state
    // --------------------------------------------------

    const [documentToDelete, setDocumentToDelete] = useState<{
        id: string;
        filename: string;
    } | null>(null);

    // --------------------------------------------------
    // Queries / mutations
    // --------------------------------------------------

    const projectQuery = useProject(projectId ?? "");

    const documentsQuery = useDocuments(projectId ?? "");

    const runsQuery = useProjectRuns(projectId ?? "");

    const uploadMutation = useUploadDocument(projectId ?? "");

    const deleteDocumentMutation = useDeleteDocument(projectId ?? "");

    const updateProjectMutation = useUpdateProject(projectId ?? "");

    const deleteProjectMutation = useDeleteProject();

    // --------------------------------------------------
    // Invalid project
    // --------------------------------------------------

    if (!projectId) {
        return (
            <main className="min-h-screen bg-slate-50">
                <div className="mx-auto max-w-7xl px-6 py-10">
                    <div className="rounded-xl border border-red-200 bg-red-50 p-6">
                        <h1 className="font-semibold text-red-900">
                            Invalid project
                        </h1>

                        <p className="mt-1 text-sm text-red-700">
                            No project ID was provided.
                        </p>
                    </div>
                </div>
            </main>
        );
    }

    // --------------------------------------------------
    // Loading
    // --------------------------------------------------

    if (projectQuery.isLoading) {
        return (
            <main className="flex min-h-screen items-center justify-center bg-slate-50">
                <Loader2 size={24} className="animate-spin text-slate-500" />
            </main>
        );
    }

    // --------------------------------------------------
    // Project error
    // --------------------------------------------------

    if (projectQuery.isError || !projectQuery.data) {
        return (
            <main className="min-h-screen bg-slate-50">
                <div className="mx-auto max-w-7xl px-6 py-10">
                    <Link
                        to="/projects"
                        className="text-sm font-medium text-slate-500 transition hover:text-slate-900"
                    >
                        Back to projects
                    </Link>

                    <div className="mt-8 rounded-xl border border-red-200 bg-red-50 p-6">
                        <h1 className="font-semibold text-red-900">
                            Project not found
                        </h1>

                        <p className="mt-1 text-sm text-red-700">
                            We couldn't load this project.
                        </p>
                    </div>
                </div>
            </main>
        );
    }

    const project = projectQuery.data;

    const documentCount = documentsQuery.data?.documents.length ?? 0;

    const runs = runsQuery.data?.runs ?? [];

    // --------------------------------------------------
    // File upload
    // --------------------------------------------------

    function openFilePicker() {
        fileInputRef.current?.click();
    }

    function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
        const file = event.target.files?.[0];

        if (!file) {
            return;
        }

        setSelectedFileName(file.name);

        uploadMutation.mutate(file, {
            onSuccess: () => {
                setSelectedFileName(null);

                if (fileInputRef.current) {
                    fileInputRef.current.value = "";
                }
            },
        });
    }

    // --------------------------------------------------
    // Open edit modal
    // --------------------------------------------------

    function openEditProject() {
        setEditName(project.name);
        setEditDescription(project.description ?? "");

        setIsEditOpen(true);
    }

    // --------------------------------------------------
    // Update project
    // --------------------------------------------------

    async function handleUpdateProject() {
        const name = editName.trim();

        if (!name) {
            return;
        }

        await updateProjectMutation.mutateAsync({
            name,
            description: editDescription.trim() || null,
        });

        setIsEditOpen(false);
    }

    // --------------------------------------------------
    // Delete project
    // --------------------------------------------------

    async function handleDeleteProject() {
        await deleteProjectMutation.mutateAsync(projectId ?? "");

        setIsDeleteProjectOpen(false);

        navigate("/projects");
    }

    // --------------------------------------------------
    // Delete document
    // --------------------------------------------------

    async function handleDeleteDocument() {
        if (!documentToDelete) {
            return;
        }

        await deleteDocumentMutation.mutateAsync(documentToDelete.id);

        setDocumentToDelete(null);
    }

    // --------------------------------------------------
    // Run status styling
    // --------------------------------------------------

    function getRunStatusClasses(status: string) {
        switch (status.toLowerCase()) {
            case "completed":
                return "bg-emerald-100 text-emerald-700";

            case "failed":
                return "bg-red-100 text-red-700";

            case "escalated":
                return "bg-amber-100 text-amber-700";

            case "running":
                return "bg-blue-100 text-blue-700";

            case "pending":
                return "bg-slate-100 text-slate-600";

            default:
                return "bg-slate-100 text-slate-600";
        }
    }

    function formatRunStatus(status: string) {
        return status
            .replace(/_/g, " ")
            .replace(/\b\w/g, (character) => character.toUpperCase());
    }

    function formatStage(stage: string) {
        return stage
            .replace(/_/g, " ")
            .replace(/\b\w/g, (character) => character.toUpperCase());
    }

    function formatRunDate(date: string) {
        return new Date(date).toLocaleString();
    }

    // --------------------------------------------------
    // Select historical run
    // --------------------------------------------------

    function handleSelectRun(runId: string) {
        setActiveRunId(runId);

        window.setTimeout(() => {
            document.getElementById("run-details")?.scrollIntoView({
                behavior: "smooth",
                block: "start",
            });
        }, 50);
    }

    return (
        <main className="min-h-screen bg-slate-50">
            <div className="mx-auto max-w-7xl px-6 py-10">
                {/* ======================================
                    Back navigation
                ======================================= */}

                <Link
                    to="/projects"
                    className="inline-flex text-sm font-medium text-slate-500 transition hover:text-slate-900"
                >
                    Back to projects
                </Link>

                {/* ======================================
                    Project header
                ======================================= */}

                <div className="mt-8 flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
                    <div className="min-w-0">
                        <h1 className="text-3xl font-bold tracking-tight text-slate-900">
                            {project.name}
                        </h1>

                        <p className="mt-2 max-w-3xl text-slate-500">
                            {project.description ||
                                "No project description provided."}
                        </p>
                    </div>

                    {/* Project actions */}

                    <div className="flex shrink-0 items-center gap-2">
                        <button
                            type="button"
                            onClick={openEditProject}
                            className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50"
                        >
                            <Edit3 size={16} />
                            Edit
                        </button>

                        <button
                            type="button"
                            onClick={() => setIsDeleteProjectOpen(true)}
                            className="inline-flex items-center gap-2 rounded-lg border border-red-200 bg-white px-4 py-2.5 text-sm font-medium text-red-600 shadow-sm transition hover:bg-red-50"
                        >
                            <Trash2 size={16} />
                            Delete
                        </button>
                    </div>
                </div>

                {/* ======================================
                    Project content
                ======================================= */}

                <div className="mt-10">
                    {/* ==================================
                        Documents
                    =================================== */}

                    <section>
                        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                            {/* Header */}

                            <div className="flex items-center justify-between gap-4">
                                <div className="flex items-center gap-3">
                                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-100">
                                        <FileText
                                            size={20}
                                            className="text-slate-700"
                                        />
                                    </div>

                                    <div>
                                        <h2 className="font-semibold text-slate-900">
                                            Documents
                                        </h2>

                                        <p className="text-sm text-slate-500">
                                            {documentCount}{" "}
                                            {documentCount === 1
                                                ? "document"
                                                : "documents"}
                                        </p>
                                    </div>
                                </div>

                                {/* Upload */}

                                <button
                                    type="button"
                                    onClick={openFilePicker}
                                    disabled={uploadMutation.isPending}
                                    className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
                                >
                                    {uploadMutation.isPending ? (
                                        <>
                                            <Loader2
                                                size={16}
                                                className="animate-spin"
                                            />
                                            Uploading...
                                        </>
                                    ) : (
                                        <>
                                            <Upload size={16} />
                                            Upload
                                        </>
                                    )}
                                </button>
                            </div>

                            {/* Hidden file input */}

                            <input
                                ref={fileInputRef}
                                type="file"
                                className="hidden"
                                onChange={handleFileChange}
                            />

                            {/* Loading */}

                            {documentsQuery.isLoading && (
                                <div className="mt-6 flex items-center justify-center rounded-xl border border-slate-200 bg-slate-50 py-12">
                                    <Loader2
                                        size={22}
                                        className="animate-spin text-slate-500"
                                    />
                                </div>
                            )}

                            {/* Error */}

                            {documentsQuery.isError && (
                                <div className="mt-6 rounded-xl border border-red-200 bg-red-50 p-4">
                                    <p className="text-sm font-medium text-red-800">
                                        Failed to load documents.
                                    </p>

                                    <p className="mt-1 text-sm text-red-600">
                                        Please refresh the page and try again.
                                    </p>
                                </div>
                            )}

                            {/* Empty */}

                            {!documentsQuery.isLoading &&
                                !documentsQuery.isError &&
                                documentCount === 0 && (
                                    <div className="mt-6 rounded-xl border-2 border-dashed border-slate-200 bg-slate-50 px-6 py-12 text-center">
                                        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-white shadow-sm">
                                            <FileText
                                                size={24}
                                                className="text-slate-400"
                                            />
                                        </div>

                                        <h3 className="mt-4 font-medium text-slate-900">
                                            No documents yet
                                        </h3>

                                        <p className="mx-auto mt-1 max-w-sm text-sm text-slate-500">
                                            Upload documents to start analyzing
                                            this project.
                                        </p>

                                        <button
                                            type="button"
                                            onClick={openFilePicker}
                                            disabled={uploadMutation.isPending}
                                            className="mt-5 inline-flex items-center gap-2 rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
                                        >
                                            <Upload size={16} />
                                            Upload document
                                        </button>
                                    </div>
                                )}

                            {/* Document list */}

                            {!documentsQuery.isLoading &&
                                !documentsQuery.isError &&
                                documentCount > 0 && (
                                    <div className="mt-6 overflow-hidden rounded-xl border border-slate-200">
                                        {documentsQuery.data?.documents.map(
                                            (document) => (
                                                <div
                                                    key={document.id}
                                                    className="flex items-center gap-4 border-b border-slate-100 p-4 last:border-b-0"
                                                >
                                                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-slate-100">
                                                        <FileText
                                                            size={19}
                                                            className="text-slate-600"
                                                        />
                                                    </div>

                                                    <div className="min-w-0 flex-1">
                                                        <p className="truncate text-sm font-medium text-slate-900">
                                                            {document.filename}
                                                        </p>

                                                        <p className="mt-1 text-xs text-slate-500">
                                                            {document.mime_type ||
                                                                "Unknown type"}
                                                            {" · "}
                                                            {new Date(
                                                                document.created_at,
                                                            ).toLocaleDateString()}
                                                        </p>
                                                    </div>

                                                    {/* Remove document */}

                                                    <button
                                                        type="button"
                                                        onClick={() =>
                                                            setDocumentToDelete(
                                                                {
                                                                    id: document.id,
                                                                    filename:
                                                                        document.filename,
                                                                },
                                                            )
                                                        }
                                                        disabled={
                                                            deleteDocumentMutation.isPending
                                                        }
                                                        title="Remove document"
                                                        aria-label={`Remove ${document.filename}`}
                                                        className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-slate-400 transition hover:bg-red-50 hover:text-red-600 disabled:cursor-not-allowed disabled:opacity-50"
                                                    >
                                                        {deleteDocumentMutation.isPending &&
                                                        documentToDelete?.id ===
                                                            document.id ? (
                                                            <Loader2
                                                                size={16}
                                                                className="animate-spin"
                                                            />
                                                        ) : (
                                                            <Trash2 size={16} />
                                                        )}
                                                    </button>
                                                </div>
                                            ),
                                        )}
                                    </div>
                                )}

                            {/* Selected file */}

                            {selectedFileName && !uploadMutation.isPending && (
                                <div className="mt-4 rounded-lg bg-slate-50 px-4 py-3">
                                    <p className="text-sm text-slate-600">
                                        Selected:{" "}
                                        <span className="font-medium text-slate-900">
                                            {selectedFileName}
                                        </span>
                                    </p>
                                </div>
                            )}

                            {/* Upload error */}

                            {uploadMutation.isError && (
                                <div className="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3">
                                    <p className="text-sm font-medium text-red-800">
                                        Upload failed.
                                    </p>

                                    <p className="mt-1 text-sm text-red-600">
                                        {uploadMutation.error instanceof Error
                                            ? uploadMutation.error.message
                                            : "Something went wrong while uploading the document."}
                                    </p>
                                </div>
                            )}

                            {/* Upload success */}

                            {uploadMutation.isSuccess && (
                                <div className="mt-4 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3">
                                    <p className="text-sm font-medium text-emerald-800">
                                        Document uploaded successfully.
                                    </p>
                                </div>
                            )}
                        </div>
                    </section>

                    {/* ==================================
                        Workflow
                    =================================== */}

                    <section className="mt-6">
                        <WorkflowPanel
                            projectId={projectId}
                            onRunCreated={setActiveRunId}
                        />
                    </section>

                    {/* ==================================
                        Run History
                    =================================== */}

                    <section className="mt-6">
                        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                            <div className="flex items-center justify-between gap-4">
                                <div className="flex items-center gap-3">
                                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-100">
                                        <History
                                            size={20}
                                            className="text-slate-700"
                                        />
                                    </div>

                                    <div>
                                        <h2 className="font-semibold text-slate-900">
                                            Run History
                                        </h2>

                                        <p className="text-sm text-slate-500">
                                            Previous workflow executions
                                        </p>
                                    </div>
                                </div>

                                {runs.length > 0 && (
                                    <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
                                        {runs.length}{" "}
                                        {runs.length === 1 ? "run" : "runs"}
                                    </span>
                                )}
                            </div>

                            {/* Loading */}

                            {runsQuery.isLoading && (
                                <div className="mt-6 flex items-center justify-center rounded-xl border border-slate-200 bg-slate-50 py-10">
                                    <div className="flex items-center gap-3 text-sm text-slate-500">
                                        <Loader2
                                            size={20}
                                            className="animate-spin"
                                        />
                                        Loading run history...
                                    </div>
                                </div>
                            )}

                            {/* Error */}

                            {runsQuery.isError && (
                                <div className="mt-6 rounded-xl border border-red-200 bg-red-50 p-4">
                                    <p className="text-sm font-medium text-red-800">
                                        Failed to load run history.
                                    </p>

                                    <p className="mt-1 text-sm text-red-600">
                                        Please refresh the page and try again.
                                    </p>
                                </div>
                            )}

                            {/* Empty */}

                            {!runsQuery.isLoading &&
                                !runsQuery.isError &&
                                runs.length === 0 && (
                                    <div className="mt-6 rounded-xl border-2 border-dashed border-slate-200 bg-slate-50 px-6 py-10 text-center">
                                        <div className="mx-auto flex h-11 w-11 items-center justify-center rounded-full bg-white shadow-sm">
                                            <History
                                                size={21}
                                                className="text-slate-400"
                                            />
                                        </div>

                                        <h3 className="mt-3 font-medium text-slate-900">
                                            No workflow runs yet
                                        </h3>

                                        <p className="mx-auto mt-1 max-w-sm text-sm text-slate-500">
                                            Start a workflow to see its
                                            execution history here.
                                        </p>
                                    </div>
                                )}

                            {/* Run list */}

                            {!runsQuery.isLoading &&
                                !runsQuery.isError &&
                                runs.length > 0 && (
                                    <div className="mt-6 overflow-hidden rounded-xl border border-slate-200">
                                        {runs.map((run) => (
                                            <div
                                                key={run.run_id}
                                                className="flex flex-col gap-4 border-b border-slate-100 p-5 last:border-b-0 sm:flex-row sm:items-center sm:justify-between"
                                            >
                                                <div className="min-w-0">
                                                    <div className="flex flex-wrap items-center gap-3">
                                                        <p className="text-sm font-semibold text-slate-900">
                                                            Workflow Run
                                                        </p>

                                                        <span
                                                            className={`rounded-full px-2.5 py-1 text-xs font-medium ${getRunStatusClasses(
                                                                run.status,
                                                            )}`}
                                                        >
                                                            {formatRunStatus(
                                                                run.status,
                                                            )}
                                                        </span>
                                                    </div>

                                                    <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500">
                                                        <span>
                                                            Stage:{" "}
                                                            <span className="font-medium text-slate-700">
                                                                {formatStage(
                                                                    run.current_stage,
                                                                )}
                                                            </span>
                                                        </span>

                                                        <span>
                                                            {formatRunDate(
                                                                run.created_at,
                                                            )}
                                                        </span>
                                                    </div>
                                                </div>

                                                <button
                                                    type="button"
                                                    onClick={() =>
                                                        handleSelectRun(
                                                            run.run_id,
                                                        )
                                                    }
                                                    className="inline-flex shrink-0 items-center justify-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
                                                >
                                                    View details
                                                    <ChevronRight size={16} />
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                )}
                        </div>
                    </section>

                    {/* ==================================
                        Review / Run Details
                    =================================== */}

                    {activeRunId && (
                        <section id="run-details" className="mt-6 scroll-mt-6">
                            <ReviewPanel
                                projectId={projectId}
                                runId={activeRunId}
                            />
                        </section>
                    )}

                    {/* ==================================
                        Project information
                    =================================== */}

                    <section className="mt-6">
                        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                            <h2 className="font-semibold text-slate-900">
                                Project information
                            </h2>

                            <div className="mt-5 grid gap-5 sm:grid-cols-3">
                                <div>
                                    <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                                        Created
                                    </p>

                                    <p className="mt-1 text-sm text-slate-700">
                                        {new Date(
                                            project.created_at,
                                        ).toLocaleDateString()}
                                    </p>
                                </div>

                                <div>
                                    <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                                        Last updated
                                    </p>

                                    <p className="mt-1 text-sm text-slate-700">
                                        {new Date(
                                            project.updated_at,
                                        ).toLocaleDateString()}
                                    </p>
                                </div>

                                <div>
                                    <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                                        Documents
                                    </p>

                                    <p className="mt-1 text-sm font-medium text-slate-900">
                                        {documentCount}
                                    </p>
                                </div>
                            </div>
                        </div>
                    </section>
                </div>
            </div>

            {/* ==========================================
                EDIT PROJECT MODAL
            =========================================== */}

            {isEditOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 px-4">
                    <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl">
                        <div className="flex items-start justify-between">
                            <div>
                                <h2 className="text-lg font-semibold text-slate-900">
                                    Edit project
                                </h2>

                                <p className="mt-1 text-sm text-slate-500">
                                    Update your project information.
                                </p>
                            </div>

                            <button
                                type="button"
                                onClick={() => setIsEditOpen(false)}
                                disabled={updateProjectMutation.isPending}
                                className="rounded-lg p-2 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
                            >
                                <X size={18} />
                            </button>
                        </div>

                        <div className="mt-6 space-y-5">
                            <div>
                                <label className="text-sm font-medium text-slate-700">
                                    Project name
                                </label>

                                <input
                                    value={editName}
                                    onChange={(event) =>
                                        setEditName(event.target.value)
                                    }
                                    className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2.5 text-sm outline-none transition focus:border-slate-400 focus:ring-2 focus:ring-slate-100"
                                    placeholder="Project name"
                                />
                            </div>

                            <div>
                                <label className="text-sm font-medium text-slate-700">
                                    Description
                                </label>

                                <textarea
                                    value={editDescription}
                                    onChange={(event) =>
                                        setEditDescription(event.target.value)
                                    }
                                    rows={4}
                                    className="mt-2 w-full resize-none rounded-lg border border-slate-200 px-3 py-2.5 text-sm outline-none transition focus:border-slate-400 focus:ring-2 focus:ring-slate-100"
                                    placeholder="Project description"
                                />
                            </div>
                        </div>

                        {updateProjectMutation.isError && (
                            <div className="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3">
                                <p className="text-sm text-red-700">
                                    {updateProjectMutation.error instanceof
                                    Error
                                        ? updateProjectMutation.error.message
                                        : "Failed to update project."}
                                </p>
                            </div>
                        )}

                        <div className="mt-6 flex justify-end gap-3">
                            <button
                                type="button"
                                onClick={() => setIsEditOpen(false)}
                                disabled={updateProjectMutation.isPending}
                                className="rounded-lg border border-slate-200 px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:opacity-50"
                            >
                                Cancel
                            </button>

                            <button
                                type="button"
                                onClick={handleUpdateProject}
                                disabled={
                                    !editName.trim() ||
                                    updateProjectMutation.isPending
                                }
                                className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
                            >
                                {updateProjectMutation.isPending ? (
                                    <>
                                        <Loader2
                                            size={16}
                                            className="animate-spin"
                                        />
                                        Saving...
                                    </>
                                ) : (
                                    <>
                                        <Save size={16} />
                                        Save changes
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* ==========================================
                DELETE PROJECT MODAL
            =========================================== */}

            {isDeleteProjectOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 px-4">
                    <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
                        <div className="flex items-start justify-between">
                            <div>
                                <h2 className="text-lg font-semibold text-slate-900">
                                    Delete project?
                                </h2>

                                <p className="mt-1 text-sm text-slate-500">
                                    This action cannot be undone.
                                </p>
                            </div>

                            <button
                                type="button"
                                onClick={() => setIsDeleteProjectOpen(false)}
                                disabled={deleteProjectMutation.isPending}
                                className="rounded-lg p-2 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
                            >
                                <X size={18} />
                            </button>
                        </div>

                        <div className="mt-5 rounded-xl border border-red-200 bg-red-50 p-4">
                            <p className="text-sm font-medium text-red-900">
                                {project.name}
                            </p>

                            <p className="mt-2 text-sm leading-6 text-red-700">
                                This will permanently delete the project, its
                                documents, workflow runs, findings, and
                                reconciliation data.
                            </p>
                        </div>

                        {deleteProjectMutation.isError && (
                            <div className="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3">
                                <p className="text-sm text-red-700">
                                    {deleteProjectMutation.error instanceof
                                    Error
                                        ? deleteProjectMutation.error.message
                                        : "Failed to delete project."}
                                </p>
                            </div>
                        )}

                        <div className="mt-6 flex justify-end gap-3">
                            <button
                                type="button"
                                onClick={() => setIsDeleteProjectOpen(false)}
                                disabled={deleteProjectMutation.isPending}
                                className="rounded-lg border border-slate-200 px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:opacity-50"
                            >
                                Cancel
                            </button>

                            <button
                                type="button"
                                onClick={handleDeleteProject}
                                disabled={deleteProjectMutation.isPending}
                                className="inline-flex items-center gap-2 rounded-lg bg-red-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-50"
                            >
                                {deleteProjectMutation.isPending ? (
                                    <>
                                        <Loader2
                                            size={16}
                                            className="animate-spin"
                                        />
                                        Deleting...
                                    </>
                                ) : (
                                    <>
                                        <Trash2 size={16} />
                                        Delete project
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* ==========================================
                DELETE DOCUMENT MODAL
            =========================================== */}

            {documentToDelete && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 px-4">
                    <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
                        <div className="flex items-start justify-between">
                            <div>
                                <h2 className="text-lg font-semibold text-slate-900">
                                    Remove document?
                                </h2>

                                <p className="mt-1 text-sm text-slate-500">
                                    The document and its extracted content will
                                    be removed.
                                </p>
                            </div>

                            <button
                                type="button"
                                onClick={() => setDocumentToDelete(null)}
                                disabled={deleteDocumentMutation.isPending}
                                className="rounded-lg p-2 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
                            >
                                <X size={18} />
                            </button>
                        </div>

                        <div className="mt-5 rounded-xl bg-slate-50 p-4">
                            <div className="flex items-center gap-3">
                                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-white">
                                    <FileText
                                        size={18}
                                        className="text-slate-500"
                                    />
                                </div>

                                <p className="truncate text-sm font-medium text-slate-700">
                                    {documentToDelete.filename}
                                </p>
                            </div>
                        </div>

                        {deleteDocumentMutation.isError && (
                            <div className="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3">
                                <p className="text-sm text-red-700">
                                    {deleteDocumentMutation.error instanceof
                                    Error
                                        ? deleteDocumentMutation.error.message
                                        : "Failed to remove document."}
                                </p>
                            </div>
                        )}

                        <div className="mt-6 flex justify-end gap-3">
                            <button
                                type="button"
                                onClick={() => setDocumentToDelete(null)}
                                disabled={deleteDocumentMutation.isPending}
                                className="rounded-lg border border-slate-200 px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:opacity-50"
                            >
                                Cancel
                            </button>

                            <button
                                type="button"
                                onClick={handleDeleteDocument}
                                disabled={deleteDocumentMutation.isPending}
                                className="inline-flex items-center gap-2 rounded-lg bg-red-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-50"
                            >
                                {deleteDocumentMutation.isPending ? (
                                    <>
                                        <Loader2
                                            size={16}
                                            className="animate-spin"
                                        />
                                        Removing...
                                    </>
                                ) : (
                                    <>
                                        <Trash2 size={16} />
                                        Remove document
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </main>
    );
}
