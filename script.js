/**
 * ─── Authentication ──────────────────────────────────────────────────────────
 */

async function doLogin(event) {
  event.preventDefault();
  const password = document.getElementById('password').value;
  const loginBtn = document.getElementById('loginBtn');
  const errorEl = document.getElementById('loginError');

  // UI state
  errorEl.style.display = 'none';
  loginBtn.disabled = true;
  loginBtn.querySelector('.btn-text').style.display = 'none';
  loginBtn.querySelector('.btn-spinner').style.display = 'inline-block';

  try {
    const response = await fetch('/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password })
    });

    const data = await response.json();

    if (data.success) {
      showUploadSection();
    } else {
      errorEl.textContent = data.message || 'Login failed';
      errorEl.style.display = 'block';
    }
  } catch (err) {
    errorEl.textContent = 'Server error. Please try again.';
    errorEl.style.display = 'block';
  } finally {
    loginBtn.disabled = false;
    loginBtn.querySelector('.btn-text').style.display = 'inline-block';
    loginBtn.querySelector('.btn-spinner').style.display = 'none';
  }
}

async function doLogout() {
  await fetch('/logout', { method: 'POST' });
  location.reload();
}

function showUploadSection() {
  document.getElementById('loginSection').style.display = 'none';
  document.getElementById('uploadSection').style.display = 'block';
  document.getElementById('logoutBtn').style.display = 'block';
  loadTeacherPapers();
}

function togglePasswordVisibility() {
  const pwd = document.getElementById('password');
  pwd.type = pwd.type === 'password' ? 'text' : 'password';
}

/**
 * ─── Upload Logic ────────────────────────────────────────────────────────────
 */

function handleFileSelect(input) {
  const display = document.getElementById('fileNameDisplay');
  if (input.files.length) {
    display.textContent = `Selected: ${input.files[0].name} (${(input.files[0].size / 1024 / 1024).toFixed(2)} MB)`;
    display.style.display = 'block';
  } else {
    display.style.display = 'none';
  }
}

async function doUpload(event) {
  event.preventDefault();
  const form = event.target;
  const formData = new FormData(form);
  const msgEl = document.getElementById('uploadMessage');
  const progressWrapper = document.getElementById('uploadProgress');
  const progressFill = document.getElementById('progressFill');
  const progressText = document.getElementById('progressText');
  const btn = document.getElementById('uploadBtn');

  msgEl.style.display = 'none';
  progressWrapper.style.display = 'block';
  btn.disabled = true;

  const xhr = new XMLHttpRequest();
  xhr.open('POST', '/upload', true);

  xhr.upload.onprogress = (e) => {
    if (e.lengthComputable) {
      const percent = (e.loaded / e.total) * 100;
      progressFill.style.width = percent + '%';
      progressText.textContent = `Uploading: ${Math.round(percent)}%`;
    }
  };

  xhr.onload = () => {
    btn.disabled = false;
    let res = {};
    try {
      res = JSON.parse(xhr.responseText);
    } catch (e) {
      res = { error: "Server returned an invalid response" };
    }

    if (xhr.status === 200 && res.success) {
      msgEl.className = 'alert alert-success';
      msgEl.textContent = '✅ ' + res.message;
      msgEl.style.display = 'block';
      form.reset();
      document.getElementById('fileNameDisplay').style.display = 'none';
      progressWrapper.style.display = 'none';
      loadTeacherPapers();
    } else {
      msgEl.className = 'alert alert-error';
      msgEl.textContent = '❌ ' + (res.error || 'Upload failed');
      msgEl.style.display = 'block';
    }
  };

  xhr.onerror = () => {
    btn.disabled = false;
    msgEl.className = 'alert alert-error';
    msgEl.textContent = '❌ Network error during upload';
    msgEl.style.display = 'block';
  };

  xhr.send(formData);
}

/**
 * ─── Search Logic ────────────────────────────────────────────────────────────
 */

async function doSearch(event) {
  if (event) event.preventDefault();
  
  const form = document.getElementById('searchForm');
  const query = new URLSearchParams(new FormData(form)).toString();
  const grid = document.getElementById('papersGrid');
  const errorEl = document.getElementById('searchError');
  const header = document.getElementById('resultsHeader');
  const countBadge = document.getElementById('resultsCount');

  grid.innerHTML = '<div class="empty-state">Searching...</div>';
  errorEl.style.display = 'none';

  try {
    const response = await fetch(`/search?${query}`);
    const data = await response.json();

    if (data.success) {
      renderPapers(data.papers, grid);
      header.style.display = 'flex';
      countBadge.textContent = `${data.papers.length} result(s)`;
    } else {
      errorEl.textContent = data.error || 'Search failed';
      errorEl.style.display = 'block';
    }
  } catch (err) {
    errorEl.textContent = 'Server error. Could not fetch results.';
    errorEl.style.display = 'block';
  }
}

function clearSearch() {
  document.getElementById('searchForm').reset();
  doSearch();
}

/**
 * ─── Data Rendering ──────────────────────────────────────────────────────────
 */

function renderPapers(papers, container, isTeacher = false) {
  if (!papers || papers.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">🏜️</div>
        <p>No question papers found.</p>
        <p class="empty-hint">Try adjusting your search filters.</p>
      </div>`;
    return;
  }

  container.innerHTML = papers.map(p => `
    <div class="paper-card">
      ${isTeacher ? `<button class="delete-btn" onclick="deletePaper(${p.id})">🗑️ Delete</button>` : ''}
      <span class="tag">${p.exam_type}</span>
      <h3>${p.subject}</h3>
      <div class="paper-info">
        <div>Year: <span>${p.year}</span></div>
        <div>Sem: <span>${p.semester}</span></div>
        <div>Branch: <span>${p.branch}</span></div>
        <div>Month: <span>${p.month}</span></div>
      </div>
      <a href="/uploads/${p.file_path}" class="btn btn-outline btn-full" download>
        ⬇️ Download Paper
      </a>
    </div>
  `).join('');
}

async function loadTeacherPapers() {
  const container = document.getElementById('uploadedPapers');
  try {
    const r = await fetch('/search'); // Simple search returns all
    const data = await r.json();
    if (data.success) {
      renderPapers(data.papers, container, true);
    }
  } catch (e) { console.error(e); }
}

async function deletePaper(id) {
  if (!confirm('Are you sure you want to delete this paper?')) return;
  
  try {
    const r = await fetch(`/delete/${id}`, { method: 'DELETE' });
    const data = await r.json();
    if (data.success) {
      loadTeacherPapers();
    } else {
      alert(data.error || 'Delete failed');
    }
  } catch (e) { alert('Server error'); }
}
