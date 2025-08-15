/**
 * Module de monitoring temps réel pour le Bot d'Échecs Professionnel
 * Gestion avancée des WebSockets, graphiques dynamiques et données live
 */

// Configuration du module temps réel
const RealtimeMonitor = {
    version: '1.0.0',
    socket: null,
    charts: {},
    config: {
        maxDataPoints: 50,
        updateInterval: 5000,
        chartAnimationDuration: 750,
        alertTimeout: 10000
    },
    data: {
        activities: [],
        stats: {},
        users: new Map(),
        performance: {}
    },
    state: {
        connected: false,
        monitoring: true,
        chartsPaused: false,
        lastUpdate: null
    },
    colors: {
        primary: 'rgb(102, 126, 234)',
        success: 'rgb(40, 167, 69)',
        warning: 'rgb(255, 193, 7)',
        danger: 'rgb(220, 53, 69)',
        info: 'rgb(23, 162, 184)',
        gradient: {
            primary: 'rgba(102, 126, 234, 0.1)',
            success: 'rgba(40, 167, 69, 0.1)',
            warning: 'rgba(255, 193, 7, 0.1)',
            danger: 'rgba(220, 53, 69, 0.1)',
            info: 'rgba(23, 162, 184, 0.1)'
        }
    }
};

/**
 * Initialisation du monitoring temps réel
 */
function initializeRealtimeMonitoring() {
    console.log(`🔴 Monitoring temps réel v${RealtimeMonitor.version} - Initialisation...`);
    
    // Initialiser la connexion WebSocket
    setupWebSocketConnection();
    
    // Initialiser les graphiques
    initializeRealtimeCharts();
    
    // Configurer les contrôles
    setupMonitoringControls();
    
    // Démarrer la collecte de données
    startDataCollection();
    
    // Gestionnaires d'événements
    setupRealtimeEventHandlers();
    
    console.log('✅ Monitoring temps réel initialisé');
}

/**
 * Configuration de la connexion WebSocket
 */
function setupWebSocketConnection() {
    if (typeof io === 'undefined') {
        console.error('❌ Socket.IO non disponible');
        return;
    }
    
    RealtimeMonitor.socket = io('/admin', {
        transports: ['websocket', 'polling'],
        timeout: 20000,
        forceNew: true
    });
    
    // Événements de connexion
    RealtimeMonitor.socket.on('connect', handleRealtimeConnect);
    RealtimeMonitor.socket.on('disconnect', handleRealtimeDisconnect);
    RealtimeMonitor.socket.on('reconnect', handleRealtimeReconnect);
    RealtimeMonitor.socket.on('error', handleRealtimeError);
    
    // Événements de données
    RealtimeMonitor.socket.on('stats_update', handleRealtimeStatsUpdate);
    RealtimeMonitor.socket.on('live_activity', handleRealtimeLiveActivity);
    RealtimeMonitor.socket.on('system_alert', handleRealtimeSystemAlert);
    RealtimeMonitor.socket.on('user_activity', handleRealtimeUserActivity);
    RealtimeMonitor.socket.on('webhook_event', handleRealtimeWebhookEvent);
    RealtimeMonitor.socket.on('move_played', handleRealtimeMoveEvent);
    RealtimeMonitor.socket.on('new_game', handleRealtimeGameEvent);
    
    // Événements personnalisés
    RealtimeMonitor.socket.on('performance_update', handlePerformanceUpdate);
    RealtimeMonitor.socket.on('alert_batch', handleAlertBatch);
}

/**
 * Gestionnaires d'événements WebSocket
 */
function handleRealtimeConnect() {
    console.log('🟢 WebSocket connecté');
    RealtimeMonitor.state.connected = true;
    updateConnectionIndicator(true);
    
    // Demander les données initiales
    RealtimeMonitor.socket.emit('request_stats');
    RealtimeMonitor.socket.emit('request_active_games');
    
    showRealtimeNotification('Connexion temps réel établie', 'success');
}

