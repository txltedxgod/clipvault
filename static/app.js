const API = '/api';
let currentId = null;
let debounceTimer = null;

const $ = id => document.getElementById(id);

async function fetchJSON(url, opts = {}) {
    const res = await fetch(url, {
        headers: { 'Content-Type': 'application/json' },
        ...opts
    });
    if (!res.ok) throw new Error(res.statusText);
    return res.json();
}

async function loadSnippets(q = '', tag = '') {
    let url = `${API}/snippets?limit=100`;
    if (q) url += `&q=${encodeURIComponent(q)}`;
    if (tag) url += `&tag=${encodeURIComponent(tag)}`;

    const snippets = await fetchJSON(url);
    const list = $('snippetList');
    list.innerHTML = '';

    snippets.forEach(s => {
        const div = document.createElement('div');
        div.className = 'snippet-item' + (s.id === currentId ? ' active' : '');
        div.onclick = () => selectSnippet(s);

        const title = s.title || 'untitled';
        const date = new Date(s.created_at).toLocaleDateString();
        const tagsHtml = s.tags.map(t => `<span class="tag">${t}</span>`).join('');

        div.innerHTML = `
            <div class="title">${title}</div>
            <div class="meta">${s.language} · ${date}</div>
            <div class="tags">${tagsHtml}</div>
        `;
        list.appendChild(div);
    });
}

function selectSnippet(s) {
    currentId = s.id;
    $('titleInput').value = s.title || '';
    $('contentArea').value = s.content;
    $('langSelect').value = s.language;
    $('tagInput').value = s.tags.join(', ');

    document.querySelectorAll('.snippet-item').forEach(el => el.classList.remove('active'));
    // find and highlight
    const items = document.querySelectorAll('.snippet-item');
    items.forEach(el => {
        if (el.querySelector('.title').textContent === (s.title || 'untitled')) {
            el.classList.add('active');
        }
    });
}

async function loadTags() {
    const tags = await fetchJSON(`${API}/tags`);
    const sel = $('tagFilter');
    sel.innerHTML = '<option value="">all tags</option>';
    tags.forEach(t => {
        const opt = document.createElement('option');
        opt.value = t.name;
        opt.textContent = t.name;
        sel.appendChild(opt);
    });
}

$('newBtn').onclick = () => {
    currentId = null;
    $('titleInput').value = '';
    $('contentArea').value = '';
    $('langSelect').value = 'text';
    $('tagInput').value = '';
    $('contentArea').focus();
};

$('saveBtn').onclick = async () => {
    const payload = {
        title: $('titleInput').value || null,
        content: $('contentArea').value,
        language: $('langSelect').value,
        tags: $('tagInput').value.split(',').map(t => t.trim()).filter(Boolean)
    };

    if (!payload.content) return;

    if (currentId) {
        await fetchJSON(`${API}/snippets/${currentId}`, {
            method: 'PUT',
            body: JSON.stringify(payload)
        });
    } else {
        const created = await fetchJSON(`${API}/snippets`, {
            method: 'POST',
            body: JSON.stringify(payload)
        });
        currentId = created.id;
    }

    await loadSnippets();
    await loadTags();
};

$('deleteBtn').onclick = async () => {
    if (!currentId) return;
    if (!confirm('delete this snippet?')) return;

    await fetchJSON(`${API}/snippets/${currentId}`, { method: 'DELETE' });
    currentId = null;
    $('titleInput').value = '';
    $('contentArea').value = '';
    $('tagInput').value = '';
    await loadSnippets();
    await loadTags();
};

$('searchInput').addEventListener('input', (e) => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
        loadSnippets(e.target.value, $('tagFilter').value);
    }, 300);
});

$('tagFilter').addEventListener('change', () => {
    loadSnippets($('searchInput').value, $('tagFilter').value);
});

// mount static files
// (fastapi needs to serve the static dir)

loadSnippets();
loadTags();
