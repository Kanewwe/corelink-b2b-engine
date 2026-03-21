const API_BASE_URL = window.location.origin + '/api';

// Navigation
const views = {
    'nav-lead-engine': 'lead-engine-view',
    'nav-add-lead': 'add-lead-view',
    'nav-campaigns': 'campaign-logs-view',
    'nav-engagements': 'engagements-view',
    'nav-search-logs': 'search-logs-view',
    'nav-templates': 'templates-view',
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
    document.getElementById('scrape-form')?.addEventListener('submit', startScrape);
    document.getElementById('refresh-btn')?.addEventListener('click', fetchLeads);
    document.getElementById('smtp-form')?.addEventListener('submit', saveSMTPSettings);
    document.getElementById('test-smtp-btn')?.addEventListener('click', testSMTP);
    document.getElementById('refresh-campaigns-btn')?.addEventListener('click', fetchCampaigns);
    document.getElementById('refresh-search-logs-btn')?.addEventListener('click', fetchSearchLogs);
    document.getElementById('template-form')?.addEventListener('submit', saveTemplate);
    document.getElementById('refresh-templates-btn')?.addEventListener('click', fetchTemplates);
    document.getElementById('quick-lead-form')?.addEventListener('submit', submitQuickLead);
    document.getElementById('pricing-form')?.addEventListener('submit', savePricing);
    document.getElementById('refresh-engagements-btn')?.addEventListener('click', fetchEngagements);
    document.getElementById('btn-scheduler-start')?.addEventListener('click', startScheduler);
    document.getElementById('btn-scheduler-stop')?.addEventListener('click', stopScheduler);
    document.getElementById('btn-scheduler-refresh')?.addEventListener('click', fetchSchedulerStatus);

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
        'nav-add-lead': '新增客戶',
        'nav-campaigns': '寄信記錄',
        'nav-engagements': '觸及率分析',
        'nav-search-logs': '搜尋記錄',
        'nav-templates': '信件模板管理',
        'nav-smtp-settings': 'SMTP 設定'
    };
    document.getElementById('page-title').innerText = titles[navId];

    // Load data for specific views
    if (navId === 'nav-campaigns') fetchCampaigns();
    if (navId === 'nav-search-logs') fetchSearchLogs();
    if (navId === 'nav-templates') fetchTemplates();
    if (navId === 'nav-engagements') { fetchEngagements(); loadPricing(); }
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

