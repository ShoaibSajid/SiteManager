// Global State
let currentTab = 'dashboard';
let charts = {};
let currentData = []; // Store current table data for sorting
let sortState = { key: null, direction: 'asc' };

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    initializeDashboard();
    setupEventListeners();
});

function setupEventListeners() {
    // Navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = link.getAttribute('data-target');
            if (targetId) {
                switchTab(targetId);
            }
        });
    });

    // Search functionality for tables
    const searchInput = document.getElementById('tableSearch');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            filterTable(e.target.value);
        });
    }

    // Site selector
    const siteSelector = document.getElementById('siteSelector');
    if (siteSelector) {
        siteSelector.addEventListener('change', (e) => {
            loadSiteInventory(e.target.value);
        });
    }

    // File upload
    const uploadBtn = document.getElementById('uploadBtn');
    const fileInput = document.getElementById('fileInput');
    
    if (uploadBtn && fileInput) {
        uploadBtn.addEventListener('click', () => {
            fileInput.click();
        });

        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                uploadFile(file);
            }
        });
    }
}

async function initializeDashboard() {
    showLoading(true);
    try {
        await Promise.all([
            loadStats(),
            loadSiteSummary(),
            loadCharts()
        ]);
        
        // Ensure we start on dashboard
        switchTab('dashboard');

        // Dashboard-specific datasets
        loadTopShortages();
        loadInactiveStock();
        
        // Update timestamp
        updateLastRefreshed();
    } catch (error) {
        console.error('Initialization error:', error);
        showError('Failed to load dashboard data');
    } finally {
        showLoading(false);
    }
}

function updateLastRefreshed() {
    const now = new Date();
    const element = document.getElementById('lastUpdated');
    if (element) {
        element.textContent = `Last updated: ${now.toLocaleTimeString()}`;
    }
}

// Data Loading Functions
async function loadStats() {
    const res = await fetch('/api/dashboard/stats');
    const stats = await res.json();
    
    updateStatCard('totalSites', stats.total_sites);
    updateStatCard('totalMaterials', stats.total_materials);
    updateStatCard('negativeItems', stats.negative_items, stats.negative_items > 0 ? 'trend-down' : 'trend-neutral');
    
    // Format large numbers
    const formatVal = (num) => {
        if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
        if (num >= 1000) return (num / 1000).toFixed(1) + 'k';
        return num.toLocaleString();
    }
    
    updateStatCard('totalQuantity', formatVal(stats.total_quantity));
}

function updateStatCard(id, value, trendClass = '') {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value;
        if (trendClass) {
            const icon = element.parentElement.querySelector('.stat-trend i');
            if (icon) {
                icon.className = `fas fa-${trendClass === 'trend-up' ? 'arrow-up' : (trendClass === 'trend-down' ? 'exclamation-circle' : 'minus')}`;
                element.parentElement.querySelector('.stat-trend').className = `stat-trend ${trendClass}`;
            }
        }
    }
}

async function loadSiteSummary() {
    const res = await fetch('/api/sites/summary');
    const sites = await res.json();
    
    // Update site selector
    const selector = document.getElementById('siteSelector');
    if (selector) {
        selector.innerHTML = '<option value="">All Sites</option>';
        sites.forEach(site => {
            const option = document.createElement('option');
            option.value = site.Site;
            option.textContent = `${site.Site} (${site['Unique Materials']} items)`;
            selector.appendChild(option);
        });
    }
    
    return sites;
}

