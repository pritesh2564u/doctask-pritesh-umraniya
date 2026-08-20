import { Link } from "react-router-dom";

import { useProjects } from "../hooks/useProjects";
import { ArrowRight, Plus } from "lucide-react";

export default function Dashboard() {
    const { data: projects, isLoading, isError, error } = useProjects();

    return (
        <main className="min-h-screen bg-slate-50">
            <div className="mx-auto max-w-7xl px-6 py-10">
                <div className="flex items-start justify-between">
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight text-slate-900">
                            Projects
                        </h1>

                        <p className="mt-2 text-slate-500">
                            Manage your document intelligence projects.
                        </p>
                    </div>

                    <Link
                        to="/projects/new"
                        className="rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800"
                    >
                        <span className="flex items-center gap-2">
                            <Plus size={18} strokeWidth={2} />
                            New Project
                        </span>
                    </Link>
                </div>

                {isLoading && (
                    <div className="mt-10 rounded-xl border border-slate-200 bg-white p-8 text-center">
                        <p className="text-sm text-slate-500">
                            Loading projects...
                        </p>
                    </div>
                )}

                {isError && (
                    <div className="mt-10 rounded-xl border border-red-200 bg-red-50 p-6">
                        <h2 className="font-semibold text-red-900">
                            Failed to load projects
                        </h2>

                        <p className="mt-1 text-sm text-red-700">
                            {error instanceof Error
                                ? error.message
                                : "Something went wrong."}
                        </p>
                    </div>
                )}

                {!isLoading && !isError && projects?.length === 0 && (
                    <div className="mt-10 rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-16 text-center">
                        <h2 className="text-lg font-semibold text-slate-900">
                            No projects yet
                        </h2>

                        <p className="mx-auto mt-2 max-w-md text-sm text-slate-500">
                            Create your first project to start uploading
                            documents and running the intelligence workflow.
                        </p>

                        <Link
                            to="/projects/new"
                            className="mt-6 inline-flex rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-slate-800"
                        >
                            Create your first project
                        </Link>
                    </div>
                )}

                {!isLoading && !isError && projects && projects.length > 0 && (
                    <div className="mt-10 grid gap-5 md:grid-cols-2 lg:grid-cols-3">
                        {projects.map((project) => (
                            <Link
                                key={project.id}
                                to={`/projects/${project.id}`}
                                className="group rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-md"
                            >
                                <div className="flex items-start justify-between gap-4">
                                    <div>
                                        <h2 className="font-semibold text-slate-900 group-hover:text-slate-700">
                                            {project.name}
                                        </h2>

                                        <p className="mt-2 line-clamp-2 text-sm text-slate-500">
                                            {project.description ||
                                                "No description provided."}
                                        </p>
                                    </div>

                                    <span className="text-slate-400 transition group-hover:translate-x-1">
                                        <ArrowRight
                                            size={18}
                                            strokeWidth={2}
                                            className="transition-transform group-hover:translate-x-1"
                                        />
                                    </span>
                                </div>

                                <div className="mt-6 border-t border-slate-100 pt-4">
                                    <p className="text-xs text-slate-400">
                                        Created{" "}
                                        {new Date(
                                            project.created_at,
                                        ).toLocaleDateString()}
                                    </p>
                                </div>
                            </Link>
                        ))}
                    </div>
                )}
            </div>
        </main>
    );
}
