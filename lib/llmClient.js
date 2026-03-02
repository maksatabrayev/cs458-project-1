// Gemini LLM Client for fraud analysis and self-healing support
const { GoogleGenerativeAI } = require("@google/generative-ai");

const GEMINI_API_KEY = (process.env.GEMINI_API_KEY || "").trim();
const genAI = GEMINI_API_KEY ? new GoogleGenerativeAI(GEMINI_API_KEY) : null;

function llmConfigured() {
    return Boolean(GEMINI_API_KEY);
}

/**
 * Analyze a login attempt for potential fraud using Gemini LLM.
 * @param {Object} riskContext - The risk assessment data
 * @returns {Object} - { isFraudulent, confidence, reasoning, action }
 */
async function analyzeFraud(riskContext) {
    if (!llmConfigured()) {
        return {
            success: false,
            isFraudulent: riskContext.riskScore >= 70,
            confidence: 0.5,
            reasoning: "GEMINI_API_KEY missing. Using rule-based fallback.",
            recommendedAction:
                riskContext.riskScore >= 70
                    ? "block"
                    : riskContext.riskScore >= 50
                        ? "challenge"
                        : "allow",
        };
    }

    try {
        const model = genAI.getGenerativeModel({ model: "gemini-2.0-flash" });

        const prompt = `You are a security analyst AI for the ARES authentication system.
Analyze the following login attempt and determine if it is potentially fraudulent.

LOGIN CONTEXT:
- User: ${riskContext.userEmail || "Unknown"}
- IP Address: ${riskContext.ip}
- Risk Score: ${riskContext.riskScore}/100
- Risk Level: ${riskContext.riskLevel}
- Failed Attempts: ${riskContext.failedAttempts}
- Account Status: ${riskContext.accountStatus}
- Risk Factors: ${JSON.stringify(riskContext.factors)}
- Timestamp: ${riskContext.timestamp}

RESPOND IN EXACTLY THIS JSON FORMAT (no markdown, no extra text):
{
  "isFraudulent": true/false,
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation",
  "recommendedAction": "allow" | "challenge" | "block" | "suspend"
}`;

        const result = await model.generateContent(prompt);
        const response = result.response.text();

        // Parse the JSON response, handling potential markdown wrapping
        let cleanResponse = response.trim();
        if (cleanResponse.startsWith("```")) {
            cleanResponse = cleanResponse.replace(/```(?:json)?\n?/g, "").trim();
        }

        const analysis = JSON.parse(cleanResponse);
        return {
            success: true,
            ...analysis,
        };
    } catch (error) {
        console.error("LLM Fraud Analysis Error:", error.message);
        // Fallback: use rule-based decision if LLM fails
        return {
            success: false,
            isFraudulent: riskContext.riskScore >= 70,
            confidence: 0.5,
            reasoning: "LLM analysis unavailable. Using rule-based fallback.",
            recommendedAction:
                riskContext.riskScore >= 70
                    ? "block"
                    : riskContext.riskScore >= 50
                        ? "challenge"
                        : "allow",
        };
    }
}

/**
 * Repair a broken Selenium selector using LLM.
 * This function is called from the test framework via API.
 * @param {string} oldSelector - The original selector that failed
 * @param {string} domSnippet - Current page DOM (trimmed)
 * @param {string} elementDescription - What the element should be
 * @returns {Object} - { newSelector, selectorType, confidence }
 */
async function repairSelector(oldSelector, domSnippet, elementDescription) {
    if (!llmConfigured()) {
        return {
            newSelector: null,
            selectorType: null,
            confidence: 0,
            reasoning: "GEMINI_API_KEY missing. LLM selector repair disabled.",
        };
    }

    try {
        const model = genAI.getGenerativeModel({ model: "gemini-2.0-flash" });

        const prompt = `You are a Selenium test repair assistant. A test element locator has broken due to UI changes.

OLD SELECTOR: ${oldSelector}
ELEMENT DESCRIPTION: ${elementDescription}

CURRENT PAGE DOM (relevant section):
${domSnippet.substring(0, 4000)}

Your task:
1. Analyze the DOM to find the element that most likely matches the old selector's intent.
2. Return a new, valid CSS selector or XPath that will locate the correct element.
3. Do NOT hallucinate selectors. Only return selectors for elements actually present in the DOM.

RESPOND IN EXACTLY THIS JSON FORMAT (no markdown, no extra text):
{
  "newSelector": "the new CSS selector or XPath",
  "selectorType": "css" | "xpath",
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation of why this element matches"
}`;

        const result = await model.generateContent(prompt);
        const response = result.response.text();

        let cleanResponse = response.trim();
        if (cleanResponse.startsWith("```")) {
            cleanResponse = cleanResponse.replace(/```(?:json)?\n?/g, "").trim();
        }

        return JSON.parse(cleanResponse);
    } catch (error) {
        console.error("LLM Selector Repair Error:", error.message);
        return {
            newSelector: null,
            selectorType: null,
            confidence: 0,
            reasoning: "LLM repair failed: " + error.message,
        };
    }
}

/**
 * Resolve interaction blockers (e.g. popup overlays intercepting clicks).
 * @param {string} targetSelector - The selector of the element we want to interact with
 * @param {string} domSnippet - Current page DOM
 * @param {string} actionDescription - Human-readable intent
 * @returns {Object} - { blockerSelector, selectorType, action, confidence, reasoning }
 */
async function resolveInteractionBlocker(targetSelector, domSnippet, actionDescription) {
    if (!llmConfigured()) {
        return {
            blockerSelector: "#close-popup-btn",
            selectorType: "css",
            action: "click",
            confidence: 0.35,
            reasoning: "GEMINI_API_KEY missing. Using fallback close selector.",
        };
    }

    try {
        const model = genAI.getGenerativeModel({ model: "gemini-2.0-flash" });

        const prompt = `You are a Selenium recovery assistant.
The target element exists but interaction is blocked (for example by popup/overlay/modal/backdrop).

TARGET SELECTOR: ${targetSelector}
ACTION INTENT: ${actionDescription || "Click target element"}

CURRENT PAGE DOM (relevant section):
${domSnippet.substring(0, 4000)}

Your task:
1. Identify the most likely blocking element.
2. Identify the best element to interact with in order to dismiss/close that blocker.
3. Return a selector and action to unblock interaction.

RESPOND IN EXACTLY THIS JSON FORMAT (no markdown, no extra text):
{
  "blockerSelector": "CSS selector or XPath for close/dismiss element",
  "selectorType": "css" | "xpath",
  "action": "click" | "remove",
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation"
}`;

        const result = await model.generateContent(prompt);
        const response = result.response.text();

        let cleanResponse = response.trim();
        if (cleanResponse.startsWith("```")) {
            cleanResponse = cleanResponse.replace(/```(?:json)?\n?/g, "").trim();
        }

        return JSON.parse(cleanResponse);
    } catch (error) {
        console.error("LLM Interaction Blocker Resolution Error:", error.message);
        return {
            blockerSelector: "#close-popup-btn",
            selectorType: "css",
            action: "click",
            confidence: 0.35,
            reasoning: "LLM unavailable. Using fallback close selector.",
        };
    }
}

module.exports = { analyzeFraud, repairSelector, resolveInteractionBlocker };