// Chart Functions
async function loadCharts() {
    const sitesRes = await fetch('/api/sites/summary');
    const sites = await sitesRes.json();
    
    // Site Comparison Chart
    const ctxSite = document.getElementById('siteChart').getContext('2d');
    if (charts.site) charts.site.destroy();
    
    charts.site = new Chart(ctxSite, {
        type: 'bar',
        data: {
            labels: sites.map(s => s.Site),
            datasets: [{
                label: 'Total Stock Quantity',
                data: sites.map(s => s['Total Quantity']),
                backgroundColor: '#3b82f6',
                borderRadius: 4,
                barPercentage: 0.6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#1e293b',
                    padding: 12,
                    cornerRadius: 8
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: '#e2e8f0', drawBorder: false },
                    ticks: { font: { family: 'Inter' } }
                },
                x: {
                    grid: { display: false },
                    ticks: { font: { family: 'Inter' } }
                }
            }
        }
    });

    // Inventory Health Distribution
    const invRes = await fetch('/api/inventory/all');
    const invData = await invRes.json();
    
    // Process distribution buckets
    const buckets = {
        critical: 0,
        low: 0,
        healthy: 0,
        excess: 0
    };
    
    invData.forEach(item => {
        const qty = item['Current Quantity'];
        if (qty < 0) buckets.critical++;
        else if (qty === 0) buckets.low++;
        else if (qty > 1000) buckets.excess++;
        else buckets.healthy++;
    });

    const ctxDist = document.getElementById('distributionChart').getContext('2d');
    if (charts.dist) charts.dist.destroy();
    
    charts.dist = new Chart(ctxDist, {
        type: 'doughnut',
        data: {
            labels: ['Critical (Negative)', 'Empty', 'Healthy', 'Excess'],
            datasets: [{
                data: Object.values(buckets),
                backgroundColor: ['#ef4444', '#f59e0b', '#10b981', '#3b82f6'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '70%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { usePointStyle: true, padding: 20 }
                }
            }
        }
    });
}

// Tab Switching
function switchTab(tabId) {
    // Reset sort state on tab switch
    sortState = { key: null, direction: 'asc' };
    
    // Update nav state
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
    document.querySelector(`[data-target="${tabId}"]`).classList.add('active');
    
    // View Switching
    const dashboardView = document.getElementById('dashboard-view');
    const dataView = document.getElementById('data-view');
    
    if (tabId === 'dashboard') {
        dashboardView.classList.remove('hidden');
        dataView.classList.add('hidden');
        document.getElementById('pageTitle').textContent = 'Executive Overview';
        document.getElementById('pageSubtitle').textContent = 'Multi-Site Inventory Analysis & Optimization';
    } else {
        dashboardView.classList.add('hidden');
        dataView.classList.remove('hidden');
        
        // Update Title
        const titles = {
            'shortages': 'Stock Shortages',
            'critical': 'Critical Attention Items',
            'abundant': 'Excess Inventory',
            'shipping': 'Transfer Recommendations',
            'site-inventory': 'Site Inventory Detail',
            'bottlenecks': 'Bottleneck Analysis',
            'focus-areas': 'Focus Areas',
            'movements': 'Movement Recommendations'
        };
        document.getElementById('sectionTitle').textContent = titles[tabId];
        document.getElementById('pageTitle').textContent = titles[tabId];
        document.getElementById('pageSubtitle').textContent = 'Detailed data view';
        
        // Show/Hide Controls
        const siteSelector = document.getElementById('siteSelectorContainer');
        if (tabId === 'site-inventory') {
            siteSelector.classList.remove('hidden');
        } else {
            siteSelector.classList.add('hidden');
        }

        // Load Data
        currentTab = tabId;
        switch(tabId) {
            case 'shortages': loadShortages(); break;
            case 'critical': loadCritical(); break;
            case 'abundant': loadAbundant(); break;
            case 'shipping': loadShipping(); break;
            case 'site-inventory': loadSiteInventory(); break;
            case 'bottlenecks': loadBottlenecks(); break;
            case 'focus-areas': loadFocusAreas(); break;
            case 'movements': loadMovements(); break;
        }
    }
}

// Table Rendering Functions
async function loadShortages() {
    renderLoadingTable();
    const res = await fetch('/api/items/shortages');
    const data = await res.json();
    currentData = data;
    currentColumns = [
        { key: 'Site', label: 'Plant', sortable: true },
        { key: 'Storage Location', label: 'Storage Location', sortable: true },
        { key: 'Material', label: 'Material ID', sortable: true, type: 'link' },
        { key: 'Material Description', label: 'Description', sortable: true },
        { key: 'Current Quantity', label: 'Variance', format: 'number', sortable: true },
        { key: 'Total Value', label: 'Value Impact', format: 'currency', sortable: true },
        { key: 'Shortage Level', label: 'Severity', type: 'badge', sortable: true }
    ];
    
    renderTable(currentData, currentColumns);
}

