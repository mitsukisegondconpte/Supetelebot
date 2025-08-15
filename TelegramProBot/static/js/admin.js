/**
 * Administration JavaScript pour le Bot d'Échecs Professionnel
 * Gestion des interactions, AJAX et fonctionnalités temps réel
 */

// Configuration globale
const AdminApp = {
    version: '2.0.0',
    debug: true,
    endpoints: {
        stats: '/admin/api/realtime-stats',
        users: '/api/users',
        activities: '/api/activities',
        games: '/api/games',
        cleanup: '/admin/api/cleanup',
        blockUser: '/admin/api/block-user',
        systemInfo: '/admin/api/system-info'
    },
    intervals: {
        stats: null,
        heartbeat: null,
        performance: null
    },
    cache: {
        users: new Map(),
        games: new Map(),
        stats: {}
    },
    socket: null
};

// Initialisation de l'application
document.addEventListener('DOMContentLoaded', function() {
    console.log(`🚀 Admin Panel v${AdminApp.version} - Initialisation...`);
    
    // Initialiser les composants principaux
    initializeAdminPanel();
    initializeEventListeners();
    initializeWebSocket();
    startPeriodicUpdates();
    
    console.log('✅ Admin Panel initialisé avec succès');
});

/**
 * Initialisation du panneau d'administration
 */
function initializeAdminPanel() {
    // Vérifier la connexion à l'API
    checkApiConnection();
    
    // Initialiser les tooltips Bootstrap
    initializeTooltips();
    
    // Configurer les modals
    setupModals();
    
    // Initialiser les graphiques si Chart.js est disponible
    if (typeof Chart !== 'undefined') {
        initializeCharts();
    }
    
    // Détecter le mode sombre
    detectDarkMode();
}

/**
 * Configuration des event listeners
 */
function initializeEventListeners() {
    // Boutons de navigation
    setupNavigationButtons();
    
    // Formulaires de recherche et filtres
    setupSearchAndFilters();
    
    // Actions en lot
    setupBatchActions();
    
    // Raccourcis clavier
    setupKeyboardShortcuts();
    
    // Gestion des erreurs globales
    setupErrorHandling();
}

/**
 * Initialisation WebSocket pour le temps réel
 */
function initializeWebSocket() {
    if (typeof io !== 'undefined') {
        AdminApp.socket = io('/admin');
        
        AdminApp.socket.on('connect', function() {
            console.log('🔌 WebSocket connecté');
            updateConnectionStatus(true);
            showNotification('Connexion temps réel établie', 'success');
        });
        
        AdminApp.socket.on('disconnect', function() {
            console.log('🔌 WebSocket déconnecté');
            updateConnectionStatus(false);
            showNotification('Connexion temps réel perdue', 'warning');
        });
        
        // Événements spécifiques
        AdminApp.socket.on('stats_update', handleStatsUpdate);
        AdminApp.socket.on('live_activity', handleLiveActivity);
        AdminApp.socket.on('system_alert', handleSystemAlert);
        AdminApp.socket.on('user_update', handleUserUpdate);
        
    } else {
        console.warn('⚠️ Socket.IO non disponible - mode dégradé');
    }
}

/**
 * Démarrage des mises à jour périodiques
 */
function startPeriodicUpdates() {
    // Statistiques toutes les 30 secondes
    AdminApp.intervals.stats = setInterval(refreshStats, 30000);
    
    // Heartbeat toutes les 5 minutes
    AdminApp.intervals.heartbeat = setInterval(sendHeartbeat, 300000);
    
    // Performance système toutes les minutes
    AdminApp.intervals.performance = setInterval(updateSystemPerformance, 60000);
    
    // Nettoyage du cache toutes les 10 minutes
    setInterval(cleanCache, 600000);
}

/**
 * Vérification de la connexion API
 */
