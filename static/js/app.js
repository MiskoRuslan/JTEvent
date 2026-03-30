// API Configuration
const API_BASE_URL = '/api';

// Token Management
const TokenManager = {
    getAccessToken() {
        const token = localStorage.getItem('access_token');
        console.log('Getting access token:', token ? token.substring(0, 20) + '...' : 'null');
        return token;
    },

    getRefreshToken() {
        const token = localStorage.getItem('refresh_token');
        console.log('Getting refresh token:', token ? token.substring(0, 20) + '...' : 'null');
        return token;
    },

    setTokens(accessToken, refreshToken) {
        console.log('Setting tokens:', {
            access: accessToken ? accessToken.substring(0, 20) + '...' : 'null',
            refresh: refreshToken ? refreshToken.substring(0, 20) + '...' : 'null'
        });
        localStorage.setItem('access_token', accessToken);
        if (refreshToken) {
            localStorage.setItem('refresh_token', refreshToken);
        }
    },

    clearTokens() {
        console.log('Clearing all tokens');
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
    },

    async refreshAccessToken() {
        const refreshToken = this.getRefreshToken();
        if (!refreshToken) {
            throw new Error('No refresh token available');
        }

        try {
            const response = await fetch(`${API_BASE_URL}/auth/token/refresh/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ refresh: refreshToken }),
            });

            if (!response.ok) {
                throw new Error('Failed to refresh token');
            }

            const data = await response.json();
            this.setTokens(data.access, data.refresh || refreshToken);
            return data.access;
        } catch (error) {
            this.clearTokens();
            throw error;
        }
    }
};

// API Wrapper
const api = {
    async request(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;

        // Public endpoints that don't need authentication
        const publicEndpoints = ['/auth/login/', '/auth/register/', '/auth/google/'];
        const isPublicEndpoint = publicEndpoints.some(pe => endpoint.startsWith(pe));

        const accessToken = isPublicEndpoint ? null : TokenManager.getAccessToken();

        const defaultHeaders = {
            'Content-Type': 'application/json',
        };

        if (accessToken) {
            defaultHeaders['Authorization'] = `Bearer ${accessToken}`;
        }

        // Don't set Content-Type for FormData
        if (options.body instanceof FormData) {
            delete defaultHeaders['Content-Type'];
        }

        const config = {
            ...options,
            headers: {
                ...defaultHeaders,
                ...options.headers,
            },
        };

        try {
            console.log(`API Request: ${endpoint}`, {
                method: config.method,
                hasAuth: !!accessToken,
                tokenPreview: accessToken ? accessToken.substring(0, 20) + '...' : 'none'
            });

            let response = await fetch(url, config);
            console.log(`API Response: ${endpoint}`, {
                status: response.status,
                ok: response.ok,
                isPublic: isPublicEndpoint
            });

            // If unauthorized, try to refresh token (but not for public endpoints)
            if (response.status === 401 && accessToken && !isPublicEndpoint) {
                console.warn('Got 401, attempting token refresh...');
                try {
                    const newToken = await TokenManager.refreshAccessToken();
                    config.headers['Authorization'] = `Bearer ${newToken}`;
                    response = await fetch(url, config);
                    console.log('Token refreshed, retrying request:', response.status);
                } catch (refreshError) {
                    console.error('Token refresh failed:', refreshError);
                    TokenManager.clearTokens();
                    showToast('Session expired. Please login again.', 'error');
                    // DON'T redirect automatically - let user see the error
                    throw new Error('Session expired');
                }
            }

            // If still 401 on public endpoint, it's a real error
            if (response.status === 401 && isPublicEndpoint) {
                const errorData = await response.json().catch(() => ({}));
                console.error('Public endpoint returned 401:', errorData);
                throw new Error(errorData.detail || errorData.error || 'Authentication failed');
            }

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                console.error('API Error:', errorData);

                // Format validation errors nicely
                if (errorData && typeof errorData === 'object' && !errorData.detail && !errorData.error) {
                    const errors = Object.entries(errorData)
                        .map(([field, messages]) => {
                            const msg = Array.isArray(messages) ? messages.join(', ') : messages;
                            return `${field}: ${msg}`;
                        })
                        .join('; ');
                    throw new Error(errors || 'Validation failed');
                }

                throw new Error(errorData.detail || errorData.error || 'Request failed');
            }

            // Handle 204 No Content
            if (response.status === 204) {
                return null;
            }

            const data = await response.json();
            console.log(`API Success: ${endpoint}`, data);
            return data;
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    },

    get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    },

    post(endpoint, data, isFormData = false) {
        const body = isFormData ? data : JSON.stringify(data);
        return this.request(endpoint, {
            method: 'POST',
            body,
        });
    },

    put(endpoint, data, isFormData = false) {
        const body = isFormData ? data : JSON.stringify(data);
        return this.request(endpoint, {
            method: 'PUT',
            body,
        });
    },

    patch(endpoint, data) {
        return this.request(endpoint, {
            method: 'PATCH',
            body: JSON.stringify(data),
        });
    },

    delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }
};

// Toast Notification System
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) return;

    const toast = document.createElement('div');
    toast.className = 'glass rounded-lg p-4 mb-3 flex items-center space-x-3 animate-slide-in shadow-lg';

    const icons = {
        success: '<svg class="w-6 h-6 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>',
        error: '<svg class="w-6 h-6 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>',
        warning: '<svg class="w-6 h-6 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>',
        info: '<svg class="w-6 h-6 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>',
    };

    toast.innerHTML = `
        ${icons[type] || icons.info}
        <span class="flex-1 font-medium">${message}</span>
        <button onclick="this.parentElement.remove()" class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
        </button>
    `;

    toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('animate-slide-out');
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

// Google OAuth Handler
async function handleGoogleAuth(credential) {
    try {
        const response = await api.post('/auth/google/', { token: credential });

        TokenManager.setTokens(response.access, response.refresh);
        localStorage.setItem('user', JSON.stringify(response.user));

        // Update Alpine store
        if (window.Alpine && Alpine.store('auth')) {
            Alpine.store('auth').setUser(response.user);
        }

        showToast('Login successful!', 'success');
        setTimeout(() => {
            window.location.href = '/dashboard';
        }, 1000);
    } catch (error) {
        showToast('Google login failed', 'error');
        console.error('Google auth error:', error);
    }
}

// Alpine.js Global Stores
document.addEventListener('alpine:init', () => {
    // Auth Store
    Alpine.store('auth', {
        user: null,
        isAuthenticated: false,

        init() {
            const userStr = localStorage.getItem('user');
            if (userStr) {
                try {
                    this.user = JSON.parse(userStr);
                    this.isAuthenticated = !!TokenManager.getAccessToken();
                } catch (error) {
                    console.error('Failed to parse user data:', error);
                    this.logout();
                }
            }
        },

        setUser(user) {
            this.user = user;
            this.isAuthenticated = true;
            localStorage.setItem('user', JSON.stringify(user));
        },

        async login(email, password) {
            try {
                const response = await api.post('/auth/login/', { email, password });
                TokenManager.setTokens(response.access, response.refresh);
                this.setUser(response.user);
                return response;
            } catch (error) {
                throw error;
            }
        },

        async logout() {
            try {
                const refreshToken = TokenManager.getRefreshToken();
                if (refreshToken) {
                    await api.post('/auth/logout/', { refresh: refreshToken });
                }
            } catch (error) {
                console.error('Logout error:', error);
            } finally {
                TokenManager.clearTokens();
                this.user = null;
                this.isAuthenticated = false;
                window.location.href = '/';
            }
        },

        async loadProfile() {
            try {
                const profile = await api.get('/auth/profile/');
                this.setUser(profile);
                return profile;
            } catch (error) {
                console.error('Failed to load profile:', error);
                this.logout();
            }
        }
    });

    // Theme Store
    Alpine.store('theme', {
        // Default to dark theme unless explicitly set to light
        dark: localStorage.getItem('theme') !== 'light',

        init() {
            this.updateTheme();
        },

        toggle() {
            this.dark = !this.dark;
            this.updateTheme();
        },

        updateTheme() {
            if (this.dark) {
                document.documentElement.classList.add('dark');
                localStorage.setItem('theme', 'dark');
            } else {
                document.documentElement.classList.remove('dark');
                localStorage.setItem('theme', 'light');
            }
        }
    });
});

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Initialize auth store
    if (window.Alpine && Alpine.store('auth')) {
        Alpine.store('auth').init();
    }

    // Initialize theme
    if (window.Alpine && Alpine.store('theme')) {
        Alpine.store('theme').init();
    }
});

// Utility Functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function formatCurrency(amount, currency = 'USD') {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency,
    }).format(amount);
}

function formatRelativeTime(date) {
    const now = new Date();
    const then = new Date(date);
    const diffInSeconds = Math.floor((now - then) / 1000);

    const intervals = {
        year: 31536000,
        month: 2592000,
        week: 604800,
        day: 86400,
        hour: 3600,
        minute: 60,
        second: 1,
    };

    for (const [unit, secondsInUnit] of Object.entries(intervals)) {
        const interval = Math.floor(diffInSeconds / secondsInUnit);
        if (interval >= 1) {
            return `${interval} ${unit}${interval > 1 ? 's' : ''} ago`;
        }
    }

    return 'just now';
}

// Real-time Event Updates (WebSocket placeholder)
class EventUpdates {
    constructor() {
        this.listeners = new Map();
    }

    subscribe(eventId, callback) {
        if (!this.listeners.has(eventId)) {
            this.listeners.set(eventId, []);
        }
        this.listeners.get(eventId).push(callback);
    }

    unsubscribe(eventId, callback) {
        const callbacks = this.listeners.get(eventId);
        if (callbacks) {
            const index = callbacks.indexOf(callback);
            if (index > -1) {
                callbacks.splice(index, 1);
            }
        }
    }

    notify(eventId, data) {
        const callbacks = this.listeners.get(eventId);
        if (callbacks) {
            callbacks.forEach(cb => cb(data));
        }
    }
}

const eventUpdates = new EventUpdates();

// Export for global use
window.api = api;
window.showToast = showToast;
window.TokenManager = TokenManager;
window.handleGoogleAuth = handleGoogleAuth;
window.eventUpdates = eventUpdates;
window.debounce = debounce;
window.formatCurrency = formatCurrency;
window.formatRelativeTime = formatRelativeTime;
