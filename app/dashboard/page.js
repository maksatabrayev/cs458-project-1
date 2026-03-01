"use client";
import { useSearchParams } from "next/navigation";
import { signOut, useSession } from "next-auth/react";
import { Suspense } from "react";

function DashboardContent() {
    const searchParams = useSearchParams();
    const { data: session } = useSession();

    let user = null;
    try {
        const userParam = searchParams.get("user");
        if (userParam) {
            user = JSON.parse(userParam);
        }
    } catch (e) { }

    // Use session data if available, otherwise use URL params
    const displayUser = session?.user || user;

    const handleLogout = () => {
        if (session) {
            signOut({ callbackUrl: "/" });
        } else {
            window.location.href = "/";
        }
    };

    return (
        <div className="dashboard-container">
            <div className="dashboard-header">
                <div>
                    <h1>🛡️ ARES Dashboard</h1>
                    <p style={{ color: "var(--text-secondary)", marginTop: "0.25rem" }}>
                        Welcome back, {displayUser?.name || "User"}
                    </p>
                </div>
                <button className="btn-logout" onClick={handleLogout} id="logout-btn">
                    Sign Out
                </button>
            </div>

            <div className="dashboard-content">
                <div className="dashboard-card">
                    <h3>User Profile</h3>
                    <ul className="user-info-list">
                        <li>
                            <span className="label">Name</span>
                            <span className="value">{displayUser?.name || "N/A"}</span>
                        </li>
                        <li>
                            <span className="label">Email</span>
                            <span className="value">{displayUser?.email || "N/A"}</span>
                        </li>
                        <li>
                            <span className="label">Status</span>
                            <span className={`account-status ${displayUser?.status || "active"}`}>
                                {displayUser?.status || "Active"}
                            </span>
                        </li>
                        <li>
                            <span className="label">Auth Method</span>
                            <span className="value">
                                {session ? "OAuth (Social)" : "Credentials"}
                            </span>
                        </li>
                    </ul>
                </div>

                <div className="dashboard-card">
                    <h3>Security Status</h3>
                    <ul className="user-info-list">
                        <li>
                            <span className="label">Session</span>
                            <span className="account-status active">Active</span>
                        </li>
                        <li>
                            <span className="label">Login Time</span>
                            <span className="value">{new Date().toLocaleTimeString()}</span>
                        </li>
                        <li>
                            <span className="label">Risk Assessment</span>
                            <span className="account-status active">Passed</span>
                        </li>
                    </ul>
                </div>

                <div className="dashboard-card">
                    <h3>System Info</h3>
                    <ul className="user-info-list">
                        <li>
                            <span className="label">System</span>
                            <span className="value">ARES v1.0</span>
                        </li>
                        <li>
                            <span className="label">Framework</span>
                            <span className="value">Self-Healing Auth</span>
                        </li>
                        <li>
                            <span className="label">AI Engine</span>
                            <span className="value">Gemini 2.0 Flash</span>
                        </li>
                    </ul>
                </div>
            </div>
        </div>
    );
}

export default function DashboardPage() {
    return (
        <Suspense fallback={<div className="dashboard-container"><p style={{ color: "var(--text-secondary)", textAlign: "center", marginTop: "2rem" }}>Loading dashboard...</p></div>}>
            <DashboardContent />
        </Suspense>
    );
}
