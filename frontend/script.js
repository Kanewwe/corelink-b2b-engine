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
    
    // New: Filters and utilities
    document.getElementById('search-leads')?.addEventListener('input', debounce(fetchLeads, 300));
    document.getElementById('filter-status')?.addEventListener('change', fetchLeads);
    document.getElementById('filter-tag')?.addEventListener('change', fetchLeads);
    document.getElementById('clear-logs-btn')?.addEventListener('click', clearLogs);
    document.getElementById('toggle-password')?.addEventListener('click', togglePasswordVisibility);
    
    // Email strategy toggle
    document.querySelectorAll('input[name="email-strategy"]').forEach(radio => {
        radio.addEventListener('change', updateStrategyDescription);
    });

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

// ══════════════════════════════════════════
// AI Keyword Generator
// ══════════════════════════════════════════

async function generateAIKeywords() {
    const keyword = document.getElementById('scrape-keyword')?.value.trim();
    const resultDiv = document.getElementById('ai-keywords-result');
    const chipsDiv = document.getElementById('keyword-chips');
    const btn = document.getElementById('ai-keyword-btn');
    
    if (!keyword) {
        alert('請先輸入一個產業關鍵字');
        return;
    }
    
    btn.disabled = true;
    btn.innerHTML = '⏳ 生成中...';
    
    try {
        const response = await fetch(`${API_BASE_URL}/keywords/generate`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ keyword })
        });
        
        const result = await response.json();
        
        if (result.success && result.keywords) {
            chipsDiv.innerHTML = '';
            result.keywords.forEach(kw => {
                const chip = document.createElement('label');
                chip.style.cssText = 'display:inline-flex; align-items:center; gap:4px; padding:6px 12px; background:rgba(139,92,246,0.2); border:1px solid rgba(139,92,246,0.4); border-radius:16px; cursor:pointer; font-size:12px;';
                chip.innerHTML = `
                    <input type="checkbox" value="${kw}" checked style="accent-color:#8b5cf6;">
                    <span>${kw}</span>
                `;
                chipsDiv.appendChild(chip);
            });
            
            const customInput = document.createElement('div');
            customInput.style.cssText = 'display:flex; gap:4px;';
            customInput.innerHTML = `
                <input type="text" id="custom-keyword" placeholder="+ 自訂關鍵字" 
                    style="padding:4px 8px; font-size:12px; border-radius:12px; border:1px dashed rgba(139,92,246,0.4); background:transparent; color:#fff; width:120px;">
                <button type="button" onclick="addCustomKeyword()" style="padding:4px 8px; font-size:11px; background:rgba(139,92,246,0.3); border:1px solid rgba(139,92,246,0.4); border-radius:12px; color:#fff; cursor:pointer;">新增</button>
            `;
            chipsDiv.appendChild(customInput);
            
            resultDiv.classList.remove('hidden');
            addLog('✨ 已生成 5 組關鍵字，請選擇要使用的', 'success');
        } else {
            alert('生成失敗：' + (result.message || '未知錯誤'));
        }
    } catch (error) {
        alert('生成失敗：' + error.message);
    }
    
    btn.disabled = false;
    btn.innerHTML = '✨ AI 關鍵字';
}

function addCustomKeyword() {
    const input = document.getElementById('custom-keyword');
    const value = input?.value.trim();
    if (!value) return;
    
    const chipsDiv = document.getElementById('keyword-chips');
    const chip = document.createElement('label');
    chip.style.cssText = 'display:inline-flex; align-items:center; gap:4px; padding:6px 12px; background:rgba(139,92,246,0.2); border:1px solid rgba(139,92,246,0.4); border-radius:16px; cursor:pointer; font-size:12px;';
    chip.innerHTML = `<input type="checkbox" value="${value}" checked style="accent-color:#8b5cf6;"><span>${value}</span>`;
    
    const customInput = chipsDiv.querySelector('div:last-child');
    chipsDiv.insertBefore(chip, customInput);
    input.value = '';
}

function getSelectedKeywords() {
    const checkboxes = document.querySelectorAll('#keyword-chips input[type="checkbox"]:checked');
    return Array.from(checkboxes).map(cb => cb.value);
}

// ══════════════════════════════════════════
// Scrape Functions
// ══════════════════════════════════════════