async function checkApiConnection() {
    try {
        const response = await fetch('/status');
        const data = await response.json();
        
        if (data.status === 'healthy') {
            updateApiStatus('healthy', `${data.users} utilisateurs`);
        } else {
            updateApiStatus('warning', 'API en mode dégradé');
        }
    } catch (error) {
        console.error('❌ Erreur connexion API:', error);
        updateApiStatus('error', 'API inaccessible');
    }
}

/**
 * Mise à jour du statut API dans l'interface
 */
function updateApiStatus(status, message) {
    const indicator = document.querySelector('.api-status-indicator');
    const text = document.querySelector('.api-status-text');
    
    if (indicator && text) {
        indicator.className = `api-status-indicator status-${status}`;
        text.textContent = message;
    }
}

/**
 * Mise à jour du statut de connexion WebSocket
 */
function updateConnectionStatus(connected) {
    const indicators = document.querySelectorAll('.connection-status');
    const texts = document.querySelectorAll('.connection-text');
    
    indicators.forEach(indicator => {
        indicator.className = connected ? 'connection-status online' : 'connection-status offline';
    });
    
    texts.forEach(text => {
        text.textContent = connected ? 'Connecté' : 'Déconnecté';
    });
}

/**
 * Actualisation des statistiques
 */
async function refreshStats() {
    try {
        const response = await fetch(AdminApp.endpoints.stats);
        const stats = await response.json();
        
        updateDashboardStats(stats);
        AdminApp.cache.stats = stats;
        
        // Émettre via WebSocket si disponible
        if (AdminApp.socket && AdminApp.socket.connected) {
            AdminApp.socket.emit('stats_request');
        }
        
    } catch (error) {
        console.error('❌ Erreur actualisation stats:', error);
        showNotification('Erreur lors de l\'actualisation', 'error');
    }
}

/**
 * Mise à jour des statistiques du dashboard
 */
function updateDashboardStats(stats) {
    const mappings = {
        'total-users': stats.total_users,
        'active-users': stats.active_users,
        'active-games': stats.active_games,
        'total-games': stats.total_games,
        'total-moves': stats.total_moves,
        'today-activities': stats.today_activities
    };
    
    Object.entries(mappings).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element && value !== undefined) {
            animateCounter(element, parseInt(value) || 0);
        }
    });
    
    // Mettre à jour l'horodatage
    const lastUpdate = document.getElementById('last-update');
    if (lastUpdate) {
        lastUpdate.textContent = new Date().toLocaleTimeString('fr-FR');
    }
}

/**
 * Animation des compteurs
 */
function animateCounter(element, targetValue) {
    const currentValue = parseInt(element.textContent) || 0;
    const increment = Math.ceil(Math.abs(targetValue - currentValue) / 10);
    let current = currentValue;
    
    const timer = setInterval(() => {
        if (current < targetValue) {
            current = Math.min(current + increment, targetValue);
        } else if (current > targetValue) {
            current = Math.max(current - increment, targetValue);
        }
        
        element.textContent = current.toLocaleString('fr-FR');
        
        if (current === targetValue) {
            clearInterval(timer);
            element.style.transform = 'scale(1.1)';
            setTimeout(() => {
                element.style.transform = 'scale(1)';
            }, 200);
        }
    }, 50);
}

/**
 * Gestion des activités en temps réel
 */
function handleStatsUpdate(data) {
    updateDashboardStats(data);
    console.log('📊 Stats mises à jour:', data);
}

function handleLiveActivity(activity) {
    addActivityToStream(activity);
    updateActivityCounter();
    console.log('🔴 Activité live:', activity);
}

function handleSystemAlert(alert) {
    showSystemAlert(alert);
    console.log('⚠️ Alerte système:', alert);
}

function handleUserUpdate(userData) {
    updateUserInCache(userData);
    console.log('👤 Mise à jour utilisateur:', userData);
}

/**
 * Ajout d'activité au flux temps réel
 */
