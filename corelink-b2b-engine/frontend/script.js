const API_BASE_URL = window.location.origin + '/api';

function getAuthHeaders() {
    const token = localStorage.getItem('corelink_token');
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    };
}

document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('corelink_token');
    const username = localStorage.getItem('corelink_user');

    if (!token) {
        document.getElementById('login-modal').classList.remove('hidden');
    } else {
        document.getElementById('display-username').innerText = username;
        fetchLeads();
        startLogPolling();
    }

    document.getElementById('login-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        await handleLogin();
    });

    document.getElementById('logout-btn')?.addEventListener('click', () => {
        localStorage.removeItem('corelink_token');
        localStorage.removeItem('corelink_user');
        window.location.reload();
    });

    // Navigation Tabs
    document.getElementById('nav-lead-engine')?.addEventListener('click', (e) => {
        e.preventDefault();
        switchView('lead-engine');
    });

    document.getElementById('nav-campaigns')?.addEventListener('click', (e) => {
        e.preventDefault();
        switchView('campaigns');
    });

    document.getElementById('refresh-logs-btn')?.addEventListener('click', fetchCampaignLogs);

    document.getElementById('lead-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        await submitLead();
    });

    document.getElementById('scrape-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        await startScrape();
    });

    document.getElementById('refresh-btn').addEventListener('click', fetchLeads);

    document.querySelectorAll('.close-btn').forEach(btn => {
        btn.addEventListener('click', closeModal);
    });
});

async function submitLead() {
    const companyName = document.getElementById('company-name').value;
    const websiteUrl = document.getElementById('website-url').value;
    const description = document.getElementById('description').value;

    const loading = document.getElementById('ai-loading');
    const submitBtn = document.getElementById('submit-lead-btn');

    loading.classList.remove('hidden');
    submitBtn.disabled = true;

    try {
        const response = await fetch(`${API_BASE_URL}/leads`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                company_name: companyName,
                website_url: websiteUrl,
                description: description
            })
        });

        if (!response.ok) throw new Error('API Error');

        document.getElementById('lead-form').reset();
        await fetchLeads();

    } catch (error) {
        alert('Could not submit lead! Please ensure the Python backend is running. Details: ' + error.message);
    } finally {
        loading.classList.add('hidden');
        submitBtn.disabled = false;
    }
}

async function startScrape() {
    const url = document.getElementById('scrape-url').value;
    const pages = parseInt(document.getElementById('scrape-pages').value, 10);
    const btn = document.getElementById('start-scrape-btn');
    const statusMsg = document.getElementById('scrape-status');

    btn.disabled = true;
    btn.innerHTML = '🚀 背景抓取中 (Crawling)...';

    try {
        const response = await fetch(`${API_BASE_URL}/scrape`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ search_url: url, max_pages: pages })
        });

        if (!response.ok) throw new Error('Failed to start scraper');

        statusMsg.style.display = 'block';
        setTimeout(() => { statusMsg.style.display = 'none'; }, 8000);

    } catch (error) {
        alert('抓取發生錯誤 (Scraper Error): ' + error.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '🚀 執行背景爬蟲 (Start Crawling)';
    }
}

async function fetchLeads() {
    try {
        const response = await fetch(`${API_BASE_URL}/leads`, { headers: getAuthHeaders() });
        if (response.status === 401) {
            localStorage.removeItem('corelink_token');
            window.location.reload();
            return;
        }
        const leads = await response.json();
        renderLeads(leads);
    } catch (error) {
        console.warn('Backend not reachable. Display format may be empty.', error);
    }
}