async function startScrape(e) {
    e.preventDefault();
    const btn = document.getElementById('start-scrape-btn');
    const status = document.getElementById('scrape-status');
    const progress = document.getElementById('miner-progress');
    
    const market = document.getElementById('scrape-market').value;
    const baseKeyword = document.getElementById('scrape-keyword').value;
    const location = document.getElementById('scrape-location')?.value || '';
    const pages = document.getElementById('scrape-pages')?.value || 3;

    // Get selected keywords or use base keyword
    const selectedKeywords = getSelectedKeywords();
    const keywords = selectedKeywords.length > 0 ? selectedKeywords : [baseKeyword];

    btn.disabled = true;
    btn.innerHTML = '🚀 探勘中...';
    
    // Show progress
    if (progress) {
        progress.classList.remove('hidden');
        document.getElementById('miner-status').textContent = '執行中...';
        document.getElementById('miner-progress-bar').style.width = '10%';
    }

    try {
        const response = await fetch(`${API_BASE_URL}/scrape-simple`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                market: market,
                pages: parseInt(pages),
                keywords: keywords,
                location: location
            })
        });

        if (response.ok) {
            status.classList.remove('hidden');
            status.className = 'status-msg success';
            status.innerText = `✅ 探勘任務已啟動！使用 ${keywords.length} 組關鍵字`;
            addLog(`🔍 開始探勘: ${keywords.join(', ')} (${market})`, 'info');
            
            // Update progress
            if (progress) {
                document.getElementById('miner-progress-bar').style.width = '30%';
            }
            
            setTimeout(() => {
                status.classList.add('hidden');
                if (progress) {
                    document.getElementById('miner-progress-bar').style.width = '100%';
                    document.getElementById('miner-status').textContent = '完成';
                }
                fetchLeads();
            }, 10000);
        } else {
            const error = await response.json();
            status.classList.remove('hidden');
            status.className = 'status-msg error';
            status.innerText = `❌ ${error.detail || '啟動失敗'}`;
        }
    } catch (error) {
        addLog('❌ 探勘啟動失敗: ' + error.message, 'error');
        status.classList.remove('hidden');
        status.className = 'status-msg error';
        status.innerText = '❌ 探勘啟動失敗';
    } finally {
        btn.disabled = false;
        btn.innerHTML = '🚀 開始自動探勘';
    }
}