async function loadCritical() {
    renderLoadingTable();
    const res = await fetch('/api/items/critical');
    const data = await res.json();
    currentData = data;
    currentColumns = [
        { key: 'Site', label: 'Plant', sortable: true },
        { key: 'Storage Location', label: 'Storage Location', sortable: true },
        { key: 'Material', label: 'Material ID', sortable: true, type: 'link' },
        { key: 'Material Description', label: 'Description', sortable: true },
        { key: 'Current Quantity', label: 'Stock Level', format: 'number', sortable: true },
        { key: 'Total Value', label: 'Value', format: 'currency', sortable: true },
        { key: 'Last Active', label: 'Last Active', sortable: true }
    ];
    
    renderTable(currentData, currentColumns);
}

async function loadAbundant() {
    renderLoadingTable();
    const res = await fetch('/api/items/abundant');
    const data = await res.json();
    currentData = data;
    currentColumns = [
        { key: 'Site', label: 'Plant', sortable: true },
        { key: 'Storage Location', label: 'Storage Location', sortable: true },
        { key: 'Material', label: 'Material ID', sortable: true, type: 'link' },
        { key: 'Material Description', label: 'Description', sortable: true },
        { key: 'Current Quantity', label: 'Stock Level', format: 'number', sortable: true },
        { key: 'Total Value', label: 'Value', format: 'currency', sortable: true },
        { key: 'Abundance Level', label: 'Status', type: 'badge-abundant', sortable: true }
    ];
    
    renderTable(currentData, currentColumns);
}

async function loadShipping() {
    renderLoadingTable();
    const res = await fetch('/api/recommendations/shipping');
    const data = await res.json();
    currentData = data;
    currentColumns = [
        { key: 'Material', label: 'Material', sortable: true, type: 'link' },
        { key: 'Material Description', label: 'Description', sortable: true },
        { key: 'From Site', label: 'Source Plant', sortable: true },
        { key: 'To Site', label: 'Dest. Plant', sortable: true },
        { key: 'Recommended Quantity', label: 'Transfer Qty', format: 'number', sortable: true },
        { key: 'Priority', label: 'Priority', type: 'badge-priority', sortable: true }
    ];
    
    renderTable(currentData, currentColumns);
}

async function loadSiteInventory(site = '') {
    renderLoadingTable();
    const url = site ? `/api/site/${site}/inventory` : '/api/inventory/all';
    const res = await fetch(url);
    const data = await res.json();
    currentData = data;
    
    const displayData = data.slice(0, 500); 
    
    currentColumns = [
        { key: 'Site', label: 'Plant', sortable: true },
        { key: 'Storage Location', label: 'Storage Location', sortable: true },
        { key: 'Material', label: 'Material ID', sortable: true, type: 'link' },
        { key: 'Material Description', label: 'Description', sortable: true },
        { key: 'Current Quantity', label: 'Qty', format: 'number', colorize: true, sortable: true },
        { key: 'Total Value', label: 'Value', format: 'currency', sortable: true },
        { key: 'Last Active', label: 'Last Active', sortable: true }
    ];
    
    renderTable(displayData, currentColumns);
}

async function loadBottlenecks() {
    renderLoadingTable();
    const res = await fetch('/api/analysis/bottlenecks');
    const data = await res.json();
    
    // Create tabs for different bottleneck types
    const tabs = ['sites', 'locations', 'materials'];
    let html = '<div class="bottleneck-tabs" style="margin-bottom: 1rem; border-bottom: 2px solid #e2e8f0;">';
    tabs.forEach((tab, idx) => {
        html += `<button class="bottleneck-tab ${idx === 0 ? 'active' : ''}" onclick="switchBottleneckTab('${tab}')" style="padding: 0.75rem 1.5rem; border: none; background: none; cursor: pointer; border-bottom: 2px solid transparent; margin-right: 1rem; font-weight: 500;">${tab.charAt(0).toUpperCase() + tab.slice(1)}</button>`;
    });
    html += '</div><div id="bottleneckContent"></div>';
    
    document.getElementById('tableBody').parentElement.parentElement.innerHTML = html;
    
    // Store data globally for tab switching
    window.bottleneckData = data;
    renderBottleneckTab('sites');
}

