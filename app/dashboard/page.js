"use client";
import { useSearchParams } from "next/navigation";
import { signOut, useSession } from "next-auth/react";
import { Suspense, useState } from "react";

function DashboardContent() {
    const searchParams = useSearchParams();
    const { data: session } = useSession();
    const [loading, setLoading] = useState(false);

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

    const handleResetAccount = async () => {
        try {
            setLoading(true);
            console.log("🔄 Resetting testuser account from dashboard...");
            
            const res = await fetch("/api/reset-account", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email: "testuser@ares.com" }),
            });

            const data = await res.json();
            
            console.log("✅ Reset API Response:", data);
            
            if (data.success) {
                alert(`✅ Account reset!\n\n${data.user.name} is now ${data.user.status}\nFailed attempts: ${data.user.failedAttempts}`);
            } else {
                alert(`❌ Reset failed: ${data.error}`);
            }
        } catch (err) {
            console.error("❌ Reset error:", err);
            alert("Reset failed. Check console for details.");
        } finally {
            setLoading(false);
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
                        {session?.user?.authProvider && (
                            <li>
                                <span className="label">OAuth Provider</span>
                                <span className="value" style={{ textTransform: "capitalize" }}>
                                    {session.user.authProvider}
                                </span>
                            </li>
                        )}
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
                        {session && (
                            <li>
                                <span className="label">OAuth Token Capture</span>
                                <span className={`account-status ${session.user?.oauthTokenCaptured ? "active" : "challenged"}`}>
                                    {session.user?.oauthTokenCaptured ? "Captured" : "Unavailable"}
                                </span>
                            </li>
                        )}
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

            {/* Floating Reset Button */}
            <button
                onClick={handleResetAccount}
                disabled={loading}
                style={{
                    position: "fixed",
                    bottom: "2rem",
                    right: "2rem",
                    width: "60px",
                    height: "60px",
                    borderRadius: "50%",
                    background: "linear-gradient(135deg, #f43f5e, #e11d48)",
                    border: "2px solid rgba(255, 255, 255, 0.2)",
                    boxShadow: "0 8px 32px rgba(244, 63, 94, 0.4), 0 0 0 4px rgba(244, 63, 94, 0.1)",
                    cursor: loading ? "not-allowed" : "pointer",
                    transition: "all 0.3s ease",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: "1.5rem",
                    zIndex: 1000,
                    opacity: loading ? 0.6 : 1,
                }}
                onMouseEnter={(e) => {
                    if (!loading) {
                        e.currentTarget.style.transform = "scale(1.1) rotate(180deg)";
                        e.currentTarget.style.boxShadow = "0 12px 40px rgba(244, 63, 94, 0.6), 0 0 0 6px rgba(244, 63, 94, 0.15)";
                    }
                }}
                onMouseLeave={(e) => {
                    e.currentTarget.style.transform = "scale(1) rotate(0deg)";
                    e.currentTarget.style.boxShadow = "0 8px 32px rgba(244, 63, 94, 0.4), 0 0 0 4px rgba(244, 63, 94, 0.1)";
                }}
                title="Reset testuser@ares.com account"
            >
                {loading ? "⏳" : "🔄"}
            </button>
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