function handleRealtimeDisconnect(reason) {
    console.log('🔴 WebSocket déconnecté:', reason);
    RealtimeMonitor.state.connected = false;
    updateConnectionIndicator(false);
    
    showRealtimeNotification('Connexion temps réel perdue', 'warning');
    
    // Tentative de reconnexion automatique
    setTimeout(() => {
        if (!RealtimeMonitor.state.connected) {
            console.log('🔄 Tentative de reconnexion...');
            RealtimeMonitor.socket.connect();
        }
    }, 5000);
}

function handleRealtimeReconnect() {
    console.log('🟡 Reconnexion WebSocket réussie');
    showRealtimeNotification('Reconnexion réussie', 'success');
}

function handleRealtimeError(error) {
    console.error('❌ Erreur WebSocket:', error);
    showRealtimeNotification('Erreur de connexion temps réel', 'error');
}

/**
 * Gestionnaires de données temps réel
 */
function handleRealtimeStatsUpdate(data) {
    if (!RealtimeMonitor.state.monitoring) return;
    
    RealtimeMonitor.data.stats = data;
    RealtimeMonitor.state.lastUpdate = new Date();
    
    updateRealtimeCharts(data);
    updateLiveMetrics(data);
    
    console.log('📊 Stats temps réel mises à jour');
}

function handleRealtimeLiveActivity(activity) {
    if (!RealtimeMonitor.state.monitoring) return;
    
    RealtimeMonitor.data.activities.unshift(activity);
    
    // Limiter le nombre d'activités en mémoire
    if (RealtimeMonitor.data.activities.length > RealtimeMonitor.config.maxDataPoints) {
        RealtimeMonitor.data.activities = RealtimeMonitor.data.activities.slice(0, RealtimeMonitor.config.maxDataPoints);
    }
    
    addActivityToRealtimeStream(activity);
    updateActivityChart(activity);
    
    console.log('🔴 Activité live reçue:', activity.type);
}

function handleRealtimeSystemAlert(alert) {
    addSystemAlert(alert);
    
    // Alerte critique - notification système
    if (alert.severity === 'danger') {
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification('⚠️ Alerte Système Critique', {
                body: alert.message,
                icon: '/static/favicon.ico'
            });
        }
    }
    
    console.log(`⚠️ Alerte système [${alert.severity}]:`, alert.message);
}

function handleRealtimeUserActivity(data) {
    RealtimeMonitor.data.users.set(data.user_id, {
        ...data,
        timestamp: Date.now()
    });
    
    updateActiveUsersList();
    console.log('👤 Activité utilisateur:', data.user_id);
}

function handleRealtimeWebhookEvent(data) {
    addWebhookEventToStream(data);
    incrementWebhookCounter();
    console.log('🔗 Événement webhook:', data.update_id);
}

function handleRealtimeMoveEvent(data) {
    addMoveEventToStream(data);
    updateGameActivityChart(data);
    console.log('♟️ Coup joué:', data.move);
}

function handleRealtimeGameEvent(data) {
    addGameEventToStream(data);
    updateGameCounter();
    console.log('🆕 Nouvelle partie:', data.game_id);
}

function handlePerformanceUpdate(data) {
    RealtimeMonitor.data.performance = data;
    updatePerformanceCharts(data);
    console.log('📈 Performance mise à jour');
}

function handleAlertBatch(alerts) {
    alerts.forEach(alert => addSystemAlert(alert));
    console.log(`📢 Lot d'alertes reçu: ${alerts.length} alertes`);
}

/**
 * Initialisation des graphiques temps réel
 */
function initializeRealtimeCharts() {
    if (typeof Chart === 'undefined') {
        console.warn('⚠️ Chart.js non disponible - graphiques désactivés');
        return;
    }
    
    // Configuration globale des graphiques
    Chart.defaults.color = '#6c757d';
    Chart.defaults.borderColor = '#dee2e6';
    Chart.defaults.font.family = 'Segoe UI, system-ui, sans-serif';
    Chart.defaults.animation.duration = RealtimeMonitor.config.chartAnimationDuration;
    
    // Graphique d'activité temps réel
    initializeActivityChart();
    
    // Graphique de performance
    initializePerformanceChart();
    
    // Graphique des utilisateurs actifs
    initializeUsersChart();
    
    // Graphique des parties
    initializeGamesChart();
    
    console.log('📊 Graphiques temps réel initialisés');
}

