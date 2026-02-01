/**
 * NetROS Frontend Application
 */

// Risk score calculation helper
function calculateRiskScore(likelihood, consequence) {
    const score = likelihood * consequence;
    let level, color;

    if (score <= 4) {
        level = 'Akseptabel';
        color = 'green';
    } else if (score <= 9) {
        level = 'Lav';
        color = 'yellow';
    } else if (score <= 16) {
        level = 'Middels';
        color = 'orange';
    } else {
        level = 'Høy';
        color = 'red';
    }

    return { score, level, color };
}

// Get color class for risk level
function getRiskColorClass(color) {
    const classes = {
        'green': 'bg-green-100 text-green-800',
        'yellow': 'bg-yellow-100 text-yellow-800',
        'orange': 'bg-orange-100 text-orange-800',
        'red': 'bg-red-100 text-red-800'
    };
    return classes[color] || 'bg-gray-100 text-gray-800';
}

// Format date for display (Norwegian format)
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('nb-NO', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
    });
}

// Format datetime for display
function formatDateTime(dateTimeString) {
    if (!dateTimeString) return '-';
    const date = new Date(dateTimeString);
    return date.toLocaleDateString('nb-NO', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Show toast notification
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    const bgColor = {
        'success': 'bg-green-500',
        'error': 'bg-red-500',
        'warning': 'bg-yellow-500',
        'info': 'bg-blue-500'
    }[type] || 'bg-blue-500';

    toast.className = `fixed bottom-4 right-4 ${bgColor} text-white px-6 py-3 rounded-lg shadow-lg z-50 transition-opacity duration-300`;
    toast.textContent = message;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('opacity-0');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Confirm dialog helper
function confirmAction(message) {
    return confirm(message);
}

// API helper functions
async function apiGet(url) {
    const response = await fetch(url, {
        headers: {
            'Accept': 'application/json'
        }
    });

    if (!response.ok) {
        if (response.status === 401) {
            window.location.href = '/login';
            return null;
        }
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
}

async function apiPost(url, data) {
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        body: JSON.stringify(data)
    });

    if (!response.ok) {
        if (response.status === 401) {
            window.location.href = '/login';
            return null;
        }
        const error = await response.json();
        throw new Error(error.detail || 'Request failed');
    }

    return response.json();
}

async function apiPatch(url, data) {
    const response = await fetch(url, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        body: JSON.stringify(data)
    });

    if (!response.ok) {
        if (response.status === 401) {
            window.location.href = '/login';
            return null;
        }
        const error = await response.json();
        throw new Error(error.detail || 'Request failed');
    }

    return response.json();
}

async function apiDelete(url) {
    const response = await fetch(url, {
        method: 'DELETE',
        headers: {
            'Accept': 'application/json'
        }
    });

    if (!response.ok) {
        if (response.status === 401) {
            window.location.href = '/login';
            return null;
        }
        if (response.status !== 204) {
            const error = await response.json();
            throw new Error(error.detail || 'Request failed');
        }
    }

    return true;
}

// Initialize HTMX event handlers
document.addEventListener('DOMContentLoaded', function() {
    // Handle 401 responses globally
    document.body.addEventListener('htmx:responseError', function(evt) {
        if (evt.detail.xhr.status === 401) {
            window.location.href = '/login';
        }
    });

    // Show loading indicators
    document.body.addEventListener('htmx:beforeRequest', function(evt) {
        const indicator = evt.detail.elt.querySelector('.htmx-indicator');
        if (indicator) {
            indicator.style.display = 'inline-block';
        }
    });

    document.body.addEventListener('htmx:afterRequest', function(evt) {
        const indicator = evt.detail.elt.querySelector('.htmx-indicator');
        if (indicator) {
            indicator.style.display = 'none';
        }
    });
});

// Risk matrix rendering helper
function renderRiskMatrix(containerId, matrixData, clickHandler = null) {
    const container = document.getElementById(containerId);
    if (!container || !matrixData) return;

    const getColor = (l, c) => {
        const score = l * c;
        if (score <= 4) return 'bg-green-200';
        if (score <= 9) return 'bg-yellow-200';
        if (score <= 16) return 'bg-orange-200';
        return 'bg-red-300';
    };

    let html = '<div class="flex">';
    html += '<div class="flex flex-col justify-around pr-2 text-xs text-gray-600">';
    ['SH', 'H', 'M', 'L', 'SL'].forEach(label => {
        html += `<span>${label}</span>`;
    });
    html += '</div>';
    html += '<div class="grid grid-cols-5 gap-1">';

    matrixData.cells.forEach((row, rowIdx) => {
        row.forEach((cell, colIdx) => {
            const count = cell.risk_count;
            const color = getColor(cell.likelihood, cell.consequence);
            const clickAttr = clickHandler ? `onclick="${clickHandler}(${cell.likelihood}, ${cell.consequence})"` : '';
            html += `
                <div class="w-12 h-12 ${color} border border-gray-300 flex items-center justify-center text-xs font-medium cursor-pointer hover:opacity-80"
                     title="${cell.likelihood} × ${cell.consequence} = ${cell.score}"
                     ${clickAttr}>
                    ${count > 0 ? count : ''}
                </div>
            `;
        });
    });

    html += '</div></div>';
    html += '<div class="flex mt-2 ml-8"><div class="grid grid-cols-5 gap-1 text-xs text-gray-600">';
    ['SL', 'L', 'M', 'H', 'SH'].forEach(label => {
        html += `<span class="w-12 text-center">${label}</span>`;
    });
    html += '</div></div>';
    html += '<div class="text-xs text-gray-500 text-center mt-1">Konsekvens</div>';

    container.innerHTML = html;
}

// Export for use in templates
window.NetROS = {
    calculateRiskScore,
    getRiskColorClass,
    formatDate,
    formatDateTime,
    showToast,
    confirmAction,
    apiGet,
    apiPost,
    apiPatch,
    apiDelete,
    renderRiskMatrix
};
