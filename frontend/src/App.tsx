import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import Dashboard from "./pages/Dashboard";
import NewProject from "./pages/NewProject";
import Project from "./pages/Project";

function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/" element={<Navigate to="/projects" replace />} />

                <Route path="/projects" element={<Dashboard />} />

                <Route path="/projects/new" element={<NewProject />} />

                <Route path="/projects/:projectId" element={<Project />} />

                <Route
                    path="/projects/:projectId"
                    element={<div className="p-10">Project Details</div>}
                />
            </Routes>
        </BrowserRouter>
    );
}

export default App;
