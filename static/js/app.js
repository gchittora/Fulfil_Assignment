// API Base URL
const API_BASE = '/api';

// Global state
let currentPage = 1;
let currentFilters = {};
let selectedFile = null;
let currentTaskId = null;
let progressInterval = null;

// ============================================================================
// Tab Management
// ============================================================================

function showTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    document.getElementById(`${tabName}-tab`).classList.add('active');
    event.target.classList.add('active');
    
    if (tabName === 'products') {
        loadProducts();
    } else if (tabName === 'webhooks') {
        loadWebhooks();
    }
}

// ============================================================================
// File Upload with Auto-Refresh
// ============================================================================

const uploadArea = document.getElementById('upload-area');
const fileInput = document.getElementById('file-input');
const uploadBtn = document.getElementById('upload-btn');

uploadArea.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', (e) => handleFileSelect(e.target.files[0]));

uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    handleFileSelect(e.dataTransfer.files[0]);
});

function handleFileSelect(file) {
    if (!file) return;
    
    if (!file.name.endsWith('.csv')) {
        alert('Please select a CSV file');
        return;
    }
    
    selectedFile = file;
    uploadArea.innerHTML = `
        <div class="upload-prompt">
            <span class="upload-icon">✅</span>
            <p>${file.name}</p>
            <small>${(file.size / 1024 / 1024).toFixed(2)} MB</small>
        </div>
    `;
    uploadBtn.style.display = 'block';
}

uploadBtn.addEventListener('click', uploadFile);

async function uploadFile() {
    if (!selectedFile) return;
    
    const formData = new FormData();
    formData.append('file', selectedFile);
    
    uploadBtn.disabled = true;
    uploadBtn.textContent = 'Uploading...';
    
    try {
        const response = await fetch(`${API_BASE}/upload`, {
            method: 'POST',
            body: formData
        });
        
        // Check if response has content before parsing JSON
        const text = await response.text();
        let data;
        
        try {
            data = text ? JSON.parse(text) : {};
        } catch (e) {
            throw new Error(`Server returned invalid response: ${text.substring(0, 100)}`);
        }
        
        if (response.ok) {
            currentTaskId = data.task_id;
            showProgress();
            startAutoRefresh();
        } else {
            const errorMsg = data.error || data.details || `Server error (${response.status})`;
            alert('Upload failed: ' + errorMsg);
            resetUpload();
        }
    } catch (error) {
        alert('Upload failed: ' + error.message);
        resetUpload();
    }
}

function showProgress() {
    document.getElementById('progress-section').style.display = 'block';
    document.getElementById('result-section').style.display = 'none';
    uploadBtn.style.display = 'none';
}

function startAutoRefresh() {
    // Auto-refresh every 2 seconds
    progressInterval = setInterval(pollProgress, 2000);
    pollProgress(); // Call immediately
}

function stopAutoRefresh() {
    if (progressInterval) {
        clearInterval(progressInterval);
        progressInterval = null;
    }
}

async function stopImport() {
    if (!currentTaskId) return;
    
    if (!confirm('Are you sure you want to stop the import? This cannot be undone.')) return;
    
    try {
        const response = await fetch(`${API_BASE}/cancel/${currentTaskId}`, {
            method: 'POST'
        });
        
        if (response.ok) {
            stopAutoRefresh();
            showError('Import cancelled by user');
        } else {
            alert('Failed to cancel import');
        }
    } catch (error) {
        alert('Failed to cancel import: ' + error.message);
    }
}

async function pollProgress() {
    if (!currentTaskId) return;
    
    try {
        const response = await fetch(`${API_BASE}/progress/${currentTaskId}`);
        const data = await response.json();
        
        if (data.state === 'PENDING') {
            document.getElementById('progress-text').textContent = data.status;
        } else if (data.state === 'PROGRESS') {
            const percent = Math.round((data.current / data.total) * 100);
            document.getElementById('progress-fill').style.width = percent + '%';
            document.getElementById('progress-fill').textContent = percent + '%';
            document.getElementById('progress-text').textContent = data.status;
            
            document.getElementById('progress-stats').innerHTML = `
                <div class="stat-item">
                    <strong>${data.current}</strong>
                    <span>Processed</span>
                </div>
                <div class="stat-item">
                    <strong>${data.created || 0}</strong>
                    <span>Created</span>
                </div>
                <div class="stat-item">
                    <strong>${data.updated || 0}</strong>
                    <span>Updated</span>
                </div>
                <div class="stat-item">
                    <strong>${data.errors || 0}</strong>
                    <span>Errors</span>
                </div>
            `;
        } else if (data.state === 'SUCCESS') {
            stopAutoRefresh();
            showResult(data.result);
        } else {
            stopAutoRefresh();
            showError(data.status);
        }
    } catch (error) {
        stopAutoRefresh();
        showError('Failed to get progress: ' + error.message);
    }
}