function switchBottleneckTab(type) {
    document.querySelectorAll('.bottleneck-tab').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    renderBottleneckTab(type);
}

function renderBottleneckTab(type) {
    const container = document.getElementById('bottleneckContent');
    const data = window.bottleneckData[type];
    
    if (!data || data.length === 0) {
        container.innerHTML = '<p class="text-muted">No bottlenecks found for this category.</p>';
        return;
    }
    
    let columns = [];
    if (type === 'sites') {
        columns = [
            { key: 'Site', label: 'Plant', sortable: true },
            { key: 'Total Shortage Qty', label: 'Total Shortage', format: 'number', sortable: true },
            { key: 'Item Count', label: 'Items Affected', sortable: true },
            { key: 'Total Value Impact', label: 'Value Impact', format: 'currency', sortable: true },
            { key: 'Priority', label: 'Priority', type: 'badge-priority', sortable: true }
        ];
    } else if (type === 'locations') {
        columns = [
            { key: 'Site', label: 'Plant', sortable: true },
            { key: 'Storage Location', label: 'Storage Location', sortable: true },
            { key: 'Total Shortage Qty', label: 'Total Shortage', format: 'number', sortable: true },
            { key: 'Item Count', label: 'Items Affected', sortable: true },
            { key: 'Total Value Impact', label: 'Value Impact', format: 'currency', sortable: true },
            { key: 'Priority', label: 'Priority', type: 'badge-priority', sortable: true }
        ];
    } else {
        columns = [
            { key: 'Material', label: 'Material ID', sortable: true, type: 'link' },
            { key: 'Material Description', label: 'Description', sortable: true },
            { key: 'Total Shortage Qty', label: 'Total Shortage', format: 'number', sortable: true },
            { key: 'Total Value Impact', label: 'Value Impact', format: 'currency', sortable: true },
            { key: 'Affected Sites', label: 'Affected Sites', sortable: true },
            { key: 'Priority', label: 'Priority', type: 'badge-priority', sortable: true }
        ];
    }
    
    currentData = data;
    currentColumns = columns;
    
    // Create table structure
    container.innerHTML = '<div class="table-responsive"><table><thead id="btHeaders"></thead><tbody id="btBody"></tbody></table></div>';
    
    // Small delay to ensure DOM is ready
    setTimeout(() => {
        renderTable(data, columns, 'btHeaders', 'btBody');
    }, 10);
}

async function loadFocusAreas() {
    renderLoadingTable();
    const res = await fetch('/api/analysis/focus-areas');
    const data = await res.json();
    
    const tabs = ['high_value', 'critical_quantity', 'site_issues', 'location_issues'];
    const tabLabels = {
        'high_value': 'High Value Impact',
        'critical_quantity': 'Critical Quantity',
        'site_issues': 'Site Issues',
        'location_issues': 'Location Issues'
    };
    
    let html = '<div class="focus-tabs" style="margin-bottom: 1rem; border-bottom: 2px solid #e2e8f0;">';
    tabs.forEach((tab, idx) => {
        html += `<button class="focus-tab ${idx === 0 ? 'active' : ''}" onclick="switchFocusTab('${tab}')" style="padding: 0.75rem 1.5rem; border: none; background: none; cursor: pointer; border-bottom: 2px solid transparent; margin-right: 1rem; font-weight: 500;">${tabLabels[tab]}</button>`;
    });
    html += '</div><div id="focusContent"></div>';
    
    document.getElementById('tableBody').parentElement.parentElement.innerHTML = html;
    
    window.focusData = data;
    renderFocusTab('high_value');
}

function switchFocusTab(type) {
    document.querySelectorAll('.focus-tab').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    renderFocusTab(type);
}