function addActivityToStream(activity) {
    const stream = document.getElementById('activity-stream');
    if (!stream) return;
    
    // Supprimer le message d'attente si présent
    const emptyState = stream.querySelector('.empty-state');
    if (emptyState) {
        emptyState.remove();
    }
    
    const activityElement = createActivityElement(activity);
    stream.insertBefore(activityElement, stream.firstChild);
    
    // Animer l'entrée
    requestAnimationFrame(() => {
        activityElement.style.transform = 'translateX(0)';
        activityElement.style.opacity = '1';
    });
    
    // Limiter le nombre d'activités affichées
    const activities = stream.querySelectorAll('.activity-item');
    if (activities.length > 50) {
        activities[activities.length - 1].remove();
    }
    
    // Marquer comme nouvelle pendant 3 secondes
    setTimeout(() => {
        activityElement.classList.remove('new');
    }, 3000);
}

/**
 * Création d'un élément d'activité
 */
function createActivityElement(activity) {
    const div = document.createElement('div');
    div.className = 'activity-item new';
    div.style.transform = 'translateX(-100%)';
    div.style.opacity = '0';
    div.style.transition = 'all 0.3s ease';
    
    const timestamp = new Date().toLocaleTimeString('fr-FR');
    const typeIcon = getActivityIcon(activity.type);
    const typeBadge = getActivityBadge(activity.type);
    
    div.innerHTML = `
        <div class="d-flex justify-content-between align-items-start">
            <div class="flex-grow-1">
                <div class="d-flex align-items-center mb-1">
                    <i class="${typeIcon} me-2 text-primary"></i>
                    <strong>${escapeHtml(activity.user_name || 'Système')}</strong>
                    ${typeBadge}
                </div>
                <div class="activity-description text-muted small">
                    ${escapeHtml(activity.description || 'Activité sans description')}
                </div>
            </div>
            <small class="text-muted ms-3">${timestamp}</small>
        </div>
    `;
    
    return div;
}

/**
 * Obtenir l'icône pour un type d'activité
 */
function getActivityIcon(type) {
    const icons = {
        'command': 'fas fa-terminal',
        'move': 'fas fa-chess-pawn',
        'game_created': 'fas fa-plus-circle',
        'game_finished': 'fas fa-flag-checkered',
        'export': 'fas fa-download',
        'webhook': 'fas fa-webhook',
        'login': 'fas fa-sign-in-alt',
        'error': 'fas fa-exclamation-triangle',
        'default': 'fas fa-info-circle'
    };
    return icons[type] || icons.default;
}

/**
 * Obtenir le badge pour un type d'activité
 */
function getActivityBadge(type) {
    const badges = {
        'command': '<span class="badge bg-primary ms-2">CMD</span>',
        'move': '<span class="badge bg-success ms-2">MOVE</span>',
        'game_created': '<span class="badge bg-info ms-2">NEW</span>',
        'game_finished': '<span class="badge bg-warning ms-2">END</span>',
        'export': '<span class="badge bg-secondary ms-2">EXPORT</span>',
        'webhook': '<span class="badge bg-dark ms-2">HOOK</span>',
        'login': '<span class="badge bg-success ms-2">LOGIN</span>',
        'error': '<span class="badge bg-danger ms-2">ERROR</span>'
    };
    return badges[type] || '<span class="badge bg-light text-dark ms-2">INFO</span>';
}

/**
 * Affichage d'alerte système
 */
function showSystemAlert(alert) {
    const container = document.getElementById('system-alerts');
    if (!container) return;
    
    const alertElement = document.createElement('div');
    alertElement.className = `alert alert-${alert.severity || 'info'} alert-dismissible fade show`;
    alertElement.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="fas fa-bell me-2"></i>
            <div class="flex-grow-1">
                <strong>${new Date().toLocaleTimeString('fr-FR')}</strong> - ${escapeHtml(alert.message)}
            </div>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    container.insertBefore(alertElement, container.firstChild);
    
    // Auto-dismiss après 10 secondes pour les alertes info
    if (alert.severity === 'info') {
        setTimeout(() => {
            if (alertElement.parentNode) {
                alertElement.remove();
            }
        }, 10000);
    }
    
    // Limiter le nombre d'alertes
    const alerts = container.querySelectorAll('.alert');
    if (alerts.length > 10) {
        alerts[alerts.length - 1].remove();
    }
}

