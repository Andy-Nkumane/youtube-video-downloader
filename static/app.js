const form = document.querySelector('#download-form');
const submitButton = form.querySelector('.submit-button');
const errorBox = document.querySelector('#form-error');
const statusCard = document.querySelector('#status-card');
const statusLabel = document.querySelector('#status-label');
const statusMessage = document.querySelector('#status-message');
const progressBar = document.querySelector('#progress-bar');
const progressLabel = document.querySelector('#progress-label');
const fileLinks = document.querySelector('#file-links');
const mediaTitle = document.querySelector('#media-title');
const cancelButton = document.querySelector('#cancel-button');
const mediaList = document.querySelector('#media-list');
const resultsCount = document.querySelector('#results-count');
let activeJobId = null;

document.querySelector('#paste-button').addEventListener('click', async () => {
  try {
    document.querySelector('#url').value = await navigator.clipboard.readText();
  } catch {
    document.querySelector('#url').focus();
  }
});

function renderJob(job) {
  statusCard.hidden = false;
  statusLabel.textContent = job.status.toUpperCase();
  statusMessage.textContent = job.message;
  mediaTitle.textContent = job.title;
  progressBar.style.width = `${job.progress}%`;
  progressLabel.textContent = `${Math.round(job.progress)}%`;
  resultsCount.textContent = `${job.items.length} ${job.items.length === 1 ? 'item' : 'items'}`;
  if (job.items.length) {
    mediaList.replaceChildren(...job.items.map((item) => {
      const row = document.createElement('div');
      row.className = 'media-row';
      const title = document.createElement('span');
      title.className = 'media-row-title';
      title.textContent = item.title;
      const status = document.createElement('span');
      status.className = `media-status ${item.status}`;
      status.textContent = item.status.toUpperCase();
      const meta = document.createElement('span');
      meta.className = 'media-row-meta';
      const size = document.createElement('span');
      size.className = 'media-size';
      size.textContent = item.size || 'Size pending';
      meta.append(size, status);
      row.append(title, meta);
      return row;
    }));
  }

  cancelButton.hidden = !['queued', 'running'].includes(job.status);
  if (job.status === 'complete') {
    submitButton.disabled = false;
    submitButton.querySelector('span').textContent = 'START ANOTHER';
    fileLinks.replaceChildren(...job.files.map((filename) => {
      const link = document.createElement('a');
      link.href = `/files/${filename.split('/').map(encodeURIComponent).join('/')}`;
      link.textContent = `SAVE ${filename.split('/').pop()}`;
      return link;
    }));
  } else if (job.status === 'failed' || job.status === 'cancelled') {
    submitButton.disabled = false;
    submitButton.querySelector('span').textContent = 'TRY AGAIN';
  }
}

async function watchJob(jobId) {
  const response = await fetch(`/api/downloads/${jobId}`);
  const job = await response.json();
  renderJob(job);
  if (job.status === 'queued' || job.status === 'running') {
    window.setTimeout(() => watchJob(jobId), 1000);
  }
}

cancelButton.addEventListener('click', async () => {
  if (!activeJobId) return;
  cancelButton.disabled = true;
  cancelButton.textContent = 'CANCELLING...';
  try {
    const response = await fetch(`/api/downloads/${activeJobId}/cancel`, { method: 'POST' });
    renderJob(await response.json());
  } finally {
    cancelButton.disabled = false;
    cancelButton.textContent = 'CANCEL DOWNLOAD';
  }
});

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  errorBox.textContent = '';
  fileLinks.replaceChildren();
  mediaList.innerHTML = '<p class="empty-results">Preparing media list...</p>';
  resultsCount.textContent = '0 items';
  submitButton.disabled = true;
  submitButton.querySelector('span').textContent = 'STARTING...';

  const data = new FormData(form);
  try {
    const response = await fetch('/api/downloads', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: data.get('url'), media_type: data.get('media_type') }),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'Could not start download.');
    activeJobId = result.id;
    renderJob(result);
    watchJob(result.id);
  } catch (error) {
    errorBox.textContent = error.message;
    submitButton.disabled = false;
    submitButton.querySelector('span').textContent = 'START DOWNLOAD';
  }
});