function renderLeads(leads) {
    const listContainer = document.getElementById('leads-list');
    listContainer.innerHTML = '';

    if (!leads || leads.length === 0) {
        listContainer.innerHTML = '<p style="color: var(--text-muted); text-align: center; margin-top: 2rem;">No prospects yet. Analyze one to begin.</p>';
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
                Assignee: <strong>${lead.assigned_bd}</strong> | Status: <strong>${lead.status.replace('_', ' ')}</strong>
                <br>
                <div style="margin-top:5px; font-size:12px;">Keywords: <span style="color:#cbd5e1">${lead.extracted_keywords || 'None'}</span></div>
            </div>
            <div class="lead-actions">
                ${lead.status === 'Tagged' || lead.status === 'Scraped'
                ? `<button class="btn-primary generate-btn" onclick="generateEmail(${lead.id})">✨ Auto-Draft Outreach</button>`
                : `<button class="btn-secondary" onclick="viewEmail(${lead.id})">✉️ View Draft</button>`
            }
            </div>
        `;
        listContainer.appendChild(card);
    });
}

async function generateEmail(leadId) {
    alert('通知: 正在呼叫 AI 模型為此客戶生成含有專屬關鍵字的內容。可能需要數秒鐘...');
    try {
        const response = await fetch(`${API_BASE_URL}/leads/${leadId}/generate-email`, {
            method: 'POST',
            headers: getAuthHeaders()
        });
        if (!response.ok) throw new Error('AI Generation failed Check API logs.');

        const campaign = await response.json();
        await fetchLeads();
        openModal(campaign.subject, campaign.content);
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

async function viewEmail(leadId) {
    try {
        const response = await fetch(`${API_BASE_URL}/leads/${leadId}/emails`, { headers: getAuthHeaders() });
        const campaigns = await response.json();

        if (campaigns && campaigns.length > 0) {
            const latest = campaigns[campaigns.length - 1];
            openModal(latest.subject, latest.content);
        } else {
            alert('No emails found for this lead.');
        }
    } catch (error) {
        alert('Error loading email: ' + error.message);
    }
}

function openModal(subject, body) {
    document.getElementById('modal-subject').value = subject;
    document.getElementById('modal-body').value = body;
    document.getElementById('email-modal').classList.remove('hidden');
}

function closeModal() {
    document.getElementById('email-modal').classList.add('hidden');
}

function switchView(viewName) {
    document.getElementById('nav-lead-engine').classList.remove('active');
    document.getElementById('nav-campaigns').classList.remove('active');
    document.getElementById('lead-engine-view').classList.add('hidden');
    document.getElementById('campaign-logs-view').classList.add('hidden');

    if (viewName === 'lead-engine') {
        document.getElementById('nav-lead-engine').classList.add('active');
        document.getElementById('lead-engine-view').classList.remove('hidden');
        fetchLeads();
    } else if (viewName === 'campaigns') {
        document.getElementById('nav-campaigns').classList.add('active');
        document.getElementById('campaign-logs-view').classList.remove('hidden');
        fetchCampaignLogs();
    }
}

async function fetchCampaignLogs() {
    const tbody = document.getElementById('logs-table-body');
    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:20px;">Fetching global dispatch records...</td></tr>';

    try {
        const response = await fetch(`${API_BASE_URL}/campaigns`, { headers: getAuthHeaders() });
        if (!response.ok) throw new Error('API Error');
        const logs = await response.json();

        tbody.innerHTML = '';
        if (logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:20px; color:var(--text-muted);">No outgoing campaigns recorded yet.</td></tr>';
            return;
        }

        logs.forEach(log => {
            let statusColor = log.status === 'Sent' ? '#10b981' : '#f59e0b';
            let formattedTime = log.created_at || 'Just now';

            const tr = document.createElement('tr');
            tr.style.borderBottom = '1px solid rgba(255,255,255,0.05)';
            tr.innerHTML = `
                <td style="padding:12px 8px; color:var(--text-muted);">${formattedTime}</td>
                <td style="padding:12px 8px; font-weight:600;">${log.company_name}</td>
                <td style="padding:12px 8px;">${log.assigned_bd}</td>
                <td style="padding:12px 8px; max-width:250px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${log.subject}</td>
                <td style="padding:12px 8px;"><span style="color:${statusColor}; font-weight:bold;">${log.status}</span></td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding:20px; color:#ef4444;">Failed to load logs. Ensure backend is running.</td></tr>`;
    }
}

async function handleLogin() {
    const user = document.getElementById('login-username').value;
    const pass = document.getElementById('login-password').value;
    const err = document.getElementById('login-error');
    err.style.display = 'none';

    try {
        const res = await fetch(`${API_BASE_URL}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: user, password: pass })
        });
        if (!res.ok) throw new Error('Invalid credentials');

        const data = await res.json();
        localStorage.setItem('corelink_token', data.token);
        localStorage.setItem('corelink_user', data.username);

        document.getElementById('login-modal').classList.add('hidden');
        document.getElementById('display-username').innerText = data.username;
        fetchLeads();
        startLogPolling();
    } catch (error) {
        err.style.display = 'block';
    }
}

let logInterval = null;
function startLogPolling() {
    if (logInterval) clearInterval(logInterval);
    fetchSystemLogs();
    logInterval = setInterval(fetchSystemLogs, 4000);
}

async function fetchSystemLogs() {
    const consoleDiv = document.getElementById('system-console');
    if (!consoleDiv) return;

    try {
        const response = await fetch(`${API_BASE_URL}/system-logs`, { headers: getAuthHeaders() });
        if (!response.ok) return;
        const data = await response.json();
        const logs = data.logs || [];

        if (logs.length > 0) {
            // Newest logs on top for the console feel
            consoleDiv.innerHTML = logs.slice().reverse().join('<br>');
        } else {
            consoleDiv.innerHTML = '<span style="color:var(--text-muted)">等待系統事件觸發... (如: 開始爬蟲或發信排程)</span>';
        }
    } catch (e) {
        consoleDiv.innerHTML = '<span style="color:#ef4444;">連線中斷，正在嘗試重新連線...</span>';
    }
}