/**
 * Notifications toast
 */
function showNotification(message, type = 'info', duration = 5000) {
    // Créer le conteneur de notifications s'il n'existe pas
    let container = document.getElementById('notification-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-container';
        container.className = 'position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }
    
    const notification = document.createElement('div');
    notification.className = `toast align-items-center text-white bg-${type} border-0 show`;
    notification.setAttribute('role', 'alert');
    
    notification.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="fas fa-${getNotificationIcon(type)} me-2"></i>
                ${escapeHtml(message)}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    container.appendChild(notification);
    
    // Auto-dismiss
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, duration);
}

/**
 * Icônes pour les notifications
 */
function getNotificationIcon(type) {
    const icons = {
        'success': 'check-circle',
        'error': 'exclamation-triangle',
        'warning': 'exclamation-circle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

/**
 * Mise à jour des performances système
 */
async function updateSystemPerformance() {
    try {
        const response = await fetch(AdminApp.endpoints.systemInfo);
        const data = await response.json();
        
        updateSystemMetrics(data);
        
    } catch (error) {
        console.log('ℹ️ Informations système limitées');
    }
}

/**
 * Mise à jour des métriques système dans l'interface
 */
function updateSystemMetrics(data) {
    const metricsContainer = document.getElementById('system-metrics');
    if (!metricsContainer) return;
    
    const metrics = {
        'CPU': data.cpu_percent ? `${data.cpu_percent.toFixed(1)}%` : 'N/A',
        'RAM': data.memory_percent ? `${data.memory_percent.toFixed(1)}%` : 'N/A',
        'Disque': data.disk_percent ? `${data.disk_percent.toFixed(1)}%` : 'N/A'
    };
    
    let html = '';
    Object.entries(metrics).forEach(([label, value]) => {
        const percentage = parseFloat(value) || 0;
        const colorClass = percentage > 80 ? 'danger' : percentage > 60 ? 'warning' : 'success';
        
        html += `
            <div class="col-md-4">
                <div class="text-center">
                    <div class="h4 text-${colorClass}">${value}</div>
                    <div class="text-muted">${label}</div>
                </div>
            </div>
        `;
    });
    
    metricsContainer.innerHTML = `<div class="row">${html}</div>`;
}

/**
 * Configuration des tooltips Bootstrap
 */
function initializeTooltips() {
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}

/**
 * Configuration des modals
 */
function setupModals() {
    // Nettoyage automatique des modals au fermeture
    document.addEventListener('hidden.bs.modal', function (event) {
        const modal = event.target;
        const content = modal.querySelector('.modal-body');
        if (content && content.id.includes('dynamic')) {
            content.innerHTML = '';
        }
    });
}

/**
 * Détection du mode sombre
 */
function detectDarkMode() {
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        document.body.classList.add('dark-mode');
    }
    
    // Écouter les changements
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
        document.body.classList.toggle('dark-mode', e.matches);
    });
}

/**
 * Configuration des boutons de navigation
 */
function setupNavigationButtons() {
    // Bouton actualiser
    const refreshButtons = document.querySelectorAll('[data-action="refresh"]');
    refreshButtons.forEach(button => {
        button.addEventListener('click', function() {
            refreshStats();
            showNotification('Données actualisées', 'success');
        });
    });
    
    // Boutons d'export
    const exportButtons = document.querySelectorAll('[data-action="export"]');
    exportButtons.forEach(button => {
        button.addEventListener('click', function() {
            const type = this.dataset.exportType || 'json';
            exportData(type);
        });
    });
}

/**
 * Configuration de la recherche et des filtres
 */
