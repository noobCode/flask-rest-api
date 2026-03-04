// API Configuration
const API_BASE_URL = 'http://localhost:5000';

// State Management
const appState = {
    user: null,
    token: null,
    refreshToken: null,
    isAdmin: false
};

// Performance: Debounce and throttle utilities
const debounce = (fn, delay) => {
    let timeoutId;
    return function(...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => fn.apply(this, args), delay);
    };
};

const throttle = (fn, limit) => {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            fn.apply(this, args);
            inThrottle = true;
            setTimeout(() => (inThrottle = false), limit);
        }
    };
};

// Initialize App
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}

function initApp() {
    setupEventListeners();
    restoreSession();
    // Performance: Use requestIdleCallback for non-critical tasks
    if ('requestIdleCallback' in window) {
        requestIdleCallback(() => {
            preloadCriticalResources();
        });
    }
}

// Preload critical resources
function preloadCriticalResources() {
    // Images and fonts can be preloaded here if needed
    // DNS prefetch for API calls
    const link = document.createElement('link');
    link.rel = 'prefetch';
    link.href = API_BASE_URL;
    document.head.appendChild(link);
}

// Event Listeners Setup - Using event delegation for performance
function setupEventListeners() {
    // Form submissions
    document.getElementById('registerForm')?.addEventListener('submit', handleRegister);
    document.getElementById('loginForm')?.addEventListener('submit', handleLogin);
    document.getElementById('updateUserForm')?.addEventListener('submit', handleUpdateUser);
    
    // Navigation links with event delegation
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('nav-link')) {
            e.preventDefault();
            const page = e.target.getAttribute('data-page');
            navigateTo(page);
        }
    });

    // Logout button
    document.getElementById('logoutBtn')?.addEventListener('click', handleLogout);

    // Performance: Throttle resize events
    if (window.innerWidth <= 768) {
        window.addEventListener('resize', throttle(() => {
            adjustLayoutForMobile();
        }, 250));
    }
}

// Page Navigation with lazy rendering
function navigateTo(pageName) {
    // Hide all pages
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });

    // Show selected page
    const page = document.getElementById(`${pageName}-page`);
    if (page) {
        page.classList.add('active');
    }

    // Update nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('data-page') === pageName) {
            link.classList.add('active');
        }
    });

    // Load data if needed (lazy load)
    if (pageName === 'dashboard') {
        // Use requestAnimationFrame for smooth rendering
        requestAnimationFrame(() => {
            loadDashboard();
        });
    }

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Session Management
function restoreSession() {
    try {
        const savedToken = localStorage.getItem('accessToken');
        const savedUser = localStorage.getItem('user');
        
        if (savedToken && savedUser) {
            appState.token = savedToken;
            appState.refreshToken = localStorage.getItem('refreshToken');
            appState.user = savedUser;
            appState.isAdmin = localStorage.getItem('isAdmin') === 'true';
            updateUIForLoggedInUser();
        }
    } catch (error) {
        console.error('Error restoring session:', error);
        localStorage.clear();
    }
}

function updateUIForLoggedInUser() {
    // Show/hide nav items
    document.querySelectorAll('[data-page="register"], [data-page="login"]').forEach(el => {
        el.style.display = 'none';
    });
    document.querySelector('[data-page="dashboard"]').style.display = '';
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) logoutBtn.style.display = '';

    // Show user info
    const userInfo = document.getElementById('userInfo');
    if (userInfo) {
        userInfo.innerHTML = `
            <div class="username">${escapeHTML(appState.user)}</div>
            <div class="role">${appState.isAdmin ? 'Administrator' : 'User'}</div>
        `;
    }

    // Show admin section if user is admin
    const adminSection = document.getElementById('adminSection');
    if (adminSection && appState.isAdmin) {
        adminSection.style.display = '';
    }
}

function updateUIForLoggedOutUser() {
    // Show/hide nav items
    document.querySelectorAll('[data-page="register"], [data-page="login"]').forEach(el => {
        el.style.display = '';
    });
    document.querySelector('[data-page="dashboard"]').style.display = 'none';
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) logoutBtn.style.display = 'none';

    // Clear user info
    const userInfo = document.getElementById('userInfo');
    if (userInfo) userInfo.innerHTML = '';
    
    const adminSection = document.getElementById('adminSection');
    if (adminSection) adminSection.style.display = 'none';

    navigateTo('home');
}