/**
 * Graphique d'activité principal
 */
function initializeActivityChart() {
    const ctx = document.getElementById('realtimeChart');
    if (!ctx) return;
    
    RealtimeMonitor.charts.activity = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Activités',
                    data: [],
                    borderColor: RealtimeMonitor.colors.primary,
                    backgroundColor: RealtimeMonitor.colors.gradient.primary,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 3,
                    pointHoverRadius: 6
                },
                {
                    label: 'Parties',
                    data: [],
                    borderColor: RealtimeMonitor.colors.success,
                    backgroundColor: RealtimeMonitor.colors.gradient.success,
                    fill: false,
                    tension: 0.4,
                    pointRadius: 3,
                    pointHoverRadius: 6
                },
                {
                    label: 'Utilisateurs',
                    data: [],
                    borderColor: RealtimeMonitor.colors.warning,
                    backgroundColor: RealtimeMonitor.colors.gradient.warning,
                    fill: false,
                    tension: 0.4,
                    pointRadius: 3,
                    pointHoverRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    position: 'top'
                },
                title: {
                    display: true,
                    text: 'Activité Temps Réel'
                },
                tooltip: {
                    callbacks: {
                        title: function(context) {
                            return 'Heure: ' + context[0].label;
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Temps'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Nombre'
                    },
                    beginAtZero: true
                }
            }
        }
    });
}

/**
 * Graphique de performance système
 */
function initializePerformanceChart() {
    const ctx = document.getElementById('performanceChart');
    if (!ctx) return;
    
    RealtimeMonitor.charts.performance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['CPU', 'Mémoire', 'Disque', 'Disponible'],
            datasets: [{
                data: [0, 0, 0, 100],
                backgroundColor: [
                    RealtimeMonitor.colors.danger,
                    RealtimeMonitor.colors.warning,
                    RealtimeMonitor.colors.info,
                    RealtimeMonitor.colors.success
                ],
                borderWidth: 0,
                cutout: '70%'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                },
                title: {
                    display: true,
                    text: 'Performance Système'
                }
            }
        }
    });
}

/**
 * Graphique des utilisateurs actifs
 */