async function fetchLeads() {
    try {
        // Get filter values
        const search = document.getElementById('search-leads')?.value || '';
        const statusFilter = document.getElementById('filter-status')?.value || '';
        const tagFilter = document.getElementById('filter-tag')?.value || '';
        
        const response = await fetch(`${API_BASE_URL}/leads`, { headers: getAuthHeaders() });
        if (response.status === 401) {
            handleLogout();
            return;
        }
        let leads = await response.json();
        
        // Apply filters
        if (search) {
            leads = leads.filter(l => l.company_name.toLowerCase().includes(search.toLowerCase()));
        }
        if (statusFilter) {
            leads = leads.filter(l => l.status === statusFilter);
        }
        if (tagFilter) {
            if (tagFilter === 'AUTO') {
                leads = leads.filter(l => l.ai_tag && l.ai_tag.startsWith('AUTO'));
            } else {
                leads = leads.filter(l => l.ai_tag === tagFilter);
            }
        }
        
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
        else if (lead.ai_tag && lead.ai_tag.startsWith('AUTO')) tagClass = 'tag-auto';

        const card = document.createElement('div');
        card.className = 'lead-card';
        
        const emailSentBadge = lead.email_sent ? '<span style="background:#10b981; color:white; padding:2px 8px; border-radius:4px; font-size:11px; margin-left:8px;">✓ 已寄信</span>' : '';
        const assignedBD = lead.assigned_bd || '尚未指派';
        const keywords = lead.extracted_keywords || '無';
        
        // NEW: Contact info display
        const contactInfo = lead.contact_name 
            ? `<div style="margin-top:5px; font-size:12px;">👤 聯絡人: <strong>${lead.contact_name}</strong> ${lead.contact_role ? `(${lead.contact_role})` : ''}</div>`
            : (lead.contact_role ? `<div style="margin-top:5px; font-size:12px;">👤 角色: ${lead.contact_role}</div>` : '');
        
        const phoneInfo = lead.phone ? `<div style="margin-top:5px; font-size:12px;">📞 電話: ${lead.phone}</div>` : '';
        const addressInfo = lead.address ? `<div style="margin-top:5px; font-size:12px;">📍 地址: ${lead.address}${lead.city ? `, ${lead.city}` : ''}</div>` : '';
        const sourceInfo = lead.source_domain ? `<div style="font-size:11px; color:var(--text-muted); margin-top:5px;">來源: ${lead.source_domain}</div>` : '';
        
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
                ${contactInfo}
                ${phoneInfo}
                ${addressInfo}
                ${sourceInfo}
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
        container.innerHTML = '<p style="color:var(--text-muted);">尚無模板，請先新增</p>';
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
        else if (tag.startsWith('AUTO')) tagClass = 'tag-auto';
        
        tagSection.innerHTML = `<h4 style="margin-bottom:10px;"><span class="tag-badge ${tagClass}">${tag}</span></h4>`;
        
        grouped[tag].forEach(t => {
            const item = document.createElement('div');
            item.style.cssText = 'padding:12px; background:rgba(255,255,255,0.05); border-radius:6px; margin-bottom:8px;';
            
            const defaultToggle = `
                <label style="display:flex; align-items:center; gap:6px; cursor:pointer; margin-top:8px;">
                    <input type="checkbox" 
                        ${t.is_default ? 'checked' : ''} 
                        onchange="toggleDefault(${t.id}, this.checked)"
                        style="accent-color:#10b981;">
                    <span style="font-size:12px; color:var(--text-muted);">預設模板</span>
                </label>
            `;
            
            item.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div style="flex:1;">
                        <div style="display:flex; align-items:center; gap:8px;">
                            <strong>${t.name}</strong>
                            ${t.is_default ? '<span style="background:#10b981; color:white; padding:2px 8px; border-radius:4px; font-size:10px;">預設</span>' : ''}
                        </div>
                        <div style="font-size:12px; color:var(--text-muted); margin-top:4px;">${t.subject}</div>
                        ${defaultToggle}
                    </div>
                    <div style="display:flex; gap:5px; margin-left:10px;">
                        <button class="btn-secondary" onclick="editTemplate(${t.id})" style="padding:4px 8px; font-size:11px;">編輯</button>
                        <button class="btn-secondary" onclick="duplicateTemplate(${t.id})" style="padding:4px 8px; font-size:11px;">複製</button>
                        <button class="btn-secondary" onclick="deleteTemplate(${t.id})" style="padding:4px 8px; font-size:11px; color:#ef4444;">刪除</button>
                    </div>
                </div>
            `;
            tagSection.appendChild(item);
        });
        
        container.appendChild(tagSection);
    });
}

async function toggleDefault(templateId, isDefault) {
    try {
        const response = await fetch(`${API_BASE_URL}/templates/${templateId}`, {
            method: 'PUT',
            headers: getAuthHeaders(),
            body: JSON.stringify({ 
                name: '', 
                tag: '', 
                subject: '', 
                body: '',
                is_default: isDefault 
            })
        });
        
        if (response.ok) {
            fetchTemplates();
            addLog(`✅ 預設模板已${isDefault ? '設為' : '取消'}: ID ${templateId}`, 'success');
        }
    } catch (error) {
        addLog('❌ 更新預設失敗: ' + error.message, 'error');
    }
}

async function duplicateTemplate(id) {
    try {
        const response = await fetch(`${API_BASE_URL}/templates`, { headers: getAuthHeaders() });
        const templates = await response.json();
        const template = templates.find(t => t.id === id);
        
        if (template) {
            // Create duplicate
            const createResponse = await fetch(`${API_BASE_URL}/templates`, {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify({
                    name: template.name + ' (複製)',
                    tag: template.tag,
                    subject: template.subject,
                    body: template.body,
                    is_default: false
                })
            });
            
            if (createResponse.ok) {
                fetchTemplates();
                addLog('✅ 模板已複製', 'success');
            }
        }
    } catch (error) {
        addLog('❌ 複製失敗: ' + error.message, 'error');
    }
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

function clearLogs() {
    const console = document.getElementById('system-console');
    console.innerHTML = '<span style="color:var(--text-muted);">日誌已清除</span>';
    addLog('🗑️ 日誌已清除', 'info');
}

function togglePasswordVisibility() {
    const input = document.getElementById('smtp-password');
    const btn = document.getElementById('toggle-password');
    if (input.type === 'password') {
        input.type = 'text';
        btn.textContent = '🙈';
    } else {
        input.type = 'password';
        btn.textContent = '👁';
    }
}

function updateStrategyDescription() {
    const strategy = document.querySelector('input[name="email-strategy"]:checked')?.value || 'free';
    const desc = document.getElementById('strategy-desc');
    
    if (strategy === 'free') {
        desc.innerHTML = `
            <strong>免費模式：</strong>三層策略（官網爬取 → SMTP驗活 → Google Dork）<br>
            <span style="color:#10b981;">✓ 完全免費</span> · 
            <span style="color:#f59e0b;">~60% 準確率</span> · 
            <span style="color:#60a5fa;">5-20秒/筆</span>
        `;
    } else {
        desc.innerHTML = `
            <strong>Hunter.io：</strong>專業 Email 發現 API<br>
            <span style="color:#ef4444;">$49/月起</span> · 
            <span style="color:#10b981;">~90% 準確率</span> · 
            <span style="color:#60a5fa;">&lt;1秒/筆</span> · 
            <span style="color:var(--text-muted);">含聯絡人姓名</span>
        `;
    }
}

function getEmailStrategy() {
    return document.querySelector('input[name="email-strategy"]:checked')?.value || 'free';
}

// ══════════════════════════════════════════
// Template v2 Functions
// ══════════════════════════════════════════

let originalHTML = '';
let editorMode = 'split';
let monacoEditor = null;

// Initialize Monaco Editor
async function initMonacoEditor() {
    const container = document.getElementById('monaco-container');
    if (!container || monacoEditor) return;
    
    // Load Monaco
    if (!window.monaco) {
        await loadMonaco();
    }
    
    monacoEditor = window.monaco.editor.create(container, {
        value: originalHTML || '<!-- 在此輸入 HTML 或讓 AI 生成 -->',
        language: 'html',
        theme: 'vs-dark',
        automaticLayout: true,
        minimap: { enabled: false },
        fontSize: 13,
        lineNumbers: 'on',
        wordWrap: 'on',
        tabSize: 2,
        scrollBeyondLastLine: false,
        renderWhitespace: 'selection',
        bracketPairColorization: { enabled: true }
    });
    
    // Update preview on change
    monacoEditor.onDidChangeModelContent(() => {
        updatePreview();
    });
}

async function loadMonaco() {
    return new Promise((resolve) => {
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/monaco-editor@0.45.0/min/vs/loader.js';
        script.onload = () => {
            require.config({ 
                paths: { 
                    vs: 'https://cdn.jsdelivr.net/npm/monaco-editor@0.45.0/min/vs' 
                }
            });
            require(['vs/editor/editor.main'], () => {
                resolve();
            });
        };
        document.body.appendChild(script);
    });
}

function getEditorContent() {
    if (monacoEditor) {
        return monacoEditor.getValue();
    }
    return document.getElementById('html-editor')?.value || '';
}

function setEditorContent(content) {
    if (monacoEditor) {
        monacoEditor.setValue(content);
    } else {
        const editor = document.getElementById('html-editor');
        if (editor) editor.value = content;
    }
}

function switchTemplateTab(tab) {
    document.querySelectorAll('.template-tab-content').forEach(el => el.classList.add('hidden'));
    document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
    
    document.getElementById(`template-${tab}-tab`)?.classList.remove('hidden');
    document.getElementById(`tab-${tab}`)?.classList.add('active');
    
    if (tab === 'list') fetchTemplates();
    if (tab === 'attachments') loadAttachments();
}

function setEditorMode(mode) {
    editorMode = mode;
    const container = document.getElementById('editor-container');
    const editor = document.getElementById('html-editor-wrapper');
    const preview = document.getElementById('preview-wrapper');
    
    document.querySelectorAll('[id^="mode-"]').forEach(btn => btn.classList.remove('active'));
    document.getElementById(`mode-${mode}`)?.classList.add('active');
    
    if (mode === 'edit') {
        container.style.gridTemplateColumns = '1fr';
        editor.style.display = 'flex';
        preview.style.display = 'none';
    } else if (mode === 'preview') {
        container.style.gridTemplateColumns = '1fr';
        editor.style.display = 'none';
        preview.style.display = 'flex';
    } else {
        container.style.gridTemplateColumns = '1fr 1fr';
        editor.style.display = 'flex';
        preview.style.display = 'flex';
    }
    
    updatePreview();
}

function updatePreview() {
    const html = getEditorContent();
    const iframe = document.getElementById('preview-iframe');
    
    if (iframe) {
        // Replace variables with test data for preview
        const previewHTML = html
            .replace(/\{\{company_name\}\}/g, 'Test Company')
            .replace(/\{\{bd_name\}\}/g, 'John Doe')
            .replace(/\{\{keywords\}\}/g, 'cable, wire, harness')
            .replace(/\{\{description\}\}/g, 'A leading manufacturer of custom cable assemblies.');
        
        iframe.srcdoc = previewHTML;
    }
}

function insertVariable(varName) {
    const variable = `{{${varName}}}`;
    
    if (monacoEditor) {
        const position = monacoEditor.getPosition();
        monacoEditor.executeEdits('', [{
            range: new window.monaco.Range(
                position.lineNumber, 
                position.column, 
                position.lineNumber, 
                position.column
            ),
            text: variable
        }]);
        monacoEditor.focus();
    } else {
        const editor = document.getElementById('html-editor');
        if (editor) {
            const start = editor.selectionStart;
            const end = editor.selectionEnd;
            const text = editor.value;
            
            editor.value = text.substring(0, start) + variable + text.substring(end);
            editor.selectionStart = editor.selectionEnd = start + variable.length;
            editor.focus();
        }
    }
    updatePreview();
}

function formatHTML() {
    let html = getEditorContent();
    
    // Basic HTML formatting - add proper indentation
    html = html.replace(/>\s+</g, '>\n<');
    html = html.replace(/\n\s*\n/g, '\n');
    
    // Indent tags
    const lines = html.split('\n');
    let indent = 0;
    const formatted = lines.map(line => {
        const trimmed = line.trim();
        if (trimmed.match(/^<\//)) indent = Math.max(0, indent - 1);
        const result = '  '.repeat(indent) + trimmed;
        if (trimmed.match(/^<[^\/!][^>]*[^\/]>$/)) indent++;
        return result;
    }).join('\n');
    
    setEditorContent(formatted);
    updatePreview();
    addLog('📝 HTML 已格式化', 'info');
}

function restoreOriginal() {
    if (originalHTML) {
        setEditorContent(originalHTML);
        updatePreview();
        addLog('↩️ 已復原到 AI 原始版本', 'info');
    }
}

// AI Generate Template
async function aiGenerateTemplate() {
    const prompt = document.getElementById('ai-prompt-input')?.value;
    const style = document.getElementById('ai-style')?.value || 'professional';
    const language = document.getElementById('ai-language')?.value || 'english';
    const status = document.getElementById('ai-status');
    
    if (!prompt) {
        status.classList.remove('hidden');
        status.className = 'status-msg error';
        status.innerText = '請輸入信件需求描述';
        return;
    }
    
    status.classList.remove('hidden');
    status.className = 'status-msg';
    status.innerText = '⏳ AI 正在生成中...';
    
    try {
        const response = await fetch(`${API_BASE_URL}/templates/ai-generate`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ prompt, style, language })
        });
        
        const result = await response.json();
        
        if (result.success) {
            setEditorContent(result.html);
            originalHTML = result.html; // Save for restore
            updatePreview();
            
            status.className = 'status-msg success';
            status.innerText = '✅ AI 已生成草稿，可在下方編輯器調整';
            addLog('✨ AI 模板生成成功', 'success');
        } else {
            status.className = 'status-msg error';
            status.innerText = `❌ ${result.message}`;
        }
    } catch (error) {
        status.className = 'status-msg error';
        status.innerText = `❌ 生成失敗: ${error.message}`;
    }
}

// Save Template v2
async function saveTemplateV2() {
    const name = document.getElementById('template-name')?.value;
    const tag = document.getElementById('template-tag')?.value;
    const subject = document.getElementById('template-subject')?.value;
    const body = getEditorContent();
    const isDefault = document.getElementById('template-default')?.checked;
    
    const status = document.getElementById('template-status');
    
    if (!name || !tag || !subject || !body) {
        status.classList.remove('hidden');
        status.className = 'status-msg error';
        status.innerText = '請填寫所有必填欄位';
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/templates`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                name,
                tag,
                subject,
                body,
                is_default: isDefault
            })
        });
        
        if (response.ok) {
            status.classList.remove('hidden');
            status.className = 'status-msg success';
            status.innerText = '✅ 模板已儲存';
            addLog(`💾 模板已儲存: ${name}`, 'success');
            
            // Clear form
            document.getElementById('template-name').value = '';
            document.getElementById('template-subject').value = '';
            document.getElementById('html-editor').value = '';
            document.getElementById('ai-prompt-input').value = '';
            updatePreview();
        } else {
            const error = await response.json();
            status.classList.remove('hidden');
            status.className = 'status-msg error';
            status.innerText = `❌ ${error.detail || '儲存失敗'}`;
        }
    } catch (error) {
        status.classList.remove('hidden');
        status.className = 'status-msg error';
        status.innerText = `❌ 儲存失敗: ${error.message}`;
    }
}