// XSS Prevention
function escapeHTML(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// Register Handler
async function handleRegister(e) {
    e.preventDefault();

    const formData = {
        username: document.getElementById('regUsername').value.trim(),
        email: document.getElementById('regEmail').value.trim(),
        password: document.getElementById('regPassword').value
    };

    // Validate password strength
    if (!validatePassword(formData.password)) {
        showMessage('Password must contain uppercase, lowercase, number, and special character (min 8 chars)', 'error');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();

        if (response.ok || response.status === 200) {
            showMessage('Registration successful! Please sign in.', 'success');
            document.getElementById('registerForm').reset();
            setTimeout(() => navigateTo('login'), 1500);
        } else {
            showMessage(data.Error || data.error || 'Registration failed', 'error');
        }
    } catch (error) {
        showMessage('Network error: ' + error.message, 'error');
        console.error('Registration error:', error);
    }
}

// Login Handler
async function handleLogin(e) {
    e.preventDefault();

    const formData = {
        username: document.getElementById('loginUsername').value.trim(),
        password: document.getElementById('loginPassword').value
    };

    try {
        const response = await fetch(`${API_BASE_URL}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();

        if (response.ok) {
            appState.token = data.access_token;
            appState.refreshToken = data.refresh_token;
            appState.user = formData.username;

            // Save to localStorage with error handling
            try {
                localStorage.setItem('accessToken', appState.token);
                localStorage.setItem('refreshToken', appState.refreshToken);
                localStorage.setItem('user', appState.user);
            } catch (e) {
                console.error('localStorage error:', e);
            }

            // Check if user is admin
            await checkUserRole();

            showMessage('Login successful!', 'success');
            document.getElementById('loginForm').reset();
            updateUIForLoggedInUser();
            setTimeout(() => navigateTo('dashboard'), 1000);
        } else {
            showMessage(data.error || 'Login failed', 'error');
        }
    } catch (error) {
        showMessage('Network error: ' + error.message, 'error');
        console.error('Login error:', error);
    }
}

// Check User Role
async function checkUserRole() {
    try {
        const response = await fetch(`${API_BASE_URL}/users`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${appState.token}`
            }
        });

        if (response.ok) {
            appState.isAdmin = true;
            localStorage.setItem('isAdmin', 'true');
        } else {
            appState.isAdmin = false;
            localStorage.setItem('isAdmin', 'false');
        }
    } catch (error) {
        appState.isAdmin = false;
        localStorage.setItem('isAdmin', 'false');
        console.error('Role check error:', error);
    }
}

// Load Dashboard
async function loadDashboard() {
    if (appState.isAdmin) {
        await loadAllUsers();
    }
}

// Load All Users (Admin Only)
async function loadAllUsers() {
    try {
        const response = await fetch(`${API_BASE_URL}/users`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${appState.token}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            displayUsersTable(data.users);
        } else {
            showMessage('Failed to load users', 'error');
        }
    } catch (error) {
        showMessage('Network error: ' + error.message, 'error');
        console.error('Load users error:', error);
    }
}

// Display Users Table
function displayUsersTable(users) {
    const container = document.getElementById('usersList');

    if (!users || users.length === 0) {
        container.innerHTML = '<p>No users found</p>';
        return;
    }

    // Use DocumentFragment for better performance
    const fragment = document.createDocumentFragment();
    const table = document.createElement('table');
    
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    headerRow.innerHTML = `
        <th>ID</th>
        <th>Username</th>
        <th>Email</th>
        <th>Role</th>
        <th>Actions</th>
    `;
    thead.appendChild(headerRow);
    table.appendChild(thead);

    const tbody = document.createElement('tbody');
    users.forEach(user => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${user.id}</td>
            <td>${escapeHTML(user.username)}</td>
            <td>${escapeHTML(user.email)}</td>
            <td>
                <span class="badge badge-${user.role === 'admin' ? 'warning' : 'info'}">
                    ${user.role}
                </span>
            </td>
            <td>
                ${user.role !== 'admin' ? `<button class="btn btn-sm btn-primary" onclick="promoteToAdmin(${user.id}); return false;">Promote</button>` : '<em>Admin</em>'}
            </td>
        `;
        tbody.appendChild(row);
    });
    table.appendChild(tbody);
    fragment.appendChild(table);
    
    container.innerHTML = '';
    container.appendChild(fragment);
}

// Promote User to Admin
async function promoteToAdmin(userId) {
    if (!confirm('Are you sure you want to promote this user to admin?')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/admin/promote/${userId}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${appState.token}`
            }
        });

        const data = await response.json();

        if (response.ok) {
            showMessage('User promoted to admin successfully', 'success');
            await loadAllUsers();
        } else {
            showMessage(data.message || data.error || 'Failed to promote user', 'error');
        }
    } catch (error) {
        showMessage('Network error: ' + error.message, 'error');
        console.error('Promote user error:', error);
    }
}

