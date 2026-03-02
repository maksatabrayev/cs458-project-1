// Context-Aware Risk Assessment Engine
// Calculates a risk score (0-100) based on multiple signals

const { getIPAttempts } = require("./users");

/**
 * Calculate risk score for a login attempt.
 * @param {Object} context - Login context
 * @param {Object} context.user - The user object
 * @param {string} context.ip - Client IP address
 * @param {string} context.userAgent - Browser user agent
 * @param {Date} context.timestamp - Login timestamp
 * @returns {Object} - { score, level, factors[] }
 */
function calculateRiskScore(context) {
    const { user, ip, userAgent, timestamp } = context;
    let score = 0;
    const factors = [];
    let unknownIPDetected = false;

    // Factor 1: Unknown IP address (new device/location)
    if (user && !user.knownIPs.includes(ip)) {
        score += 25;
        unknownIPDetected = true;
        factors.push({
            name: "Unknown IP",
            points: 25,
            detail: `Login attempt from unrecognized IP: ${ip}`,
        });
    }

    // Factor 2: Failed login attempts (user-level)
    if (user) {
        const failedPenalty = Math.min(user.failedAttempts * 8, 40);
        if (failedPenalty > 0) {
            score += failedPenalty;
            factors.push({
                name: "Failed Attempts",
                points: failedPenalty,
                detail: `${user.failedAttempts} consecutive failed login attempts`,
            });
        }
    }

    // Factor 3: IP-level rate limiting
    const ipAttempts = getIPAttempts(ip);
    if (ipAttempts.count > 5) {
        const ipPenalty = Math.min((ipAttempts.count - 5) * 5, 20);
        score += ipPenalty;
        factors.push({
            name: "IP Rate Limit",
            points: ipPenalty,
            detail: `${ipAttempts.count} attempts from this IP`,
        });
    }

    // Factor 4: Unusual login time (between 2 AM - 5 AM)
    const hour = new Date(timestamp).getHours();
    if (hour >= 2 && hour <= 5) {
        score += 10;
        factors.push({
            name: "Unusual Time",
            points: 10,
            detail: `Login attempt at unusual hour: ${hour}:00`,
        });
    }

    // Factor 5: Account already in non-active state
    if (user) {
        const statusPenalty = {
            active: 0,
            challenged: 10,
            locked: 30,
            suspended: 50,
        };
        const penalty = statusPenalty[user.status] || 0;
        if (penalty > 0) {
            score += penalty;
            factors.push({
                name: "Account Status",
                points: penalty,
                detail: `Account is currently ${user.status}`,
            });
        }
    }

    // Cap the score at 100
    score = Math.min(score, 100);

    // Determine risk level
    let level = "low";
    if (score >= 70) level = "critical";
    else if (score >= 50) level = "high";
    else if (score >= 30) level = "medium";

    return {
        score,
        level,
        factors,
        recommendation: getRecommendation(score, level),
        requiresLLMAnalysis:
            score >= 50 ||
            unknownIPDetected ||
            (user && user.failedAttempts >= 10),
        triggers: {
            unknownIP: unknownIPDetected,
            failedAttemptsThreshold: Boolean(user && user.failedAttempts >= 10),
            scoreThreshold: score >= 50,
        },
    };
}

function getRecommendation(score, level) {
    if (score >= 70)
        return "Block login and suspend account. Request manual verification.";
    if (score >= 50)
        return "Challenge the user with additional verification before allowing access.";
    if (score >= 30)
        return "Allow login but flag for monitoring. Consider additional verification step.";
    return "Allow login. No additional action required.";
}

module.exports = { calculateRiskScore };