// Send Test Email
async function sendTestEmail() {
    const status = document.getElementById('template-status');
    status.classList.remove('hidden');
    status.className = 'status-msg';
    status.innerText = '📧 正在寄送測試信...';
    
    try {
        const response = await fetch(`${API_BASE_URL}/templates/test-send`, {
            method: 'POST',
            headers: getAuthHeaders()
        });
        
        const result = await response.json();
        
        if (result.success) {
            status.className = 'status-msg success';
            status.innerText = `✅ ${result.message}`;
            addLog('📧 測試信已寄送', 'success');
        } else {
            status.className = 'status-msg error';
            status.innerText = `❌ ${result.message}`;
        }
    } catch (error) {
        status.className = 'status-msg error';
        status.innerText = `❌ 寄送失敗: ${error.message}`;
    }
}

// File Upload
function handleDragOver(e) {
    e.preventDefault();
    document.getElementById('upload-dropzone')?.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    document.getElementById('upload-dropzone')?.classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    document.getElementById('upload-dropzone')?.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    handleFiles(files);
}

function handleFileSelect(e) {
    const files = e.target.files;
    handleFiles(files);
}

function handleFiles(files) {
    // For now, just log - file upload would need backend storage
    addLog(`📁 選擇了 ${files.length} 個檔案`, 'info');
    
    const list = document.getElementById('uploaded-files-list');
    list.innerHTML = '';
    
    Array.from(files).forEach(file => {
        const item = document.createElement('div');
        item.className = 'file-item';
        item.innerHTML = `
            <div>
                <span style="margin-right:8px;">📄</span>
                <strong>${file.name}</strong>
                <span style="color:var(--text-muted); margin-left:8px;">${(file.size / 1024).toFixed(1)}KB</span>
            </div>
            <div>
                <label style="display:flex; align-items:center; gap:4px; cursor:pointer; margin-right:10px;">
                    <input type="checkbox" checked>
                    <span style="font-size:12px;">預設夾帶</span>
                </label>
                <button class="btn-secondary" style="padding:2px 8px; font-size:11px;">刪除</button>
            </div>
        `;
        list.appendChild(item);
    });
}

function loadAttachments() {
    // Load existing attachments - placeholder
    const list = document.getElementById('uploaded-files-list');
    if (list && list.children.length === 0) {
        list.innerHTML = '<p style="color:var(--text-muted); font-size:12px;">尚無上傳檔案</p>';
    }
}

// Initialize template page
document.getElementById('ai-generate-btn')?.addEventListener('click', aiGenerateTemplate);
document.getElementById('ai-clear-btn')?.addEventListener('click', () => {
    document.getElementById('ai-prompt-input').value = '';
    document.getElementById('ai-status').classList.add('hidden');
});
document.getElementById('upload-dropzone')?.addEventListener('click', () => {
    document.getElementById('file-input')?.click();
});

// Init Monaco on templates view
document.getElementById('nav-templates')?.addEventListener('click', () => {
    setTimeout(initMonacoEditor, 100);
});