function showResult(result) {
    document.getElementById('progress-section').style.display = 'none';
    document.getElementById('result-section').style.display = 'block';
    
    const resultDiv = document.getElementById('result-message');
    resultDiv.className = 'alert alert-success';
    resultDiv.innerHTML = `
        <h3>✅ Import Complete!</h3>
        <div class="stats">
            <div class="stat-item">
                <strong>${result.total}</strong>
                <span>Total Rows</span>
            </div>
            <div class="stat-item">
                <strong>${result.created}</strong>
                <span>Created</span>
            </div>
            <div class="stat-item">
                <strong>${result.updated}</strong>
                <span>Updated</span>
            </div>
            <div class="stat-item">
                <strong>${result.errors}</strong>
                <span>Errors</span>
            </div>
        </div>
    `;
    
    setTimeout(resetUpload, 5000);
}

function showError(message) {
    document.getElementById('progress-section').style.display = 'none';
    document.getElementById('result-section').style.display = 'block';
    
    const resultDiv = document.getElementById('result-message');
    resultDiv.className = 'alert alert-error';
    resultDiv.innerHTML = `<h3>❌ Import Failed</h3><p>${message}</p>`;
    
    setTimeout(resetUpload, 5000);
}

function resetUpload() {
    selectedFile = null;
    currentTaskId = null;
    uploadBtn.disabled = false;
    uploadBtn.textContent = 'Upload and Process';
    uploadBtn.style.display = 'none';
    
    uploadArea.innerHTML = `
        <div class="upload-prompt">
            <span class="upload-icon">📁</span>
            <p>Click to select CSV file or drag and drop</p>
            <small>Maximum file size: 1GB</small>
        </div>
    `;
    
    fileInput.value = '';
}

// ============================================================================
// Product Management
// ============================================================================

async function loadProducts(page = 1) {
    currentPage = page;
    
    const params = new URLSearchParams({
        page: page,
        per_page: 20,
        ...currentFilters
    });
    
    try {
        const response = await fetch(`${API_BASE}/products?${params}`);
        const data = await response.json();
        
        displayProducts(data.products);
        displayPagination(data.pages, data.current_page);
    } catch (error) {
        console.error('Failed to load products:', error);
    }
}

function displayProducts(products) {
    const tbody = document.getElementById('products-tbody');
    
    if (products.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="loading">No products found</td></tr>';
        return;
    }
    
    tbody.innerHTML = products.map(product => `
        <tr>
            <td>${product.sku}</td>
            <td>${product.name}</td>
            <td>${product.description || '-'}</td>
            <td>${product.price ? '$' + product.price : '-'}</td>
            <td>
                <span class="status-badge ${product.active ? 'status-active' : 'status-inactive'}">
                    ${product.active ? 'Active' : 'Inactive'}
                </span>
            </td>
            <td>
                <button class="action-btn btn-primary" onclick="editProduct(${product.id})">Edit</button>
                <button class="action-btn btn-danger" onclick="deleteProduct(${product.id})">Delete</button>
            </td>
        </tr>
    `).join('');
}

function displayPagination(totalPages, currentPage) {
    const pagination = document.getElementById('pagination');
    
    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    
    let html = '';
    
    if (currentPage > 1) {
        html += `<button class="page-btn" onclick="loadProducts(${currentPage - 1})">Previous</button>`;
    }
    
    for (let i = 1; i <= totalPages; i++) {
        if (i === 1 || i === totalPages || (i >= currentPage - 2 && i <= currentPage + 2)) {
            html += `<button class="page-btn ${i === currentPage ? 'active' : ''}" 
                     onclick="loadProducts(${i})">${i}</button>`;
        } else if (i === currentPage - 3 || i === currentPage + 3) {
            html += '<span>...</span>';
        }
    }
    
    if (currentPage < totalPages) {
        html += `<button class="page-btn" onclick="loadProducts(${currentPage + 1})">Next</button>`;
    }
    
    pagination.innerHTML = html;
}

function filterProducts() {
    currentFilters = {
        sku: document.getElementById('filter-sku').value,
        name: document.getElementById('filter-name').value,
        active: document.getElementById('filter-active').value
    };
    loadProducts(1);
}

function showCreateModal() {
    document.getElementById('product-modal-title').textContent = 'Add Product';
    document.getElementById('product-form').reset();
    document.getElementById('product-id').value = '';
    document.getElementById('product-modal').classList.add('show');
}

async function editProduct(id) {
    try {
        const response = await fetch(`${API_BASE}/products/${id}`);
        const product = await response.json();
        
        document.getElementById('product-modal-title').textContent = 'Edit Product';
        document.getElementById('product-id').value = product.id;
        document.getElementById('product-sku').value = product.sku;
        document.getElementById('product-name').value = product.name;
        document.getElementById('product-description').value = product.description || '';
        document.getElementById('product-price').value = product.price || '';
        document.getElementById('product-active').checked = product.active;
        
        document.getElementById('product-modal').classList.add('show');
    } catch (error) {
        alert('Failed to load product: ' + error.message);
    }
}

