// @/lib/oauthSecurity.js
const { findUserByEmailOrPhone, recordFailedAttempt, recordSuccessfulLogin } = require("@/lib/users");
const { calculateRiskScore } = require("@/lib/riskEngine");
const { analyzeFraud } = require("@/lib/llmClient");

export async function verifyOAuthLogin(email) {
    // 1. Find User
    const user = findUserByEmailOrPhone(email);
    if (!user) {
        return { exists: false, allowed: false, error: "User not registered." };
    }

    // Default IP/UA for server-side OAuth checks (or grab from headers if you pass them down)
    const ip = "OAuth-Server-Side"; 
    const userAgent = "NextAuth-Callback";

    // 2. Run Risk Engine
    const riskAssessment = calculateRiskScore({
        user, ip, userAgent, timestamp: new Date(),
    });

    // 3. Status Checks
    if (user.status === "suspended" || user.status === "locked") {
        return { exists: true, allowed: false, error: `Account is ${user.status}.` };
    }

    // 4. Run LLM Fraud Analysis if risk is high
    if (riskAssessment.requiresLLMAnalysis) {
        const llmAnalysis = await analyzeFraud({
            userEmail: user.email, ip, riskScore: riskAssessment.score,
            riskLevel: riskAssessment.level, failedAttempts: user.failedAttempts,
            accountStatus: user.status, factors: riskAssessment.factors,
            timestamp: new Date().toISOString(),
        });

        if (llmAnalysis.recommendedAction === "block" || llmAnalysis.recommendedAction === "suspend") {
            recordFailedAttempt(user, ip);
            return { exists: true, allowed: false, error: "Blocked by security analysis." };
        }
    }

    // 5. Success!
    recordSuccessfulLogin(user, ip);
    return { exists: true, allowed: true, user: { id: user.id, riskScore: riskAssessment.score, riskLevel: riskAssessment.level } };
}