// Update User Handler
async function handleUpdateUser(e) {
    e.preventDefault();

    const updateData = {
        username: document.getElementById('updateUsername').value.trim() || appState.user,
        email: document.getElementById('updateEmail').value.trim(),
        password: document.getElementById('updatePassword').value
    };

    if (!updateData.email && !updateData.password && updateData.username === appState.user) {
        showMessage('Please fill in at least one field to update', 'error');
        return;
    }

    if (updateData.password && !validatePassword(updateData.password)) {
        showMessage('Password must contain uppercase, lowercase, number, and special character', 'error');
        return;
    }

    try {
        // Get current user's ID
        const userResponse = await fetch(`${API_BASE_URL}/users`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${appState.token}`
            }
        });

        if (!userResponse.ok) {
            showMessage('Failed to get user information', 'error');
            return;
        }

        const userData = await userResponse.json();
        const currentUser = userData.users.find(u => u.username === appState.user);
        
        if (!currentUser) {
            showMessage('User not found', 'error');
            return;
        }

        const response = await fetch(`${API_BASE_URL}/users/${currentUser.id}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${appState.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updateData)
        });

        if (response.ok) {
            appState.user = updateData.username;
            localStorage.setItem('user', appState.user);
            updateUIForLoggedInUser();
            showMessage('Profile updated successfully', 'success');
            document.getElementById('updateUserForm').reset();
        } else {
            const data = await response.json();
            showMessage(data.error || 'Failed to update profile', 'error');
        }
    } catch (error) {
        showMessage('Network error: ' + error.message, 'error');
        console.error('Update user error:', error);
    }
}

// Delete Account
async function deleteAccount() {
    showConfirmModal(
        'Delete Account',
        'Are you sure you want to delete your account? This action cannot be undone.',
        async () => {
            try {
                const userResponse = await fetch(`${API_BASE_URL}/users`, {
                    method: 'GET',
                    headers: {
                        'Authorization': `Bearer ${appState.token}`
                    }
                });

                if (!userResponse.ok) {
                    showMessage('Failed to get user information', 'error');
                    return;
                }

                const userData = await userResponse.json();
                const currentUser = userData.users.find(u => u.username === appState.user);
                
                if (!currentUser) {
                    showMessage('User not found', 'error');
                    return;
                }

                const response = await fetch(`${API_BASE_URL}/users/${currentUser.id}`, {
                    method: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${appState.token}`
                    }
                });

                if (response.ok) {
                    showMessage('Account deleted successfully', 'success');
                    setTimeout(() => handleLogout(), 1500);
                } else {
                    const data = await response.json();
                    showMessage(data.error || 'Failed to delete account', 'error');
                }
            } catch (error) {
                showMessage('Network error: ' + error.message, 'error');
                console.error('Delete account error:', error);
            }
        }
    );
}

// Logout Handler
function handleLogout() {
    appState.user = null;
    appState.token = null;
    appState.refreshToken = null;
    appState.isAdmin = false;

    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('user');
    localStorage.removeItem('isAdmin');

    updateUIForLoggedOutUser();
    showMessage('Logged out successfully', 'success');
}

// Message Display with debouncing
const messageQueue = [];
function showMessage(message, type = 'info') {
    const container = document.getElementById('messageContainer');
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.textContent = message;
    alert.setAttribute('role', type === 'error' ? 'alert' : 'status');

    container.appendChild(alert);

    // Auto-remove after 5 seconds
    const timeoutId = setTimeout(() => {
        alert.remove();
    }, 5000);

    // Allow manual dismissal
    alert.addEventListener('click', () => {
        clearTimeout(timeoutId);
        alert.remove();
    });
}

// Confirmation Modal
function showConfirmModal(title, message, onConfirm) {
    const modal = document.getElementById('confirmModal');
    document.getElementById('confirmTitle').textContent = title;
    document.getElementById('confirmMessage').textContent = message;
    modal.classList.add('show');
    modal.style.display = 'flex';

    const confirmBtn = document.getElementById('confirmBtn');
    const newConfirmBtn = confirmBtn.cloneNode(true);
    confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);

    newConfirmBtn.addEventListener('click', () => {
        closeModal();
        onConfirm();
    });

    // Focus management for accessibility
    newConfirmBtn.focus();
}

function closeModal() {
    const modal = document.getElementById('confirmModal');
    modal.classList.remove('show');
    modal.style.display = 'none';
}

// Utility Functions
function validatePassword(password) {
    const hasUpperCase = /[A-Z]/.test(password);
    const hasLowerCase = /[a-z]/.test(password);
    const hasNumber = /\d/.test(password);
    const hasSpecialChar = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password);
    return hasUpperCase && hasLowerCase && hasNumber && hasSpecialChar && password.length >= 8;
}

function adjustLayoutForMobile() {
    // Adjust layout for mobile if needed
    const container = document.querySelector('.container');
    if (window.innerWidth <= 768) {
        container?.classList.add('mobile');
    } else {
        container?.classList.remove('mobile');
    }
}

// Close modal when clicking outside
document.addEventListener('click', (e) => {
    const modal = document.getElementById('confirmModal');
    if (e.target === modal) {
        closeModal();
    }
});

// Performance: Use Intersection Observer for lazy loading
if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Load content when visible
                observer.unobserve(entry.target);
            }
        });
    });
}