document.getElementById('product-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const id = document.getElementById('product-id').value;
    const data = {
        sku: document.getElementById('product-sku').value,
        name: document.getElementById('product-name').value,
        description: document.getElementById('product-description').value,
        price: parseFloat(document.getElementById('product-price').value) || null,
        active: document.getElementById('product-active').checked
    };
    
    try {
        const url = id ? `${API_BASE}/products/${id}` : `${API_BASE}/products`;
        const method = id ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            closeModal('product-modal');
            loadProducts(currentPage);
        } else {
            const error = await response.json();
            alert('Failed to save product: ' + error.error);
        }
    } catch (error) {
        alert('Failed to save product: ' + error.message);
    }
});

async function deleteProduct(id) {
    if (!confirm('Are you sure you want to delete this product?')) return;
    
    try {
        const response = await fetch(`${API_BASE}/products/${id}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            alert('Product deleted successfully');
            // Reload products after short delay to ensure database commit
            setTimeout(() => loadProducts(currentPage), 500);
        } else {
            alert('Failed to delete product');
        }
    } catch (error) {
        alert('Failed to delete product: ' + error.message);
    }
}

async function confirmBulkDelete() {
    const confirmed = confirm(
        '⚠️ WARNING: This will delete ALL products from the database.\n\n' +
        'This action cannot be undone!\n\n' +
        'Are you absolutely sure?'
    );
    
    if (!confirmed) return;
    
    try {
        const response = await fetch(`${API_BASE}/products/bulk-delete`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        alert(data.message);
        loadProducts(1);
    } catch (error) {
        alert('Failed to delete products: ' + error.message);
    }
}

// ============================================================================
// Webhook Management
// ============================================================================

async function loadWebhooks() {
    try {
        const response = await fetch(`${API_BASE}/webhooks`);
        const webhooks = await response.json();
        
        displayWebhooks(webhooks);
    } catch (error) {
        console.error('Failed to load webhooks:', error);
    }
}

function displayWebhooks(webhooks) {
    const tbody = document.getElementById('webhooks-tbody');
    
    if (webhooks.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="loading">No webhooks configured</td></tr>';
        return;
    }
    
    tbody.innerHTML = webhooks.map(webhook => `
        <tr>
            <td>${webhook.url}</td>
            <td>${webhook.event_type}</td>
            <td>
                <span class="status-badge ${webhook.enabled ? 'status-active' : 'status-inactive'}">
                    ${webhook.enabled ? 'Enabled' : 'Disabled'}
                </span>
            </td>
            <td>
                <button class="action-btn btn-primary" onclick="editWebhook(${webhook.id})">Edit</button>
                <button class="action-btn btn-danger" onclick="deleteWebhook(${webhook.id})">Delete</button>
            </td>
        </tr>
    `).join('');
}

function showWebhookModal() {
    document.getElementById('webhook-modal-title').textContent = 'Add Webhook';
    document.getElementById('webhook-form').reset();
    document.getElementById('webhook-id').value = '';
    document.getElementById('webhook-modal').classList.add('show');
}

async function editWebhook(id) {
    try {
        const response = await fetch(`${API_BASE}/webhooks`);
        const webhooks = await response.json();
        const webhook = webhooks.find(w => w.id === id);
        
        document.getElementById('webhook-modal-title').textContent = 'Edit Webhook';
        document.getElementById('webhook-id').value = webhook.id;
        document.getElementById('webhook-url').value = webhook.url;
        document.getElementById('webhook-event').value = webhook.event_type;
        document.getElementById('webhook-enabled').checked = webhook.enabled;
        
        document.getElementById('webhook-modal').classList.add('show');
    } catch (error) {
        alert('Failed to load webhook: ' + error.message);
    }
}

document.getElementById('webhook-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const id = document.getElementById('webhook-id').value;
    const data = {
        url: document.getElementById('webhook-url').value,
        event_type: document.getElementById('webhook-event').value,
        enabled: document.getElementById('webhook-enabled').checked
    };
    
    try {
        const url = id ? `${API_BASE}/webhooks/${id}` : `${API_BASE}/webhooks`;
        const method = id ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            closeModal('webhook-modal');
            loadWebhooks();
        } else {
            const error = await response.json();
            alert('Failed to save webhook: ' + error.error);
        }
    } catch (error) {
        alert('Failed to save webhook: ' + error.message);
    }
});

async function deleteWebhook(id) {
    if (!confirm('Are you sure you want to delete this webhook?')) return;
    
    try {
        const response = await fetch(`${API_BASE}/webhooks/${id}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            loadWebhooks();
        } else {
            alert('Failed to delete webhook');
        }
    } catch (error) {
        alert('Failed to delete webhook: ' + error.message);
    }
}

// ============================================================================
// Modal Management
// ============================================================================

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('show');
}

window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.classList.remove('show');
    }
}

// ============================================================================
// Initialize
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    loadProducts();
});
