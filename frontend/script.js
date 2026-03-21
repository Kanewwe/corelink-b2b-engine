const API_BASE_URL = window.location.origin + '/api';

// Navigation
const views = {
    'nav-lead-engine': 'lead-engine-view',
    'nav-campaigns': 'campaign-logs-view',
    'nav-search-logs': 'search-logs-view',
    'nav-smtp-settings': 'smtp-settings-view'
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('corelink_token');
    const username = localStorage.getItem('corelink_user');

    if (!token) {
        document.getElementById('login-modal').classList.remove('hidden');
    } else {
        document.getElementById('display-username').innerText = username;
        fetchLeads();
        startLogPolling();
        loadSMTPSettings();
    }

    // Event Listeners
    document.getElementById('login-form')?.addEventListener('submit', handleLogin);
    document.getElementById('logout-btn')?.addEventListener('click', handleLogout);
    document.getElementById('lead-form')?.addEventListener('submit', submitLead);
    document.getElementById('scrape-form')?.addEventListener('submit', startScrape);
    document.getElementById('refresh-btn')?.addEventListener('click', fetchLeads);
    document.getElementById('smtp-form')?.addEventListener('submit', saveSMTPSettings);
    document.getElementById('test-smtp-btn')?.addEventListener('click', testSMTP);
    document.getElementById('refresh-campaigns-btn')?.addEventListener('click', fetchCampaigns);
    document.getElementById('refresh-search-logs-btn')?.addEventListener('click', fetchSearchLogs);

    // Navigation
    Object.keys(views).forEach(navId => {
        document.getElementById(navId)?.addEventListener('click', (e) => {
            e.preventDefault();
            switchView(navId);
        });
    });

    // Modal close buttons
    document.querySelectorAll('.close-btn').forEach(btn => {
        btn.addEventListener('click', closeModal);
    });
});

// Navigation
function switchView(navId) {
    // Update nav active state
    document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
    document.getElementById(navId).classList.add('active');

    // Hide all views
    document.querySelectorAll('.view-content').forEach(view => view.classList.add('hidden'));

    // Show selected view
    const viewId = views[navId];
    document.getElementById(viewId).classList.remove('hidden');

    // Update page title
    const titles = {
        'nav-lead-engine': 'AI Prospecting Dashboard',
        'nav-campaigns': '寄信記錄',
        'nav-search-logs': '搜尋記錄',
        'nav-smtp-settings': 'SMTP 設定'
    };
    document.getElementById('page-title').innerText = titles[navId];

    // Load data for specific views
    if (navId === 'nav-campaigns') fetchCampaigns();
    if (navId === 'nav-search-logs') fetchSearchLogs();
}

// Auth
function getAuthHeaders() {
    const token = localStorage.getItem('corelink_token');
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    };
}

