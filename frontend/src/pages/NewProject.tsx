import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useCreateProject } from "../hooks/useProjects";
import { ArrowLeft, Loader2 } from "lucide-react";

export default function NewProject() {
    const navigate = useNavigate();
    const createProjectMutation = useCreateProject();

    const [name, setName] = useState("");
    const [description, setDescription] = useState("");

    function handleSubmit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();

        const trimmedName = name.trim();

        if (!trimmedName) {
            return;
        }

        createProjectMutation.mutate(
            {
                name: trimmedName,
                description: description.trim() || null,
            },
            {
                onSuccess: (project) => {
                    navigate(`/projects/${project.id}`);
                },
            },
        );
    }

    return (
        <main className="min-h-screen bg-slate-50">
            <div className="mx-auto max-w-3xl px-6 py-10">
                <Link
                    to="/projects"
                    className="text-sm font-medium text-slate-500 hover:text-slate-900"
                >
                    <span className="flex items-center gap-2">
                        <ArrowLeft size={16} />
                        Back to projects
                    </span>
                </Link>

                <div className="mt-8">
                    <h1 className="text-3xl font-bold tracking-tight text-slate-900">
                        Create project
                    </h1>

                    <p className="mt-2 text-slate-500">
                        Create a project to upload documents and run the
                        intelligence workflow.
                    </p>
                </div>

                <form
                    onSubmit={handleSubmit}
                    className="mt-8 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
                >
                    <div>
                        <label
                            htmlFor="name"
                            className="block text-sm font-medium text-slate-900"
                        >
                            Project name
                        </label>

                        <input
                            id="name"
                            name="name"
                            type="text"
                            value={name}
                            onChange={(event) => setName(event.target.value)}
                            placeholder="e.g. Project Alpha"
                            maxLength={255}
                            required
                            className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none transition placeholder:text-slate-400 focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
                        />
                    </div>

                    <div className="mt-6">
                        <label
                            htmlFor="description"
                            className="block text-sm font-medium text-slate-900"
                        >
                            Description
                            <span className="ml-1 font-normal text-slate-400">
                                (optional)
                            </span>
                        </label>

                        <textarea
                            id="description"
                            name="description"
                            value={description}
                            onChange={(event) =>
                                setDescription(event.target.value)
                            }
                            placeholder="Describe what this project is about..."
                            rows={5}
                            className="mt-2 w-full resize-none rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none transition placeholder:text-slate-400 focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
                        />
                    </div>

                    {createProjectMutation.isError && (
                        <div className="mt-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3">
                            <p className="text-sm text-red-700">
                                {createProjectMutation.error instanceof Error
                                    ? createProjectMutation.error.message
                                    : "Failed to create project."}
                            </p>
                        </div>
                    )}

                    <div className="mt-8 flex items-center justify-end gap-3 border-t border-slate-100 pt-6">
                        <Link
                            to="/projects"
                            className="rounded-lg px-4 py-2.5 text-sm font-medium text-slate-600 hover:bg-slate-100"
                        >
                            Cancel
                        </Link>

                        <button
                            type="submit"
                            disabled={
                                !name.trim() || createProjectMutation.isPending
                            }
                            className="rounded-lg bg-slate-900 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                            {createProjectMutation.isPending ? (
                                <span className="flex items-center gap-2">
                                    <Loader2
                                        size={16}
                                        className="animate-spin"
                                    />
                                    Creating...
                                </span>
                            ) : (
                                "Create project"
                            )}
                        </button>
                    </div>
                </form>
            </div>
        </main>
    );
}