function setupSearchAndFilters() {
    // Recherche universelle
    const searchInputs = document.querySelectorAll('[data-search]');
    searchInputs.forEach(input => {
        let timeout;
        input.addEventListener('input', function() {
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                performSearch(this.value, this.dataset.search);
            }, 300);
        });
    });
    
    // Filtres
    const filterSelects = document.querySelectorAll('[data-filter]');
    filterSelects.forEach(select => {
        select.addEventListener('change', function() {
            applyFilter(this.value, this.dataset.filter);
        });
    });
}

/**
 * Configuration des actions en lot
 */
function setupBatchActions() {
    // Sélection multiple
    const masterCheckbox = document.getElementById('select-all');
    if (masterCheckbox) {
        masterCheckbox.addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('.item-checkbox');
            checkboxes.forEach(cb => cb.checked = this.checked);
            updateBatchActionsVisibility();
        });
    }
    
    // Checkboxes individuelles
    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('item-checkbox')) {
            updateBatchActionsVisibility();
        }
    });
}

/**
 * Configuration des raccourcis clavier
 */
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + R : Actualiser
        if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
            e.preventDefault();
            refreshStats();
        }
        
        // Échap : Fermer les modals
        if (e.key === 'Escape') {
            const modals = document.querySelectorAll('.modal.show');
            modals.forEach(modal => {
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) bsModal.hide();
            });
        }
        
        // Ctrl/Cmd + K : Focus recherche
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.querySelector('[data-search]');
            if (searchInput) searchInput.focus();
        }
    });
}

/**
 * Gestion des erreurs globales
 */
function setupErrorHandling() {
    window.addEventListener('error', function(e) {
        console.error('❌ Erreur JavaScript:', e);
        showNotification('Une erreur s\'est produite', 'error');
    });
    
    window.addEventListener('unhandledrejection', function(e) {
        console.error('❌ Promise rejetée:', e);
        showNotification('Erreur de connexion', 'error');
    });
}

/**
 * Utilitaires
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatDuration(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const remainingSeconds = seconds % 60;
    
    if (hours > 0) {
        return `${hours}h ${minutes}m`;
    } else if (minutes > 0) {
        return `${minutes}m ${remainingSeconds}s`;
    } else {
        return `${remainingSeconds}s`;
    }
}

/**
 * Nettoyage périodique du cache
 */
function cleanCache() {
    const now = Date.now();
    const maxAge = 10 * 60 * 1000; // 10 minutes
    
    // Nettoyer le cache des utilisateurs
    AdminApp.cache.users.forEach((value, key) => {
        if (now - value.timestamp > maxAge) {
            AdminApp.cache.users.delete(key);
        }
    });
    
    // Nettoyer le cache des parties
    AdminApp.cache.games.forEach((value, key) => {
        if (now - value.timestamp > maxAge) {
            AdminApp.cache.games.delete(key);
        }
    });
    
    console.log('🧹 Cache nettoyé');
}

/**
 * Heartbeat pour maintenir la connexion
 */
function sendHeartbeat() {
    if (AdminApp.socket && AdminApp.socket.connected) {
        AdminApp.socket.emit('heartbeat', {
            timestamp: Date.now(),
            version: AdminApp.version
        });
    }
}

/**
 * Nettoyage à la fermeture de la page
 */
window.addEventListener('beforeunload', function() {
    // Nettoyer les intervalles
    Object.values(AdminApp.intervals).forEach(interval => {
        if (interval) clearInterval(interval);
    });
    
    // Fermer la connexion WebSocket
    if (AdminApp.socket) {
        AdminApp.socket.disconnect();
    }
    
    console.log('🧹 Nettoyage effectué avant fermeture');
});

// Export pour utilisation globale
window.AdminApp = AdminApp;
window.showNotification = showNotification;
window.refreshStats = refreshStats;

console.log('📱 AdminJS v' + AdminApp.version + ' chargé');