async function handleLogin(e) {
    e.preventDefault();
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;

    try {
        const response = await fetch(`${API_BASE_URL}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('corelink_token', data.token);
            localStorage.setItem('corelink_user', data.username);
            document.getElementById('login-modal').classList.add('hidden');
            document.getElementById('display-username').innerText = data.username;
            fetchLeads();
            startLogPolling();
            loadSMTPSettings();
        } else {
            document.getElementById('login-error').style.display = 'block';
        }
    } catch (error) {
        console.error('Login error:', error);
    }
}

function handleLogout() {
    localStorage.removeItem('corelink_token');
    localStorage.removeItem('corelink_user');
    window.location.reload();
}

// Lead Management
async function submitLead(e) {
    e.preventDefault();
    const loading = document.getElementById('ai-loading');
    loading.classList.remove('hidden');

    try {
        const response = await fetch(`${API_BASE_URL}/leads`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                company_name: document.getElementById('company-name').value,
                website_url: document.getElementById('website-url').value,
                description: document.getElementById('description').value
            })
        });

        if (response.ok) {
            document.getElementById('lead-form').reset();
            fetchLeads();
            addLog('✅ 手動新增客戶成功', 'success');
        }
    } catch (error) {
        addLog('❌ 新增客戶失敗: ' + error.message, 'error');
    } finally {
        loading.classList.add('hidden');
    }
}

async function startScrape(e) {
    e.preventDefault();
    const btn = document.getElementById('start-scrape-btn');
    const status = document.getElementById('scrape-status');

    btn.disabled = true;
    btn.innerHTML = '🚀 探勘中...';

    try {
        const response = await fetch(`${API_BASE_URL}/scrape`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                market: document.getElementById('scrape-market').value,
                keyword: document.getElementById('scrape-keyword').value
            })
        });

        if (response.ok) {
            status.classList.remove('hidden');
            addLog(`🔍 開始探勘: ${document.getElementById('scrape-keyword').value}`, 'info');
            setTimeout(() => status.classList.add('hidden'), 5000);
        }
    } catch (error) {
        addLog('❌ 探勘啟動失敗: ' + error.message, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '🚀 開始自動探勘';
    }
}

async function fetchLeads() {
    try {
        const response = await fetch(`${API_BASE_URL}/leads`, { headers: getAuthHeaders() });
        if (response.status === 401) {
            handleLogout();
            return;
        }
        const leads = await response.json();
        renderLeads(leads);
    } catch (error) {
        console.error('Fetch leads error:', error);
    }
}

function renderLeads(leads) {
    const container = document.getElementById('leads-list');
    container.innerHTML = '';

    if (!leads || leads.length === 0) {
        container.innerHTML = '<p style="color: var(--text-muted); text-align: center;">尚無客戶資料</p>';
        return;
    }

    leads.forEach(lead => {
        let tagClass = 'tag-unknown';
        if (lead.ai_tag === 'NA-CABLE') tagClass = 'tag-cable';
        else if (lead.ai_tag === 'NA-NAMEPLATE') tagClass = 'tag-nameplate';
        else if (lead.ai_tag === 'NA-PLASTIC') tagClass = 'tag-plastic';

        const card = document.createElement('div');
        card.className = 'lead-card';
        card.innerHTML = `
            <div class="lead-card-header">
                <span class="lead-name">${lead.company_name}</span>
                <span class="tag-badge ${tagClass}">${lead.ai_tag}</span>
            </div>
            <div class="lead-meta">
                <div>負責人: <strong>${lead.assigned_bd}</strong> | 狀態: <strong>${lead.status}</strong></div>
                <div style="margin-top:5px; font-size:12px;">
                    🔑 關鍵字: <span style="color:#cbd5e1">${lead.extracted_keywords || '無'}</span>
                </div>
                ${lead.domain ? `<div style="margin-top:5px; font-size:12px;">🌐 網域: ${lead.domain}</div>` : ''}
                ${lead.email_candidates ? `<div style="margin-top:5px; font-size:12px;">📧 Email: ${lead.email_candidates.split(',')[0]}...</div>` : ''}
            </div>
            <div class="lead-actions">
                ${lead.status === 'Tagged' || lead.status === 'Scraped'
                    ? `<button class="btn-primary generate-btn" onclick="generateEmail(${lead.id})">✨ 生成開發信</button>`
                    : `<button class="btn-secondary" onclick="viewEmail(${lead.id})">✉️ 查看信件</button>`
                }
            </div>
        `;
        container.appendChild(card);
    });
}

// Campaigns (寄信記錄)
async function fetchCampaigns() {
    try {
        const response = await fetch(`${API_BASE_URL}/campaigns`, { headers: getAuthHeaders() });
        if (!response.ok) throw new Error('Failed to fetch');
        const campaigns = await response.json();
        renderCampaigns(campaigns);
    } catch (error) {
        console.error('Fetch campaigns error:', error);
    }
}

function renderCampaigns(campaigns) {
    const tbody = document.getElementById('campaigns-table-body');
    tbody.innerHTML = '';

    if (!campaigns || campaigns.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; color:var(--text-muted);">尚無寄信記錄</td></tr>';
        return;
    }

    campaigns.forEach(c => {
        const statusClass = c.status === 'Sent' ? 'level-success' : 
                           c.status === 'Draft' ? 'level-info' : 'level-warning';
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${c.created_at || 'N/A'}</td>
            <td>${c.company_name || 'N/A'}</td>
            <td>${c.assigned_bd || 'N/A'}</td>
            <td>${c.subject || 'N/A'}</td>
            <td><span class="${statusClass}">${c.status}</span></td>
            <td><button class="btn-secondary" onclick="viewEmail(${c.lead_id})">查看</button></td>
        `;
        tbody.appendChild(row);
    });
}

// Search Logs (搜尋記錄)
async function fetchSearchLogs() {
    try {
        const response = await fetch(`${API_BASE_URL}/system-logs`, { headers: getAuthHeaders() });
        if (!response.ok) throw new Error('Failed to fetch');
        const data = await response.json();
        renderSearchLogs(data.logs || []);
    } catch (error) {
        console.error('Fetch search logs error:', error);
    }
}

