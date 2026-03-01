"use client";
import { useState, useEffect } from "react";
import { signIn } from "next-auth/react";

export default function LoginPage() {
  const [loginType, setLoginType] = useState("email"); // email or phone
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(null); // { type, message }
  const [riskInfo, setRiskInfo] = useState(null);
  const [showPopup, setShowPopup] = useState(false);

  // Particles effect
  useEffect(() => {
    const container = document.getElementById("particles");
    if (!container) return;
    for (let i = 0; i < 30; i++) {
      const particle = document.createElement("div");
      particle.className = "particle";
      particle.style.left = Math.random() * 100 + "%";
      particle.style.animationDuration = Math.random() * 10 + 8 + "s";
      particle.style.animationDelay = Math.random() * 5 + "s";
      particle.style.width = Math.random() * 3 + 1 + "px";
      particle.style.height = particle.style.width;
      container.appendChild(particle);
    }
    return () => {
      if (container) container.innerHTML = "";
    };
  }, []);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setStatus(null);
    setRiskInfo(null);

    try {
      const res = await fetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ identifier, password }),
      });

      const data = await res.json();

      if (data.riskScore !== undefined) {
        setRiskInfo({
          score: data.riskScore,
          level: data.riskLevel || "low",
        });
      }

      if (data.success) {
        setStatus({
          type: "success",
          message: data.message || "Login successful!",
        });
        // Redirect to dashboard after short delay
        setTimeout(() => {
          window.location.href = "/dashboard?user=" + encodeURIComponent(JSON.stringify(data.user));
        }, 1000);
      } else {
        let errorMsg = data.error || "Login failed.";
        if (data.accountStatus === "locked") {
          errorMsg = `🔒 Account locked! (${data.failedAttempts} failed attempts)`;
        } else if (data.accountStatus === "suspended") {
          errorMsg = "🚫 Account suspended. Contact administrator.";
        } else if (data.accountStatus === "challenged") {
          errorMsg = `⚠️ Account under review. ${errorMsg}`;
        } else if (data.failedAttempts) {
          errorMsg += ` (Attempt ${data.failedAttempts})`;
        }
        if (data.llmAnalysis) {
          errorMsg += ` — AI: ${data.llmAnalysis.reasoning}`;
        }
        setStatus({ type: "error", message: errorMsg });
      }
    } catch (err) {
      setStatus({ type: "error", message: "Network error. Please try again." });
    } finally {
      setLoading(false);
    }
  };

  const handleSocialLogin = (provider) => {
    signIn(provider, { callbackUrl: "/dashboard" });
  };

  const togglePopup = () => {
    setShowPopup(!showPopup);
  };

  return (
    <>
      <div className="particles" id="particles"></div>

      {/* Dynamic overlay popup for testing (Test Case 2: Multimodal Failure) */}
      {showPopup && (
        <div
          id="dynamic-popup-overlay"
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.7)",
            zIndex: 1000,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <div
            style={{
              background: "var(--bg-secondary)",
              border: "1px solid var(--border-color)",
              borderRadius: "var(--radius-lg)",
              padding: "2rem",
              maxWidth: "400px",
              textAlign: "center",
            }}
          >
            <h3 style={{ marginBottom: "1rem" }}>🍪 Cookie Notice</h3>
            <p style={{ color: "var(--text-secondary)", marginBottom: "1.5rem", fontSize: "0.9rem" }}>
              We use cookies to enhance your experience. By continuing, you agree to our cookie policy.
            </p>
            <button
              id="close-popup-btn"
              onClick={togglePopup}
              className="btn-primary"
              style={{ maxWidth: "200px", margin: "0 auto" }}
            >
              Accept & Close
            </button>
          </div>
        </div>
      )}

      <div className="login-container">
        <div className="login-card">
          <div className="login-header">
            <div className="login-logo">
              <div className="logo-icon">A</div>
              <span className="logo-text">ARES</span>
            </div>
            <h1>Welcome Back</h1>
            <p>Sign in to your secure account</p>
          </div>

          {status && (
            <div className={`status-message ${status.type}`}>
              {status.message}
            </div>
          )}

          {riskInfo && (
            <div style={{ marginBottom: "1rem" }}>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  fontSize: "0.75rem",
                  color: "var(--text-muted)",
                  marginBottom: "0.25rem",
                }}
              >
                <span>Risk Score</span>
                <span
                  style={{
                    color:
                      riskInfo.level === "critical"
                        ? "var(--accent-rose)"
                        : riskInfo.level === "high"
                          ? "var(--accent-amber)"
                          : "var(--accent-emerald)",
                  }}
                >
                  {riskInfo.score}/100 ({riskInfo.level})
                </span>
              </div>
              <div className="risk-bar">
                <div
                  className={`risk-bar-fill ${riskInfo.score >= 50 ? "high" : riskInfo.score >= 30 ? "medium" : "low"
                    }`}
                  style={{ width: `${riskInfo.score}%` }}
                ></div>
              </div>
            </div>
          )}

          <form className="login-form" onSubmit={handleLogin}>
            <div className="login-tabs">
              <button
                type="button"
                className={`login-tab ${loginType === "email" ? "active" : ""}`}
                onClick={() => {
                  setLoginType("email");
                  setIdentifier("");
                }}
                id="tab-email"
              >
                📧 Email
              </button>
              <button
                type="button"
                className={`login-tab ${loginType === "phone" ? "active" : ""}`}
                onClick={() => {
                  setLoginType("phone");
                  setIdentifier("");
                }}
                id="tab-phone"
              >
                📱 Phone
              </button>
            </div>

            <div className="form-group">
              <label htmlFor="identifier">
                {loginType === "email" ? "Email Address" : "Phone Number"}
              </label>
              <input
                type={loginType === "email" ? "email" : "tel"}
                id="identifier"
                className="form-input"
                placeholder={
                  loginType === "email"
                    ? "you@example.com"
                    : "+90 555 123 4567"
                }
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
                required
                autoComplete={loginType === "email" ? "email" : "tel"}
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input
                type="password"
                id="password"
                className="form-input"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
              />
            </div>

            <button
              type="submit"
              className="btn-primary"
              id="login-btn"
              disabled={loading}
            >
              {loading ? (
                <>
                  <span className="spinner"></span> Authenticating...
                </>
              ) : (
                "Sign In"
              )}
            </button>
          </form>

          <div className="divider">
            <span>or continue with</span>
          </div>

          <div className="social-buttons">
            <button
              className="btn-social btn-google"
              id="google-login-btn"
              onClick={() => handleSocialLogin("google")}
              type="button"
            >
              <span className="social-icon">
                <svg width="20" height="20" viewBox="0 0 24 24">
                  <path
                    fill="#4285F4"
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
                  />
                  <path
                    fill="#34A853"
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  />
                  <path
                    fill="#FBBC05"
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                  />
                  <path
                    fill="#EA4335"
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                  />
                </svg>
              </span>
              Login with Google
            </button>

            <button
              className="btn-social btn-facebook"
              id="facebook-login-btn"
              onClick={() => handleSocialLogin("facebook")}
              type="button"
            >
              <span className="social-icon">
                <svg width="20" height="20" viewBox="0 0 24 24">
                  <path
                    fill="#1877F2"
                    d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"
                  />
                </svg>
              </span>
              Login with Facebook
            </button>
          </div>

          {/* Hidden button to trigger popup for testing */}
          <button
            id="trigger-popup-btn"
            onClick={togglePopup}
            style={{
              marginTop: "1rem",
              width: "100%",
              padding: "0.5rem",
              background: "transparent",
              border: "1px dashed var(--border-color)",
              borderRadius: "var(--radius-sm)",
              color: "var(--text-muted)",
              fontSize: "0.75rem",
              cursor: "pointer",
              fontFamily: "inherit",
            }}
          >
            🧪 Toggle Test Popup (for Selenium test scenarios)
          </button>

          <div
            style={{
              marginTop: "1.5rem",
              textAlign: "center",
              fontSize: "0.8rem",
              color: "var(--text-muted)",
            }}
          >
            Test Accounts: testuser@ares.com / Test@1234
            <br />
            admin@ares.com / Admin@5678
          </div>
        </div>
      </div>
    </>
  );
}