// Quick Lead Management (獨立新增頁面)
async function submitQuickLead(e) {
    e.preventDefault();
    const btn = document.getElementById('quick-lead-btn');
    const loading = document.getElementById('quick-lead-loading');
    const result = document.getElementById('quick-lead-result');

    btn.disabled = true;
    loading.classList.remove('hidden');
    result.classList.add('hidden');

    try {
        // Use a placeholder description since this is a quick form
        const response = await fetch(`${API_BASE_URL}/leads`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                company_name: document.getElementById('quick-company-name').value,
                website_url: document.getElementById('quick-website-url').value,
                description: "Quick add from new lead form."
            })
        });

        if (response.ok) {
            const lead = await response.json();
            result.classList.remove('hidden', 'error');
            result.className = 'status-msg success';
            result.innerHTML = `✅ <strong>${lead.company_name}</strong> 已新增！<br>分類標籤：<span class="tag-badge">${lead.ai_tag}</span>，負責人：${lead.assigned_bd}`;
            document.getElementById('quick-lead-form').reset();
            setTimeout(() => result.classList.add('hidden'), 6000);
        } else {
            throw new Error('Server error');
        }
    } catch (error) {
        result.classList.remove('hidden');
        result.className = 'status-msg error';
        result.innerText = '❌ 新增失敗，請稍後再試';
    } finally {
        btn.disabled = false;
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
        
        const emailSentBadge = lead.email_sent ? '<span style="background:#10b981; color:white; padding:2px 8px; border-radius:4px; font-size:11px; margin-left:8px;">✓ 已寄信</span>' : '';
        const assignedBD = lead.assigned_bd || '尚未指派';
        const keywords = lead.extracted_keywords || '無';
        
        card.innerHTML = `
            <div class="lead-card-header">
                <span class="lead-name">${lead.company_name}${emailSentBadge}</span>
                <span class="tag-badge ${tagClass}">${lead.ai_tag || 'UNKNOWN'}</span>
            </div>
            <div class="lead-meta">
                <div>負責人: <strong>${assignedBD}</strong> | 狀態: <strong>${lead.status || '未知'}</strong></div>
                <div style="margin-top:5px; font-size:12px;">
                    🔑 關鍵字: <span style="color:#cbd5e1">${keywords}</span>
                </div>
                ${lead.domain ? `<div style="margin-top:5px; font-size:12px;">🌐 網域: ${lead.domain}</div>` : ''}
                ${lead.email_candidates ? `<div style="margin-top:5px; font-size:12px;">📧 Email: ${lead.email_candidates.split(',')[0]}...</div>` : ''}
            </div>
            <div class="lead-actions">
                ${lead.status === 'Tagged' || lead.status === 'Scraped'
                    ? `<button class="btn-primary generate-btn" onclick="generateEmail(${lead.id})">✨ 生成開發信</button>`
                    : `<button class="btn-secondary" onclick="viewEmail(${lead.id})">✉️ 查看信件</button>`
                }
                ${!lead.email_sent ? `<button class="btn-secondary" onclick="markEmailSent(${lead.id})" style="margin-left:8px;">✓ 標記已寄</button>` : ''}
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
    fetchSchedulerStatus();
}

// Scheduler Control
async function fetchSchedulerStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/scheduler/status`, { 
            headers: getAuthHeaders() 
        });
        const data = await response.json();
        
        const statusEl = document.getElementById('scheduler-status');
        if (data.running) {
            statusEl.innerHTML = '<span style="color:#10b981;">● 運行中</span>';
        } else {
            statusEl.innerHTML = '<span style="color:#ef4444;">○ 已停止</span>';
        }
    } catch (error) {
        console.error('Scheduler status error:', error);
    }
}

async function startScheduler() {
    try {
        const response = await fetch(`${API_BASE_URL}/scheduler/start`, { 
            method: 'POST',
            headers: getAuthHeaders() 
        });
        if (response.ok) {
            addLog('✅ 寄信排程已啟動', 'success');
            fetchSchedulerStatus();
        }
    } catch (error) {
        addLog('❌ 啟動排程失敗', 'error');
    }
}

async function stopScheduler() {
    try {
        const response = await fetch(`${API_BASE_URL}/scheduler/stop`, { 
            method: 'POST',
            headers: getAuthHeaders() 
        });
        if (response.ok) {
            addLog('✅ 寄信排程已停止', 'success');
            fetchSchedulerStatus();
        }
    } catch (error) {
        addLog('❌ 停止排程失敗', 'error');
    }
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

    try {
        const response = await fetch(`${API_BASE_URL}/smtp/test`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                server: document.getElementById('smtp-server').value,
                port: parseInt(document.getElementById('smtp-port').value),
                user: document.getElementById('smtp-user').value,
                password: document.getElementById('smtp-password').value
            })
        });

        const result = await response.json();
        
        if (result.success) {
            status.className = 'status-msg success';
            status.innerText = `✅ ${result.message}`;
            addLog('📧 SMTP 測試成功', 'success');
        } else {
            status.className = 'status-msg error';
            status.innerText = `❌ ${result.message}`;
            addLog('❌ SMTP 測試失敗: ' + result.message, 'error');
        }
    } catch (error) {
        status.className = 'status-msg error';
        status.innerText = '❌ 測試失敗: ' + error.message;
        addLog('❌ SMTP 測試錯誤', 'error');
    }
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