function renderFocusTab(type) {
    const container = document.getElementById('focusContent');
    const data = window.focusData[type];
    
    if (!data || data.length === 0) {
        container.innerHTML = '<p class="text-muted">No focus areas found for this category.</p>';
        return;
    }
    
    let columns = [];
    if (type === 'high_value' || type === 'critical_quantity') {
        columns = [
            { key: 'Site', label: 'Plant', sortable: true },
            { key: 'Storage Location', label: 'Storage Location', sortable: true },
            { key: 'Material', label: 'Material ID', sortable: true, type: 'link' },
            { key: 'Material Description', label: 'Description', sortable: true },
            { key: 'Current Quantity', label: 'Qty', format: 'number', colorize: true, sortable: true },
            { key: 'Total Value', label: 'Value', format: 'currency', sortable: true },
            { key: 'Focus Reason', label: 'Reason', sortable: true },
            { key: 'Action', label: 'Recommended Action', sortable: true }
        ];
    } else if (type === 'site_issues') {
        columns = [
            { key: 'Site', label: 'Plant', sortable: true },
            { key: 'Shortage Count', label: 'Shortages', sortable: true },
            { key: 'Total Shortage Qty', label: 'Total Shortage', format: 'number', sortable: true },
            { key: 'Total Value Impact', label: 'Value Impact', format: 'currency', sortable: true },
            { key: 'Focus Reason', label: 'Reason', sortable: true },
            { key: 'Action', label: 'Recommended Action', sortable: true }
        ];
    } else {
        columns = [
            { key: 'Site', label: 'Plant', sortable: true },
            { key: 'Storage Location', label: 'Storage Location', sortable: true },
            { key: 'Shortage Count', label: 'Shortages', sortable: true },
            { key: 'Total Shortage Qty', label: 'Total Shortage', format: 'number', sortable: true },
            { key: 'Total Value Impact', label: 'Value Impact', format: 'currency', sortable: true },
            { key: 'Focus Reason', label: 'Reason', sortable: true },
            { key: 'Action', label: 'Recommended Action', sortable: true }
        ];
    }
    
    currentData = data;
    currentColumns = columns;
    
    // Create table structure
    container.innerHTML = '<div class="table-responsive"><table><thead id="ftHeaders"></thead><tbody id="ftBody"></tbody></table></div>';
    
    // Small delay to ensure DOM is ready
    setTimeout(() => {
        renderTable(data, columns, 'ftHeaders', 'ftBody');
    }, 10);
}

async function loadMovements() {
    renderLoadingTable();
    const res = await fetch('/api/recommendations/movements');
    const data = await res.json();
    currentData = data;
    currentColumns = [
        { key: 'Material', label: 'Material', sortable: true, type: 'link' },
        { key: 'Material Description', label: 'Description', sortable: true },
        { key: 'From Site', label: 'From Plant', sortable: true },
        { key: 'From Storage Location', label: 'From Storage', sortable: true },
        { key: 'To Site', label: 'To Plant', sortable: true },
        { key: 'To Storage Location', label: 'To Storage', sortable: true },
        { key: 'Available Qty', label: 'Available', format: 'number', sortable: true },
        { key: 'Required Qty', label: 'Required', format: 'number', sortable: true },
        { key: 'Recommended Quantity', label: 'Transfer Qty', format: 'number', sortable: true },
        { key: 'Estimated Value', label: 'Value', format: 'currency', sortable: true },
        { key: 'Priority', label: 'Priority', type: 'badge-priority', sortable: true },
        { key: 'Impact', label: 'Impact', type: 'badge-priority', sortable: true }
    ];
    
    renderTable(currentData, currentColumns);
}

// Modal Functions
function openModal(material) {
    const modal = document.getElementById('detailsModal');
    const loading = document.getElementById('modalLoading');
    const content = document.getElementById('modalData');
    
    document.getElementById('modalTitle').textContent = `Details: ${material}`;
    modal.classList.add('active');
    loading.classList.remove('hidden');
    content.innerHTML = '';
    
    // Fetch Details
    fetch(`/api/material/${material}/details`)
        .then(res => res.json())
        .then(data => {
            renderModalContent(data, material);
            loading.classList.add('hidden');
        })
        .catch(err => {
            content.innerHTML = '<p class="text-danger">Failed to load details.</p>';
            loading.classList.add('hidden');
        });
}