function initializeUsersChart() {
    const ctx = document.getElementById('usersChart');
    if (!ctx) return;
    
    RealtimeMonitor.charts.users = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Actifs', 'Récents', 'Inactifs'],
            datasets: [{
                label: 'Utilisateurs',
                data: [0, 0, 0],
                backgroundColor: [
                    RealtimeMonitor.colors.success,
                    RealtimeMonitor.colors.warning,
                    RealtimeMonitor.colors.info
                ],
                borderRadius: 8,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: 'Répartition Utilisateurs'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

/**
 * Graphique des parties
 */
function initializeGamesChart() {
    const ctx = document.getElementById('gamesChart');
    if (!ctx) return;
    
    RealtimeMonitor.charts.games = new Chart(ctx, {
        type: 'polarArea',
        data: {
            labels: ['Actives', 'Terminées', 'Abandonnées'],
            datasets: [{
                data: [0, 0, 0],
                backgroundColor: [
                    RealtimeMonitor.colors.gradient.success,
                    RealtimeMonitor.colors.gradient.primary,
                    RealtimeMonitor.colors.gradient.warning
                ],
                borderColor: [
                    RealtimeMonitor.colors.success,
                    RealtimeMonitor.colors.primary,
                    RealtimeMonitor.colors.warning
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                },
                title: {
                    display: true,
                    text: 'État des Parties'
                }
            }
        }
    });
}

/**
 * Mise à jour des graphiques temps réel
 */
function updateRealtimeCharts(data) {
    if (RealtimeMonitor.state.chartsPaused) return;
    
    const timestamp = new Date().toLocaleTimeString('fr-FR', { 
        hour: '2-digit', 
        minute: '2-digit', 
        second: '2-digit' 
    });
    
    // Graphique d'activité principal
    if (RealtimeMonitor.charts.activity) {
        const chart = RealtimeMonitor.charts.activity;
        
        chart.data.labels.push(timestamp);
        chart.data.datasets[0].data.push(data.activities_last_minute || 0);
        chart.data.datasets[1].data.push(data.active_games || 0);
        chart.data.datasets[2].data.push(data.active_users_5min || 0);
        
        // Limiter les points de données
        if (chart.data.labels.length > RealtimeMonitor.config.maxDataPoints) {
            chart.data.labels.shift();
            chart.data.datasets.forEach(dataset => dataset.data.shift());
        }
        
        chart.update('none');
    }
    
    // Graphique des utilisateurs
    if (RealtimeMonitor.charts.users && data.user_breakdown) {
        const chart = RealtimeMonitor.charts.users;
        chart.data.datasets[0].data = [
            data.user_breakdown.active || 0,
            data.user_breakdown.recent || 0,
            data.user_breakdown.inactive || 0
        ];
        chart.update('none');
    }
    
    // Graphique des parties
    if (RealtimeMonitor.charts.games && data.game_breakdown) {
        const chart = RealtimeMonitor.charts.games;
        chart.data.datasets[0].data = [
            data.game_breakdown.active || 0,
            data.game_breakdown.finished || 0,
            data.game_breakdown.abandoned || 0
        ];
        chart.update('none');
    }
}

/**
 * Mise à jour des métriques en temps réel
 */
function updateLiveMetrics(data) {
    const metrics = {
        'live-users': data.active_users || 0,
        'live-games': data.active_games || 0,
        'live-moves': data.moves_per_minute || 0,
        'live-commands': data.commands_per_minute || 0,
        'response-time': `${data.avg_response_time || 0}ms`,
        'success-rate': `${(data.success_rate || 100).toFixed(1)}%`
    };
    
    Object.entries(metrics).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) {
            updateMetricValue(element, value);
        }
    });
}

/**
 * Animation de mise à jour des métriques
 */
function updateMetricValue(element, newValue) {
    const isNumeric = !isNaN(parseFloat(newValue));
    
    if (isNumeric) {
        const currentValue = parseFloat(element.textContent) || 0;
        const targetValue = parseFloat(newValue);
        
        animateMetricCounter(element, currentValue, targetValue);
    } else {
        element.textContent = newValue;
        
        // Animation de pulsation
        element.style.transform = 'scale(1.1)';
        setTimeout(() => {
            element.style.transform = 'scale(1)';
        }, 200);
    }
}

/**
 * Animation des compteurs numériques
 */
function animateMetricCounter(element, from, to) {
    const duration = 1000;
    const startTime = performance.now();
    
    function animate(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        const easeOutQuart = 1 - Math.pow(1 - progress, 4);
        const current = from + (to - from) * easeOutQuart;
        
        element.textContent = Math.round(current).toLocaleString('fr-FR');
        
        if (progress < 1) {
            requestAnimationFrame(animate);
        }
    }
    
    requestAnimationFrame(animate);
}

/**
 * Ajout d'activité au flux temps réel
 */
function addActivityToRealtimeStream(activity) {
    const stream = document.getElementById('activity-stream');
    if (!stream) return;
    
    // Supprimer le message vide
    const emptyMessage = stream.querySelector('.empty-message');
    if (emptyMessage) emptyMessage.remove();
    
    const element = createRealtimeActivityElement(activity);
    stream.insertBefore(element, stream.firstChild);
    
    // Animation d'entrée
    requestAnimationFrame(() => {
        element.style.transform = 'translateX(0)';
        element.style.opacity = '1';
    });
    
    // Limiter le nombre d'activités affichées
    const activities = stream.querySelectorAll('.realtime-activity');
    if (activities.length > 50) {
        activities[activities.length - 1].remove();
    }
    
    // Auto-scroll si nécessaire
    if (stream.scrollTop < 100) {
        stream.scrollTop = 0;
    }
    
    updateActivityCounter();
}

/**
 * Création d'un élément d'activité temps réel
 */
function createRealtimeActivityElement(activity) {
    const element = document.createElement('div');
    element.className = 'realtime-activity live-activity new';
    element.style.transform = 'translateX(-100%)';
    element.style.opacity = '0';
    element.style.transition = 'all 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
    
    const timestamp = new Date().toLocaleTimeString('fr-FR');
    const typeColor = getActivityTypeColor(activity.type);
    const typeIcon = getRealtimeActivityIcon(activity.type);
    
    element.innerHTML = `
        <div class="d-flex align-items-start">
            <div class="activity-icon me-3">
                <i class="${typeIcon}" style="color: ${typeColor}"></i>
            </div>
            <div class="flex-grow-1">
                <div class="d-flex justify-content-between align-items-center mb-1">
                    <strong class="user-name">${escapeHtml(activity.user_name || 'Système')}</strong>
                    <span class="activity-type badge" style="background-color: ${typeColor}">
                        ${activity.type.toUpperCase()}
                    </span>
                </div>
                <div class="activity-description small text-muted">
                    ${escapeHtml(activity.description)}
                </div>
                <div class="activity-meta small text-muted mt-1">
                    <i class="fas fa-clock me-1"></i>${timestamp}
                    ${activity.data ? `<span class="ms-2"><i class="fas fa-info-circle me-1"></i>Données supplémentaires</span>` : ''}
                </div>
            </div>
        </div>
    `;
    
    // Marquer comme nouvelle pendant 5 secondes
    setTimeout(() => {
        element.classList.remove('new');
    }, 5000);
    
    // Ajouter gestionnaire de clic pour détails
    element.addEventListener('click', () => showActivityDetails(activity));
    
    return element;
}

/**
 * Obtenir la couleur d'un type d'activité
 */
function getActivityTypeColor(type) {
    const colors = {
        'command': RealtimeMonitor.colors.primary,
        'move': RealtimeMonitor.colors.success,
        'game_created': RealtimeMonitor.colors.info,
        'game_finished': RealtimeMonitor.colors.warning,
        'export': RealtimeMonitor.colors.info,
        'webhook': RealtimeMonitor.colors.dark,
        'error': RealtimeMonitor.colors.danger,
        'login': RealtimeMonitor.colors.success
    };
    return colors[type] || RealtimeMonitor.colors.info;
}

/**
 * Obtenir l'icône d'un type d'activité
 */
function getRealtimeActivityIcon(type) {
    const icons = {
        'command': 'fas fa-terminal',
        'move': 'fas fa-chess-pawn',
        'game_created': 'fas fa-plus-circle',
        'game_finished': 'fas fa-flag-checkered',
        'export': 'fas fa-download',
        'webhook': 'fas fa-exchange-alt',
        'error': 'fas fa-exclamation-triangle',
        'login': 'fas fa-sign-in-alt'
    };
    return icons[type] || 'fas fa-info-circle';
}

/**
 * Configuration des contrôles de monitoring
 */
function setupMonitoringControls() {
    // Bouton pause/reprendre
    const toggleButton = document.getElementById('monitor-toggle');
    if (toggleButton) {
        toggleButton.addEventListener('click', toggleMonitoring);
    }
    
    // Bouton clear activités
    const clearButton = document.getElementById('clear-activities');
    if (clearButton) {
        clearButton.addEventListener('click', clearActivityStream);
    }
    
    // Bouton pause graphiques
    const pauseChartsButton = document.getElementById('pause-charts');
    if (pauseChartsButton) {
        pauseChartsButton.addEventListener('click', toggleChartsPause);
    }
    
    // Sélecteur de vitesse de mise à jour
    const speedSelector = document.getElementById('update-speed');
    if (speedSelector) {
        speedSelector.addEventListener('change', changeUpdateSpeed);
    }
}

/**
 * Basculer le monitoring
 */
function toggleMonitoring() {
    RealtimeMonitor.state.monitoring = !RealtimeMonitor.state.monitoring;
    
    const button = document.getElementById('monitor-toggle');
    const icon = button.querySelector('i');
    const text = button.querySelector('span');
    
    if (RealtimeMonitor.state.monitoring) {
        button.className = 'btn btn-outline-warning';
        icon.className = 'fas fa-pause';
        text.textContent = 'Pause';
        showRealtimeNotification('Monitoring activé', 'success');
    } else {
        button.className = 'btn btn-outline-success';
        icon.className = 'fas fa-play';
        text.textContent = 'Resume';
        showRealtimeNotification('Monitoring en pause', 'info');
    }
}

/**
 * Vider le flux d'activités
 */
function clearActivityStream() {
    const stream = document.getElementById('activity-stream');
    if (stream) {
        stream.innerHTML = `
            <div class="text-center text-muted py-4 empty-message">
                <i class="fas fa-stream fa-2x mb-3"></i>
                <p>Flux d'activités vidé</p>
                <small>En attente de nouvelles activités...</small>
            </div>
        `;
    }
    
    // Reset du compteur
    const counter = document.getElementById('activity-count');
    if (counter) counter.textContent = '0';
    
    RealtimeMonitor.data.activities = [];
    showRealtimeNotification('Flux d\'activités vidé', 'info');
}

/**
 * Basculer la pause des graphiques
 */
function toggleChartsPause() {
    RealtimeMonitor.state.chartsPaused = !RealtimeMonitor.state.chartsPaused;
    
    const button = document.getElementById('pause-charts');
    const icon = button.querySelector('i');
    
    if (RealtimeMonitor.state.chartsPaused) {
        button.className = 'btn btn-outline-success btn-sm';
        icon.className = 'fas fa-play';
        showRealtimeNotification('Graphiques en pause', 'info');
    } else {
        button.className = 'btn btn-outline-warning btn-sm';
        icon.className = 'fas fa-pause';
        showRealtimeNotification('Graphiques actifs', 'success');
    }
}

/**
 * Changer la vitesse de mise à jour
 */
function changeUpdateSpeed(event) {
    const speed = parseInt(event.target.value);
    RealtimeMonitor.config.updateInterval = speed;
    
    showRealtimeNotification(`Vitesse mise à jour: ${speed/1000}s`, 'info');
    
    // Redémarrer la collecte avec la nouvelle vitesse
    restartDataCollection();
}

/**
 * Démarrer la collecte de données
 */
function startDataCollection() {
    // Demander les données initiales
    if (RealtimeMonitor.socket && RealtimeMonitor.socket.connected) {
        RealtimeMonitor.socket.emit('request_stats');
        RealtimeMonitor.socket.emit('request_active_games');
    }
    
    // Mise à jour périodique
    setInterval(() => {
        if (RealtimeMonitor.state.monitoring && RealtimeMonitor.socket && RealtimeMonitor.socket.connected) {
            RealtimeMonitor.socket.emit('request_stats');
        }
    }, RealtimeMonitor.config.updateInterval);
}

/**
 * Redémarrer la collecte avec nouveaux paramètres
 */
function restartDataCollection() {
    // Les intervalles sont gérés par le serveur via WebSocket
    if (RealtimeMonitor.socket && RealtimeMonitor.socket.connected) {
        RealtimeMonitor.socket.emit('update_config', {
            interval: RealtimeMonitor.config.updateInterval
        });
    }
}

/**
 * Configuration des gestionnaires d'événements
 */
function setupRealtimeEventHandlers() {
    // Gestionnaire de redimensionnement
    window.addEventListener('resize', debounce(resizeCharts, 300));
    
    // Gestionnaire de visibilité de la page
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    // Gestionnaire de focus/blur
    window.addEventListener('focus', handleWindowFocus);
    window.addEventListener('blur', handleWindowBlur);
    
    // Gestionnaire de défilement pour le flux d'activités
    const activityStream = document.getElementById('activity-stream');
    if (activityStream) {
        activityStream.addEventListener('scroll', handleActivityStreamScroll);
    }
}

/**
 * Redimensionner les graphiques
 */
function resizeCharts() {
    Object.values(RealtimeMonitor.charts).forEach(chart => {
        if (chart && typeof chart.resize === 'function') {
            chart.resize();
        }
    });
}

/**
 * Gérer le changement de visibilité
 */
function handleVisibilityChange() {
    if (document.hidden) {
        // Page cachée - ralentir les mises à jour
        RealtimeMonitor.state.backgroundMode = true;
    } else {
        // Page visible - reprendre les mises à jour normales
        RealtimeMonitor.state.backgroundMode = false;
        
        // Demander une mise à jour immédiate
        if (RealtimeMonitor.socket && RealtimeMonitor.socket.connected) {
            RealtimeMonitor.socket.emit('request_stats');
        }
    }
}

/**
 * Gérer le focus de la fenêtre
 */
function handleWindowFocus() {
    if (RealtimeMonitor.socket && !RealtimeMonitor.socket.connected) {
        // Tentative de reconnexion si déconnecté
        RealtimeMonitor.socket.connect();
    }
}

function handleWindowBlur() {
    // La fenêtre a perdu le focus
    console.log('🔇 Fenêtre en arrière-plan');
}

/**
 * Gérer le défilement du flux d'activités
 */
function handleActivityStreamScroll(event) {
    const stream = event.target;
    const scrollPercent = (stream.scrollTop / (stream.scrollHeight - stream.clientHeight)) * 100;
    
    // Afficher un indicateur si pas en haut
    const scrollIndicator = document.getElementById('scroll-indicator');
    if (scrollIndicator) {
        scrollIndicator.style.opacity = scrollPercent > 10 ? '1' : '0';
    }
}

/**
 * Mise à jour de l'indicateur de connexion
 */
function updateConnectionIndicator(connected) {
    const indicators = document.querySelectorAll('.connection-status');
    const texts = document.querySelectorAll('.connection-text');
    
    indicators.forEach(indicator => {
        indicator.className = `connection-status ${connected ? 'online' : 'offline'}`;
    });
    
    texts.forEach(text => {
        text.textContent = connected ? 'Connecté - Temps réel actif' : 'Déconnecté';
    });
}

/**
 * Affichage de notifications temps réel
 */
function showRealtimeNotification(message, type = 'info', duration = 3000) {
    // Utiliser la fonction de notification globale si disponible
    if (typeof showNotification === 'function') {
        showNotification(message, type, duration);
        return;
    }
    
    // Sinon créer une notification simple
    console.log(`[${type.toUpperCase()}] ${message}`);
}

/**
 * Mise à jour du compteur d'activités
 */
function updateActivityCounter() {
    const counter = document.getElementById('activity-count');
    if (counter) {
        const currentCount = parseInt(counter.textContent) || 0;
        counter.textContent = currentCount + 1;
        
        // Animation du compteur
        counter.style.transform = 'scale(1.2)';
        setTimeout(() => {
            counter.style.transform = 'scale(1)';
        }, 200);
    }
}

/**
 * Utilitaire de débounce
 */
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

/**
 * Utilitaire d'échappement HTML
 */
function escapeHtml(text) {
    if (typeof text !== 'string') return text;
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Nettoyage à la fermeture
 */
window.addEventListener('beforeunload', () => {
    if (RealtimeMonitor.socket) {
        RealtimeMonitor.socket.disconnect();
    }
    console.log('🧹 Monitoring temps réel nettoyé');
});

// Initialisation automatique
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeRealtimeMonitoring);
} else {
    initializeRealtimeMonitoring();
}

// Export global
window.RealtimeMonitor = RealtimeMonitor;
window.initializeRealtimeMonitoring = initializeRealtimeMonitoring;

console.log('🔴 Module RealtimeMonitor v' + RealtimeMonitor.version + ' chargé');