// Email Templates Management
async function fetchTemplates() {
    const container = document.getElementById('templates-list');
    
    try {
        const response = await fetch(`${API_BASE_URL}/templates`, { headers: getAuthHeaders() });
        if (!response.ok) {
            container.innerHTML = '<p style="color:var(--text-muted);">API 錯誤，請檢查認證</p>';
            throw new Error('Failed to fetch');
        }
        const templates = await response.json();
        renderTemplates(templates);
    } catch (error) {
        console.error('Fetch templates error:', error);
        container.innerHTML = '<p style="color:var(--text-muted);">載入失敗，請重新整理</p>';
    }
}

function renderTemplates(templates) {
    const container = document.getElementById('templates-list');
    container.innerHTML = '';

    if (!templates || templates.length === 0) {
        container.innerHTML = '<p style="color:var(--text-muted);">尚無模板</p>';
        return;
    }

    // Group by tag
    const grouped = {};
    templates.forEach(t => {
        if (!grouped[t.tag]) grouped[t.tag] = [];
        grouped[t.tag].push(t);
    });

    Object.keys(grouped).forEach(tag => {
        const tagSection = document.createElement('div');
        tagSection.style.marginBottom = '20px';
        
        let tagClass = 'tag-unknown';
        if (tag === 'NA-CABLE') tagClass = 'tag-cable';
        else if (tag === 'NA-NAMEPLATE') tagClass = 'tag-nameplate';
        else if (tag === 'NA-PLASTIC') tagClass = 'tag-plastic';
        
        tagSection.innerHTML = `<h4 style="margin-bottom:10px;"><span class="tag-badge ${tagClass}">${tag}</span></h4>`;
        
        grouped[tag].forEach(t => {
            const item = document.createElement('div');
            item.style.cssText = 'padding:10px; background:rgba(255,255,255,0.05); border-radius:6px; margin-bottom:8px;';
            item.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <strong>${t.name}</strong> ${t.is_default ? '<span style="color:#10b981;">(預設)</span>' : ''}
                        <div style="font-size:12px; color:var(--text-muted); margin-top:4px;">${t.subject}</div>
                    </div>
                    <div style="display:flex; gap:5px;">
                        <button class="btn-secondary" onclick="editTemplate(${t.id})" style="padding:4px 8px; font-size:12px;">編輯</button>
                        <button class="btn-secondary" onclick="deleteTemplate(${t.id})" style="padding:4px 8px; font-size:12px; color:#ef4444;">刪除</button>
                    </div>
                </div>
            `;
            tagSection.appendChild(item);
        });
        
        container.appendChild(tagSection);
    });
}

async function saveTemplate(e) {
    e.preventDefault();
    
    const templateId = document.getElementById('template-id').value;
    const templateData = {
        name: document.getElementById('template-name').value,
        tag: document.getElementById('template-tag').value,
        subject: document.getElementById('template-subject').value,
        body: document.getElementById('template-body').value,
        is_default: document.getElementById('template-default').checked
    };

    try {
        const url = templateId ? `${API_BASE_URL}/templates/${templateId}` : `${API_BASE_URL}/templates`;
        const method = templateId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: getAuthHeaders(),
            body: JSON.stringify(templateData)
        });

        if (response.ok) {
            document.getElementById('template-form').reset();
            document.getElementById('template-id').value = '';
            fetchTemplates();
            addLog(`✅ 模板${templateId ? '更新' : '新增'}成功`, 'success');
        }
    } catch (error) {
        addLog('❌ 模板儲存失敗: ' + error.message, 'error');
    }
}

async function editTemplate(id) {
    try {
        const response = await fetch(`${API_BASE_URL}/templates`, { headers: getAuthHeaders() });
        const templates = await response.json();
        const template = templates.find(t => t.id === id);
        
        if (template) {
            document.getElementById('template-id').value = template.id;
            document.getElementById('template-name').value = template.name;
            document.getElementById('template-tag').value = template.tag;
            document.getElementById('template-subject').value = template.subject;
            document.getElementById('template-body').value = template.body;
            document.getElementById('template-default').checked = template.is_default;
        }
    } catch (error) {
        console.error('Edit template error:', error);
    }
}

async function deleteTemplate(id) {
    if (!confirm('確定要刪除這個模板嗎？')) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/templates/${id}`, {
            method: 'DELETE',
            headers: getAuthHeaders()
        });

        if (response.ok) {
            fetchTemplates();
            addLog('✅ 模板已刪除', 'success');
        }
    } catch (error) {
        addLog('❌ 刪除失敗: ' + error.message, 'error');
    }
}

// Mark Email as Sent
async function markEmailSent(leadId) {
    try {
        const response = await fetch(`${API_BASE_URL}/leads/${leadId}/mark-sent`, {
            method: 'POST',
            headers: getAuthHeaders()
        });

        if (response.ok) {
            fetchLeads();
            addLog('✅ 已標記為寄信完成', 'success');
        }
    } catch (error) {
        addLog('❌ 標記失敗: ' + error.message, 'error');
    }
}

// --- Email Engagement Tracking ---
async function fetchEngagements() {
    try {
        const response = await fetch(`${API_BASE_URL}/engagements`, { headers: getAuthHeaders() });
        if (!response.ok) throw new Error('Failed');
        const data = await response.json();
        renderEngagementStats(data);
    } catch (error) {
        console.error('Fetch engagements error:', error);
    }
}

function renderEngagementStats(data) {
    // Render tag-level stats
    const container = document.getElementById('engagement-tag-stats');
    const tbody = document.getElementById('engagements-table-body');
    const tagStats = data.tag_stats || {};
    const records = data.records || [];

    // Tag stats summary
    if (Object.keys(tagStats).length === 0) {
        container.innerHTML = '<p style="color:var(--text-muted);">尚無追蹤資料，請先寄送信件</p>';
    } else {
        let html = `<table class="data-table"><thead><tr><th>行業界別</th><th>總數</th><th>開信</th><th>點擊</th><th>回覆</th><th>開信率</th><th>點擊率</th></tr></thead><tbody>`;
        const tagLabels = { 'NA-CABLE': 'Cable', 'NA-NAMEPLATE': 'Nameplate', 'NA-PLASTIC': 'Plastic', 'UNKNOWN': '未知' };
        Object.keys(tagStats).forEach(tag => {
            const s = tagStats[tag];
            const openRate = s.total > 0 ? ((s.opened / s.total) * 100).toFixed(1) + '%' : '0%';
            const clickRate = s.total > 0 ? ((s.clicked / s.total) * 100).toFixed(1) + '%' : '0%';
            let tagClass = 'tag-unknown';
            if (tag === 'NA-CABLE') tagClass = 'tag-cable';
            else if (tag === 'NA-NAMEPLATE') tagClass = 'tag-nameplate';
            else if (tag === 'NA-PLASTIC') tagClass = 'tag-plastic';
            html += `<tr>
                <td><span class="tag-badge ${tagClass}">${tagLabels[tag] || tag}</span></td>
                <td>${s.total}</td>
                <td><span class="level-success">${s.opened}</span></td>
                <td><span class="level-info">${s.clicked}</span></td>
                <td><span style="color:#a78bfa;">${s.replied}</span></td>
                <td><strong>${openRate}</strong></td>
                <td><strong>${clickRate}</strong></td>
            </tr>`;
        });
        html += '</tbody></table>';
        html += `<div style="margin-top:12px; font-size:13px; color:var(--text-muted);">
            總客戶數: <strong style="color:white;">${data.total_leads}</strong> |
            總寄送次數: <strong style="color:white;">${data.total_campaigns}</strong>
        </div>`;
        container.innerHTML = html;
    }

    // Individual records table
    if (records.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; color:var(--text-muted);">尚無追蹤資料</td></tr>';
    } else {
        tbody.innerHTML = '';
        records.forEach(r => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${r.company_name}</td>
                <td>${r.ai_tag}</td>
                <td>${r.opened ? '<span style="color:#10b981;">✓</span>' : '<span style="color:#555;">✗</span>'}</td>
                <td>${r.clicked ? '<span style="color:#3b82f6;">✓</span>' : '<span style="color:#555;">✗</span>'}</td>
                <td>${r.replied ? '<span style="color:#a78bfa;">✓</span>' : '<span style="color:#555;">✗</span>'}</td>
                <td>${r.tracked_at}</td>
            `;
            tbody.appendChild(row);
        });
    }
}

// --- Pricing Config ---
async function loadPricing() {
    try {
        const response = await fetch(`${API_BASE_URL}/pricing`, { headers: getAuthHeaders() });
        if (!response.ok) return;
        const config = await response.json();
        document.getElementById('pricing-base-fee').value = config.base_fee || 1000;
        document.getElementById('pricing-per-lead').value = config.per_lead || 50;
        document.getElementById('pricing-email-open-track').value = config.email_open_track || 10;
        document.getElementById('pricing-email-click-track').value = config.email_click_track || 15;
        document.getElementById('pricing-per-lead-usd').value = config.per_lead_usd || 1.5;
    } catch (error) {
        console.error('Load pricing error:', error);
    }
}

async function savePricing(e) {
    e.preventDefault();
    const status = document.getElementById('pricing-status');
    try {
        const response = await fetch(`${API_BASE_URL}/pricing`, {
            method: 'PUT',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                base_fee: parseInt(document.getElementById('pricing-base-fee').value),
                per_lead: parseInt(document.getElementById('pricing-per-lead').value),
                email_open_track: parseInt(document.getElementById('pricing-email-open-track').value),
                email_click_track: parseInt(document.getElementById('pricing-email-click-track').value),
                per_lead_usd: parseFloat(document.getElementById('pricing-per-lead-usd').value)
            })
        });
        if (response.ok) {
            status.classList.remove('hidden');
            status.className = 'status-msg success';
            status.innerText = '✅ 收費標準已儲存';
            addLog('💰 收費標準已更新', 'success');
            setTimeout(() => status.classList.add('hidden'), 4000);
        }
    } catch (error) {
        status.classList.remove('hidden');
        status.className = 'status-msg error';
        status.innerText = '❌ 儲存失敗';
    }
}

function calcQuote() {
    const count = parseInt(document.getElementById('quote-lead-count').value) || 0;
    const base = parseInt(document.getElementById('pricing-base-fee').value) || 1000;
    const perLead = parseInt(document.getElementById('pricing-per-lead').value) || 50;
    const openTrack = parseInt(document.getElementById('pricing-email-open-track').value) || 10;
    const clickTrack = parseInt(document.getElementById('pricing-email-click-track').value) || 15;
    const perLeadUsd = parseFloat(document.getElementById('pricing-per-lead-usd').value) || 1.5;

    const totalNtd = base + (count * perLead) + (count * openTrack) + (count * clickTrack);
    const totalUsd = (count * perLeadUsd).toFixed(2);

    document.getElementById('quote-result').innerHTML = `
        <div style="padding:12px; background:rgba(255,255,255,0.05); border-radius:8px;">
            <div>基礎費用：<strong>NT$ ${base.toLocaleString()}</strong></div>
            <div>客戶費用：<strong>NT$ ${(count * perLead).toLocaleString()}</strong> (${count} 筆 × NT$ ${perLead})</div>
            <div>開信追蹤：<strong>NT$ ${(count * openTrack).toLocaleString()}</strong> (${count} 筆 × NT$ ${openTrack})</div>
            <div>點擊追蹤：<strong>NT$ ${(count * clickTrack).toLocaleString()}</strong> (${count} 筆 × NT$ ${clickTrack})</div>
            <hr style="border-color:rgba(255,255,255,0.1); margin:8px 0;">
            <div style="font-size:16px; color:#10b981;">💵 總費用：NT$ <strong>${totalNtd.toLocaleString()}</strong></div>
            <div style="font-size:16px; color:#60a5fa;">💵 美元報價：US$ <strong>${totalUsd.toLocaleString()}</strong></div>
        </div>
    `;
}