function closeModal() {
    document.getElementById('detailsModal').classList.remove('active');
}

function renderModalContent(data, materialId) {
    const content = document.getElementById('modalData');
    
    // Calculate totals
    const totalQty = data.locations.reduce((sum, loc) => sum + loc.Quantity, 0);
    const totalValue = data.locations.reduce((sum, loc) => sum + loc.Value, 0);
    
    let html = `
        <div class="modal-section">
            <h3>Overview</h3>
            <div class="stats-grid" style="grid-template-columns: 1fr 1fr; margin-bottom: 0;">
                <div class="stat-card" style="padding: 1rem;">
                    <div class="stat-header" style="margin-bottom: 0.5rem;">
                        <span class="stat-title">Total Quantity</span>
                    </div>
                    <div class="stat-value" style="font-size: 1.5rem;">${Number(totalQty).toLocaleString()}</div>
                </div>
                <div class="stat-card" style="padding: 1rem;">
                    <div class="stat-header" style="margin-bottom: 0.5rem;">
                        <span class="stat-title">Total Value</span>
                    </div>
                    <div class="stat-value" style="font-size: 1.5rem;">${Number(totalValue).toLocaleString(undefined, {style: 'currency', currency: 'USD'})}</div>
                </div>
            </div>
        </div>

        <div class="modal-section">
            <h3>Storage Location Breakdown</h3>
            <div class="table-responsive" style="max-height: 200px; overflow-y: auto;">
                <table>
                    <thead>
                        <tr>
                            <th style="padding: 0.5rem;">Plant</th>
                            <th style="padding: 0.5rem;">Storage Loc</th>
                            <th style="padding: 0.5rem;">Quantity</th>
                            <th style="padding: 0.5rem;">Value</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.locations.map(loc => `
                            <tr>
                                <td style="padding: 0.5rem;">${loc.Site}</td>
                                <td style="padding: 0.5rem;">${loc['Storage Location']}</td>
                                <td style="padding: 0.5rem; font-weight: 600;">${Number(loc.Quantity).toLocaleString()}</td>
                                <td style="padding: 0.5rem;">${Number(loc.Value).toLocaleString(undefined, {style: 'currency', currency: 'USD'})}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="modal-section">
            <h3>Recent Transactions (Last 10)</h3>
            <div class="transaction-list">
                ${data.transactions.length > 0 ? data.transactions.map(tx => `
                    <div class="transaction-item">
                        <span class="tx-date">${tx.Date}</span>
                        <span class="tx-type">${tx.Type}</span>
                        <span class="tx-loc">${tx.Site} / ${tx.Storage}</span>
                        <span class="tx-qty ${tx.Qty < 0 ? 'text-danger' : 'text-success'}">${tx.Qty}</span>
                    </div>
                `).join('') : '<p class="text-muted">No recent transactions found.</p>'}
            </div>
        </div>
    `;
    
    content.innerHTML = html;
}

// Sorting Logic
function sortTable(key) {
    if (sortState.key === key) {
        sortState.direction = sortState.direction === 'asc' ? 'desc' : 'asc';
    } else {
        sortState.key = key;
        sortState.direction = 'asc';
    }
    
    currentData.sort((a, b) => {
        let valA = a[key];
        let valB = b[key];
        
        if (typeof valA === 'number' && typeof valB === 'number') {
            return sortState.direction === 'asc' ? valA - valB : valB - valA;
        }
        
        valA = String(valA || '').toLowerCase();
        valB = String(valB || '').toLowerCase();
        
        if (valA < valB) return sortState.direction === 'asc' ? -1 : 1;
        if (valA > valB) return sortState.direction === 'asc' ? 1 : -1;
        return 0;
    });
    
    renderTable(currentData, currentColumns);
    updateSortIcons(key, sortState.direction);
}

function updateSortIcons(activeKey, direction) {
    document.querySelectorAll('.sort-icon').forEach(icon => {
        icon.className = 'fas fa-sort sort-icon text-gray-300';
    });
    
    const activeHeader = document.querySelector(`th[data-key="${activeKey}"] .sort-icon`);
    if (activeHeader) {
        activeHeader.className = `fas fa-sort-${direction === 'asc' ? 'up' : 'down'} sort-icon text-blue-500`;
    }
}

// Utility Helpers
function renderLoadingTable() {
    const tbody = document.getElementById('tableBody');
    tbody.innerHTML = '<tr><td colspan="100%" class="text-center py-4"><div class="spinner mx-auto"></div></td></tr>';
}

let currentColumns = []; 

function renderTable(data, columns, headerId = 'tableHeaders', bodyId = 'tableBody') {
    const thead = document.getElementById(headerId);
    const tbody = document.getElementById(bodyId);
    
    if (!thead || !tbody) {
        console.error(`Table elements not found: ${headerId}, ${bodyId}`);
        return;
    }
    
    thead.innerHTML = `<tr>${columns.map(col => `
        <th class="${col.sortable ? 'cursor-pointer hover:bg-gray-50' : ''}" 
            onclick="${col.sortable ? `sortTable('${col.key}')` : ''}"
            data-key="${col.key}">
            <div class="flex items-center gap-2">
                ${col.label}
                ${col.sortable ? '<i class="fas fa-sort sort-icon text-gray-300"></i>' : ''}
            </div>
        </th>
    `).join('')}</tr>`;
    
    if (!data || data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="100%" style="text-align:center; padding: 2rem;">No records found</td></tr>';
        return;
    }
    
    tbody.innerHTML = data.map(row => `
        <tr>
            ${columns.map(col => {
                let val = row[col.key];
                
                if (col.format === 'number') val = Number(val).toLocaleString();
                if (col.format === 'currency') val = Number(val).toLocaleString(undefined, {style: 'currency', currency: 'USD'});
                
                if (col.type === 'link') {
                    return `<td><a href="#" onclick="openModal('${val}'); return false;" class="text-blue-500 hover:underline font-medium">${val}</a></td>`;
                }

                if (col.type === 'badge') {
                    const level = (val || 'Unknown').toLowerCase();
                    return `<td><span class="badge badge-${level}">${row[col.key]}</span></td>`;
                }
                
                if (col.type === 'badge-priority') {
                    const level = (val || 'medium').toLowerCase() === 'high' ? 'critical' : 'moderate';
                    return `<td><span class="badge badge-${level}">${row[col.key]}</span></td>`;
                }

                if (col.type === 'badge-abundant') {
                    const level = (val || 'moderate').toLowerCase().replace(' ', '-');
                    return `<td><span class="badge badge-abundant">${row[col.key]}</span></td>`;
                }
                
                if (col.colorize) {
                     const num = row[col.key];
                     let className = num < 0 ? 'text-danger' : (num > 0 ? 'text-success' : 'text-muted');
                     return `<td class="${className}" style="font-weight: 600">${val}</td>`;
                }
                
                return `<td>${val !== undefined ? val : '-'}</td>`;
            }).join('')}
        </tr>
    `).join('');
}

function filterTable(query) {
    const lowerQuery = query.toLowerCase();
    const filtered = currentData.filter(row => {
        return Object.values(row).some(val => 
            String(val).toLowerCase().includes(lowerQuery)
        );
    });
    renderTable(filtered, currentColumns);
}

function showLoading(show) {
    // Optional global loading state
}

function showError(msg) {
    console.error(msg);
}

// Dashboard extras
async function loadTopShortages() {
    const body = document.getElementById('topShortagesBody');
    if (!body) return;
    try {
        const res = await fetch('/api/analysis/top-shortages?limit=8');
        const data = await res.json();
        if (!data || data.length === 0) {
            body.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:1rem;">No shortages found</td></tr>';
            return;
        }
        body.innerHTML = data.map(row => `
            <tr>
                <td>${row.Site}</td>
                <td>${row['Storage Location']}</td>
                <td><a href="#" onclick="openModal('${row.Material}'); return false;" class="text-blue-500 hover:underline">${row.Material}</a></td>
                <td class="${row['Current Quantity'] < 0 ? 'text-danger' : 'text-muted'}">${Number(row['Current Quantity']).toLocaleString()}</td>
                <td>${Number(row['Total Value']).toLocaleString(undefined, {style:'currency', currency:'USD'})}</td>
            </tr>
        `).join('');
    } catch (e) {
        body.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:1rem;">Error loading data</td></tr>';
    }
}

async function loadInactiveStock() {
    const body = document.getElementById('inactiveBody');
    if (!body) return;
    try {
        const res = await fetch('/api/analysis/inactive-stock?days=90&limit=8');
        const data = await res.json();
        if (!data || data.length === 0) {
            body.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:1rem;">No inactive stock found</td></tr>';
            return;
        }
        body.innerHTML = data.map(row => `
            <tr>
                <td>${row.Site}</td>
                <td>${row['Storage Location']}</td>
                <td><a href="#" onclick="openModal('${row.Material}'); return false;" class="text-blue-500 hover:underline">${row.Material}</a></td>
                <td>${Number(row['Current Quantity']).toLocaleString()}</td>
                <td>${row['Last Active']}</td>
            </tr>
        `).join('');
    } catch (e) {
        body.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:1rem;">Error loading data</td></tr>';
    }
}

// File Upload Functions
async function uploadFile(file) {
    const uploadBtn = document.getElementById('uploadBtn');
    const uploadStatus = document.getElementById('uploadStatus');
    const fileInput = document.getElementById('fileInput');
    
    // Validate file type
    const validTypes = ['.xlsx', '.xls'];
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!validTypes.includes(fileExtension)) {
        showUploadStatus('error', 'Please upload an Excel file (.xlsx or .xls)');
        fileInput.value = '';
        return;
    }
    
    // Validate file size (50MB max)
    const maxSize = 50 * 1024 * 1024; // 50MB
    if (file.size > maxSize) {
        showUploadStatus('error', 'File size exceeds 50MB limit');
        fileInput.value = '';
        return;
    }
    
    // Create FormData
    const formData = new FormData();
    formData.append('file', file);
    
    // Update UI
    uploadBtn.classList.add('uploading');
    uploadBtn.disabled = true;
    showUploadStatus('processing', `Uploading ${file.name}...`);
    
    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            showUploadStatus('success', `File uploaded successfully! Processing ${result.stats.total_items} items...`);
            
            // Reload all dashboard data after a short delay
            setTimeout(async () => {
                try {
                    // Reset analyzer by reloading page or reinitializing
                    await initializeDashboard();
                    showUploadStatus('success', 'Dashboard updated with new data!');
                    
                    // Hide status after 3 seconds
                    setTimeout(() => {
                        hideUploadStatus();
                    }, 3000);
                } catch (error) {
                    console.error('Error reloading dashboard:', error);
                    showUploadStatus('error', 'File uploaded but failed to reload dashboard. Please refresh the page.');
                }
            }, 1000);
        } else {
            showUploadStatus('error', result.error || 'Upload failed. Please try again.');
        }
    } catch (error) {
        console.error('Upload error:', error);
        showUploadStatus('error', 'Network error. Please check your connection and try again.');
    } finally {
        uploadBtn.classList.remove('uploading');
        uploadBtn.disabled = false;
        fileInput.value = ''; // Reset file input
    }
}

function showUploadStatus(type, message) {
    const uploadStatus = document.getElementById('uploadStatus');
    if (!uploadStatus) return;
    
    uploadStatus.textContent = message;
    uploadStatus.className = `upload-status ${type}`;
    uploadStatus.classList.remove('hidden');
}

function hideUploadStatus() {
    const uploadStatus = document.getElementById('uploadStatus');
    if (uploadStatus) {
        uploadStatus.classList.add('hidden');
    }
}
