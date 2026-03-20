const API_BASE_URL = 'http://localhost:8000/api';

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
    btn.innerHTML = 'Crawling...';

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
        alert('Scraper Error: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '🚀 Start Automated Crawl';
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
    alert('Started AI Email Generation. Depending on API speed this may take a few seconds...');
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
    } catch (error) {
        err.style.display = 'block';
    }
}