function renderSearchLogs(logs) {
    const container = document.getElementById('search-logs-container');
    container.innerHTML = '';

    if (!logs || logs.length === 0) {
        container.innerHTML = '<p style="color: var(--text-muted); text-align: center;">尚無搜尋記錄</p>';
        return;
    }

    logs.reverse().forEach(log => {
        const entry = document.createElement('div');
        entry.className = 'log-entry';
        entry.innerHTML = `
            <span class="timestamp">${log.substring(1, 9)}</span>
            <span>${log.substring(10)}</span>
        `;
        container.appendChild(entry);
    });
}

// SMTP Settings
function loadSMTPSettings() {
    const settings = JSON.parse(localStorage.getItem('smtp_settings') || '{}');
    if (settings.server) document.getElementById('smtp-server').value = settings.server;
    if (settings.port) document.getElementById('smtp-port').value = settings.port;
    if (settings.user) document.getElementById('smtp-user').value = settings.user;
}

async function saveSMTPSettings(e) {
    e.preventDefault();
    
    const settings = {
        server: document.getElementById('smtp-server').value,
        port: document.getElementById('smtp-port').value,
        user: document.getElementById('smtp-user').value,
        password: document.getElementById('smtp-password').value
    };

    // Save to localStorage (in real app, this should go to backend)
    localStorage.setItem('smtp_settings', JSON.stringify(settings));

    // Show status
    const status = document.getElementById('smtp-status');
    status.classList.remove('hidden');
    status.className = 'status-msg success';
    status.innerText = '✅ SMTP 設定已儲存';

    addLog('⚙️ SMTP 設定已更新', 'info');
}

async function testSMTP() {
    const status = document.getElementById('smtp-status');
    status.classList.remove('hidden');
    status.className = 'status-msg';
    status.innerText = '📧 正在測試 SMTP 連線...';

    // In real implementation, this would call a backend API to test SMTP
    setTimeout(() => {
        status.className = 'status-msg success';
        status.innerText = '✅ SMTP 連線測試成功（模擬）';
        addLog('📧 SMTP 測試成功', 'success');
    }, 1500);
}

// Email Generation
async function generateEmail(leadId) {
    addLog('✨ 正在生成開發信...', 'info');
    try {
        const response = await fetch(`${API_BASE_URL}/leads/${leadId}/generate-email`, {
            method: 'POST',
            headers: getAuthHeaders()
        });
        if (!response.ok) throw new Error('Generation failed');
        
        const campaign = await response.json();
        fetchLeads();
        openModal(campaign.subject, campaign.content);
        addLog('✅ 開發信生成完成', 'success');
    } catch (error) {
        addLog('❌ 生成失敗: ' + error.message, 'error');
    }
}

async function viewEmail(leadId) {
    try {
        const response = await fetch(`${API_BASE_URL}/leads/${leadId}/emails`, { headers: getAuthHeaders() });
        const emails = await response.json();
        if (emails && emails.length > 0) {
            const latest = emails[emails.length - 1];
            openModal(latest.subject, latest.content);
        }
    } catch (error) {
        console.error('View email error:', error);
    }
}

// Modal
function openModal(subject, body) {
    document.getElementById('modal-subject').value = subject;
    document.getElementById('modal-body').value = body;
    document.getElementById('email-modal').classList.remove('hidden');
}

function closeModal() {
    document.getElementById('email-modal').classList.add('hidden');
}

// System Logs
function addLog(message, level = 'info') {
    const console = document.getElementById('system-console');
    const timestamp = new Date().toLocaleTimeString('zh-TW', { hour12: false });
    const levelClass = `level-${level}`;
    
    const entry = document.createElement('div');
    entry.innerHTML = `<span class="timestamp">[${timestamp}]</span> <span class="${levelClass}">${message}</span>`;
    console.appendChild(entry);
    console.scrollTop = console.scrollHeight;
}

function startLogPolling() {
    // Poll system logs every 10 seconds
    setInterval(async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/system-logs`, { headers: getAuthHeaders() });
            if (response.ok) {
                const data = await response.json();
                updateConsole(data.logs);
            }
        } catch (error) {
            // Silent fail for polling
        }
    }, 10000);
}

function updateConsole(logs) {
    if (!logs || logs.length === 0) return;
    
    const console = document.getElementById('system-console');
    // Only update if new logs
    const currentText = console.innerText;
    logs.forEach(log => {
        if (!currentText.includes(log)) {
            const entry = document.createElement('div');
            entry.innerHTML = `<span class="timestamp">${log.substring(0, 10)}</span> ${log.substring(11)}`;
            console.appendChild(entry);
        }
    });
    console.scrollTop = console.scrollHeight;
}
