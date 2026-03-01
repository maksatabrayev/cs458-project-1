// In-memory user store with account state management
// Account states: Active, Locked, Challenged, Suspended

const bcrypt = require("bcryptjs");

// Pre-hashed passwords for test users
const USERS = [
    {
        id: "1",
        email: "testuser@ares.com",
        phone: "+905551234567",
        password: bcrypt.hashSync("Test@1234", 10),
        name: "Test User",
        status: "active", // active | locked | challenged | suspended
        failedAttempts: 0,
        lastFailedAt: null,
        lastLoginAt: null,
        lastLoginIP: null,
        knownIPs: ["127.0.0.1", "::1"],
        loginHistory: [],
    },
    {
        id: "2",
        email: "admin@ares.com",
        phone: "+905559876543",
        password: bcrypt.hashSync("Admin@5678", 10),
        name: "Admin User",
        status: "active",
        failedAttempts: 0,
        lastFailedAt: null,
        lastLoginAt: null,
        lastLoginIP: null,
        knownIPs: ["127.0.0.1", "::1"],
        loginHistory: [],
    },
];

// Track login attempts per IP for rate limiting
const IP_ATTEMPTS = {};

function findUserByEmail(email) {
    return USERS.find((u) => u.email === email);
}

function findUserByPhone(phone) {
    return USERS.find((u) => u.phone === phone);
}

function findUserByEmailOrPhone(identifier) {
    return (
        USERS.find((u) => u.email === identifier) ||
        USERS.find((u) => u.phone === identifier)
    );
}

function validatePassword(user, password) {
    return bcrypt.compareSync(password, user.password);
}

function recordFailedAttempt(user, ip) {
    user.failedAttempts += 1;
    user.lastFailedAt = new Date().toISOString();

    // Track IP-level attempts
    if (!IP_ATTEMPTS[ip]) {
        IP_ATTEMPTS[ip] = { count: 0, firstAttempt: new Date().toISOString() };
    }
    IP_ATTEMPTS[ip].count += 1;

    // State transitions based on failed attempts
    if (user.failedAttempts >= 15) {
        user.status = "suspended";
    } else if (user.failedAttempts >= 10) {
        user.status = "locked";
    } else if (user.failedAttempts >= 5) {
        user.status = "challenged";
    }

    return user;
}

function recordSuccessfulLogin(user, ip) {
    user.failedAttempts = 0;
    user.lastFailedAt = null;
    user.lastLoginAt = new Date().toISOString();
    user.lastLoginIP = ip;
    if (!user.knownIPs.includes(ip)) {
        user.knownIPs.push(ip);
    }
    user.loginHistory.push({
        timestamp: new Date().toISOString(),
        ip: ip,
        success: true,
    });
    return user;
}

function getIPAttempts(ip) {
    return IP_ATTEMPTS[ip] || { count: 0, firstAttempt: null };
}

function resetIPAttempts(ip) {
    delete IP_ATTEMPTS[ip];
}

function resetUserStatus(userId) {
    const user = USERS.find((u) => u.id === userId);
    if (user) {
        user.status = "active";
        user.failedAttempts = 0;
        user.lastFailedAt = null;
    }
    return user;
}

function getAllUsers() {
    return USERS.map(({ password, ...rest }) => rest);
}

module.exports = {
    findUserByEmail,
    findUserByPhone,
    findUserByEmailOrPhone,
    validatePassword,
    recordFailedAttempt,
    recordSuccessfulLogin,
    getIPAttempts,
    resetIPAttempts,
    resetUserStatus,
    getAllUsers,
};
