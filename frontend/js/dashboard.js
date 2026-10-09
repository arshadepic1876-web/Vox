/**
 * VOX - Dashboard Controller
 * Handles live stats, task list rendering, search/filters, and modal interactions.
 */

// Application State
const AppState = {
    tasks: [],
    currentFilter: 'all',
    searchQuery: '',
    pendingPreviewTask: null,
};

// DOM References
const DOM = {
    statusDot: document.getElementById('server-status-dot'),
    statusText: document.getElementById('server-status-text'),
    statTotal: document.getElementById('stat-total'),
    statPending: document.getElementById('stat-pending'),
    statCompleted: document.getElementById('stat-completed'),
    statUrgent: document.getElementById('stat-urgent'),
    statOverdue: document.getElementById('stat-overdue'),
    tasksContainer: document.getElementById('tasks-container'),
    emptyState: document.getElementById('tasks-empty-state'),
    filterPills: document.getElementById('filter-pills'),
    searchInput: document.getElementById('task-search-input'),
    openAddBtn: document.getElementById('open-add-modal-btn'),
    taskForm: document.getElementById('task-form'),
    formModalTitle: document.getElementById('form-modal-title'),
    formTaskId: document.getElementById('form-task-id'),
    formTitle: document.getElementById('form-title'),
    formDescription: document.getElementById('form-description'),
    formDueDate: document.getElementById('form-due-date'),
    formDueTime: document.getElementById('form-due-time'),
    formPriority: document.getElementById('form-priority'),
    formCategory: document.getElementById('form-category'),
    formUrgent: document.getElementById('form-urgent'),
    // Preview modal elements (interactive edit popup)
    previewEditTitle: document.getElementById('preview-edit-title'),
    previewEditDate: document.getElementById('preview-edit-date'),
    previewEditTime: document.getElementById('preview-edit-time'),
    previewEditPriority: document.getElementById('preview-edit-priority'),
    previewEditCategory: document.getElementById('preview-edit-category'),
    previewEditUrgent: document.getElementById('preview-edit-urgent'),
    previewLanguageChip: document.getElementById('preview-language-chip'),
    previewTranscript: document.getElementById('preview-transcript'),
    previewConfirmBtn: document.getElementById('preview-confirm-btn'),
    // Delete modal elements
    deleteTaskId: document.getElementById('delete-task-id'),
    confirmDeleteBtn: document.getElementById('confirm-delete-btn'),
};

// Initialize Application on Page Load
document.addEventListener('DOMContentLoaded', () => {
    initServerHealthCheck();
    loadTasks();
    setupEventListeners();
});

// Check Server Health
async function initServerHealthCheck() {
    try {
        const res = await Api.checkHealth();
        if (res && res.success) {
            DOM.statusDot.classList.remove('offline');
            DOM.statusText.textContent = 'Backend Online';
        } else {
            DOM.statusDot.classList.add('offline');
            DOM.statusText.textContent = 'Backend Offline';
        }
    } catch {
        DOM.statusDot.classList.add('offline');
        DOM.statusText.textContent = 'Backend Offline';
    }
}

// Fetch tasks from API
async function loadTasks() {
    try {
        const tasks = await Api.getTasks();
        AppState.tasks = tasks;
        renderDashboard();
    } catch (err) {
        // Fallback for clean offline initial view
        console.warn('Could not load tasks from API:', err);
        AppState.tasks = [];
        renderDashboard();
    }
}

// Event Listeners Setup
function setupEventListeners() {
    // Filter pills
    if (DOM.filterPills) {
        DOM.filterPills.addEventListener('click', (e) => {
            const btn = e.target.closest('.filter-pill');
            if (!btn) return;
            document.querySelectorAll('.filter-pill').forEach(p => p.classList.remove('active'));
            btn.classList.add('active');
            AppState.currentFilter = btn.dataset.filter;
            renderTasksList();
        });
    }

    // Search input (debounced)
    if (DOM.searchInput) {
        DOM.searchInput.addEventListener('input', debounce((e) => {
            AppState.searchQuery = e.target.value.toLowerCase().trim();
            renderTasksList();
        }, 200));
    }

    // Open Manual Add Modal
    if (DOM.openAddBtn) {
        DOM.openAddBtn.addEventListener('click', () => {
            openCreateTaskModal();
        });
    }

    // Form submission (Create or Update)
    if (DOM.taskForm) {
        DOM.taskForm.addEventListener('submit', handleTaskFormSubmit);
    }

    // Preview Modal Buttons
    if (DOM.previewConfirmBtn) {
        DOM.previewConfirmBtn.addEventListener('click', handlePreviewConfirm);
    }

    // Delete Confirmation Button
    if (DOM.confirmDeleteBtn) {
        DOM.confirmDeleteBtn.addEventListener('click', handleConfirmDelete);
    }

    // Direct Voice Command Input Form
    const textCommandForm = document.getElementById('text-command-form');
    const textCommandInput = document.getElementById('text-command-input');
    if (textCommandForm && textCommandInput) {
        textCommandForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const text = textCommandInput.value.trim();
            if (!text) return;

            try {
                showToast('Analyzing voice command...', 'info', 1500);
                const res = await Api.parseText(text);
                if (res && res.success && res.data) {
                    showTaskPreview(res.data);
                    textCommandInput.value = '';
                }
            } catch (err) {
                showToast(err.message || 'Error understanding task', 'error');
            }
        });
    }
}

// Render Dashboard (Stats + Tasks)
function renderDashboard() {
    updateStatistics();
    renderTasksList();
}

// Compute and Update Dashboard Statistics
function updateStatistics() {
    const total = AppState.tasks.length;
    let pending = 0;
    let completed = 0;
    let urgent = 0;
    let overdue = 0;

    AppState.tasks.forEach(task => {
        if (task.status === 'completed') {
            completed++;
        } else {
            pending++;
            if (task.urgent) urgent++;
            if (isTaskOverdue(task.due_date, task.due_time)) overdue++;
        }
    });

    DOM.statTotal.textContent = total;
    DOM.statPending.textContent = pending;
    DOM.statCompleted.textContent = completed;
    DOM.statUrgent.textContent = urgent;
    DOM.statOverdue.textContent = overdue;
}

// Render Task List with Filters and Search applied
function renderTasksList() {
    const filtered = AppState.tasks.filter(task => {
        const matchesSearch = !AppState.searchQuery || 
            (task.title && task.title.toLowerCase().includes(AppState.searchQuery)) ||
            (task.description && task.description.toLowerCase().includes(AppState.searchQuery)) ||
            (task.category && task.category.toLowerCase().includes(AppState.searchQuery));

        if (!matchesSearch) return false;

        const isOverdue = task.status !== 'completed' && isTaskOverdue(task.due_date, task.due_time);

        switch (AppState.currentFilter) {
            case 'today':
                return task.due_date === new Date().toISOString().split('T')[0];
            case 'upcoming':
                return task.status !== 'completed' && !isOverdue && Boolean(task.due_date);
            case 'overdue':
                return isOverdue;
            case 'urgent':
                return task.urgent && task.status !== 'completed';
            case 'high':
                return (task.priority === 'HIGH' || task.priority === 'CRITICAL') && task.status !== 'completed';
            case 'completed':
                return task.status === 'completed';
            case 'all':
            default:
                return true;
        }
    });

    // Clear existing task cards (keep empty state element)
    const existingCards = DOM.tasksContainer.querySelectorAll('.task-card');
    existingCards.forEach(c => c.remove());

    if (filtered.length === 0) {
        DOM.emptyState.style.display = 'block';
        return;
    }

    DOM.emptyState.style.display = 'none';

    filtered.forEach(task => {
        const card = createTaskCardElement(task);
        DOM.tasksContainer.appendChild(card);
    });
}

// Create DOM element for a single task card
function createTaskCardElement(task) {
    const card = document.createElement('div');
    const isCompleted = task.status === 'completed';
    const isOverdue = !isCompleted && isTaskOverdue(task.due_date, task.due_time);

    card.className = `task-card ${isCompleted ? 'completed' : ''}`;
    card.dataset.id = task.task_id;

    // Priority badge class
    const priorityClass = `badge-${(task.priority || 'medium').toLowerCase()}`;
    const formattedDate = formatDateDisplay(task.due_date);
    const formattedTime = formatTimeDisplay(task.due_time);

    card.innerHTML = `
        <button class="task-complete-btn" aria-label="Mark task complete" onclick="toggleTaskCompletion('${task.task_id}')">
            <svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/></svg>
        </button>

        <div class="task-content">
            <h4 class="task-title">${escapeHtml(task.title)}</h4>
            ${task.description ? `<p class="task-description">${escapeHtml(task.description)}</p>` : ''}

            <div class="task-meta">
                ${formattedDate ? `
                    <span class="meta-item ${isOverdue ? 'overdue' : ''}">
                        <svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clip-rule="evenodd"/></svg>
                        <span>${formattedDate}${formattedTime ? ` &bull; ${formattedTime}` : ''}</span>
                    </span>
                ` : ''}

                <span class="badge ${priorityClass}">${escapeHtml(task.priority || 'MEDIUM')}</span>

                ${task.urgent ? `<span class="badge badge-urgent">URGENT</span>` : ''}

                <span class="badge badge-category">${escapeHtml(task.category || 'Other')}</span>
            </div>
        </div>

        <div class="task-actions">
            <button class="task-action-btn edit-btn" aria-label="Edit Task" onclick="editTask('${task.task_id}')">
                <svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16"><path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z"/></svg>
            </button>
            <button class="task-action-btn delete-btn" aria-label="Delete Task" onclick="confirmDeleteTask('${task.task_id}')">
                <svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16"><path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd"/></svg>
            </button>
        </div>
    `;

    return card;
}

// Toggle Task Completion Status
async function toggleTaskCompletion(taskId) {
    try {
        const updated = await Api.toggleComplete(taskId);
        const index = AppState.tasks.findIndex(t => t.task_id === taskId);
        if (index !== -1) {
            AppState.tasks[index] = updated;
            renderDashboard();
            const statusMsg = updated.status === 'completed' ? 'Task marked as completed!' : 'Task reopened';
            showToast(statusMsg, 'success');
        }
    } catch (err) {
        showToast('Failed to update task status', 'error');
    }
}

// Open Form Modal for New Task
function openCreateTaskModal() {
    DOM.formModalTitle.textContent = 'Create New Task';
    DOM.formTaskId.value = '';
    DOM.taskForm.reset();
    DOM.formPriority.value = 'MEDIUM';
    DOM.formCategory.value = 'College';
    openModal('task-form-modal');
}

// Open Form Modal for Editing Existing Task
function editTask(taskId) {
    const task = AppState.tasks.find(t => t.task_id === taskId);
    if (!task) return;

    DOM.formModalTitle.textContent = 'Edit Task';
    DOM.formTaskId.value = task.task_id;
    DOM.formTitle.value = task.title || '';
    DOM.formDescription.value = task.description || '';
    DOM.formDueDate.value = task.due_date || '';
    DOM.formDueTime.value = task.due_time || '';
    DOM.formPriority.value = task.priority || 'MEDIUM';
    DOM.formCategory.value = task.category || 'Other';
    DOM.formUrgent.checked = Boolean(task.urgent);

    openModal('task-form-modal');
}

// Handle Form Submit (Create or Update)
async function handleTaskFormSubmit(e) {
    e.preventDefault();

    const taskId = DOM.formTaskId.value;
    const taskPayload = {
        title: DOM.formTitle.value.trim(),
        description: DOM.formDescription.value.trim(),
        due_date: DOM.formDueDate.value || null,
        due_time: DOM.formDueTime.value || null,
        priority: DOM.formPriority.value,
        category: DOM.formCategory.value,
        urgent: DOM.formUrgent.checked,
    };

    if (!taskPayload.title) {
        showToast('Task title is required', 'error');
        return;
    }

    try {
        if (taskId) {
            // Update
            const updated = await Api.updateTask(taskId, taskPayload);
            const idx = AppState.tasks.findIndex(t => t.task_id === taskId);
            if (idx !== -1) AppState.tasks[idx] = updated;
            showToast('Task updated successfully', 'success');
        } else {
            // Create
            const created = await Api.createTask(taskPayload);
            AppState.tasks.unshift(created);
            showToast('Task created successfully', 'success');
        }

        closeModal('task-form-modal');
        renderDashboard();
    } catch (err) {
        showToast(err.message || 'Error saving task', 'error');
    }
}

// Open Delete Confirmation
function confirmDeleteTask(taskId) {
    DOM.deleteTaskId.value = taskId;
    openModal('delete-modal');
}

// Handle Permanent Delete
async function handleConfirmDelete() {
    const taskId = DOM.deleteTaskId.value;
    if (!taskId) return;

    try {
        await Api.deleteTask(taskId);
        AppState.tasks = AppState.tasks.filter(t => t.task_id !== taskId);
        closeModal('delete-modal');
        renderDashboard();
        showToast('Task deleted successfully', 'info');
    } catch (err) {
        showToast('Could not delete task', 'error');
    }
}

// ==============================================================================
// TASK PREVIEW CONTROLLER (Human-in-the-Loop Confirmation & Direct Editing)
// ==============================================================================
function showTaskPreview(parsedTask) {
    AppState.pendingPreviewTask = parsedTask;

    // Populate editable inputs with auto-caught AI values
    if (DOM.previewEditTitle) {
        DOM.previewEditTitle.value = parsedTask.title || 'Untitled Task';
    }
    if (DOM.previewEditDate) {
        DOM.previewEditDate.value = parsedTask.due_date || '';
    }
    if (DOM.previewEditTime) {
        DOM.previewEditTime.value = parsedTask.due_time || '';
    }
    if (DOM.previewEditPriority) {
        DOM.previewEditPriority.value = parsedTask.priority || 'MEDIUM';
    }
    if (DOM.previewEditCategory) {
        DOM.previewEditCategory.value = parsedTask.category || 'College';
    }
    if (DOM.previewEditUrgent) {
        DOM.previewEditUrgent.checked = Boolean(parsedTask.urgent);
    }
    if (DOM.previewLanguageChip) {
        const lang = parsedTask.detected_language || 'Auto-Detected';
        DOM.previewLanguageChip.textContent = `🌐 ${lang}`;
    }
    if (DOM.previewTranscript) {
        DOM.previewTranscript.textContent = `"${parsedTask.raw_transcription || 'No transcription available'}"`;
    }

    // Display the interactive popup
    openModal('preview-modal');
}

// Confirm Task Preview -> Read modified fields and save directly to backend
async function handlePreviewConfirm() {
    if (!AppState.pendingPreviewTask) return;

    const editedTitle = DOM.previewEditTitle ? DOM.previewEditTitle.value.trim() : '';
    if (!editedTitle) {
        showToast('Please specify a task title.', 'error');
        return;
    }

    const taskPayload = {
        title: editedTitle,
        description: AppState.pendingPreviewTask.description || editedTitle,
        due_date: DOM.previewEditDate ? (DOM.previewEditDate.value || null) : AppState.pendingPreviewTask.due_date,
        due_time: DOM.previewEditTime ? (DOM.previewEditTime.value || null) : AppState.pendingPreviewTask.due_time,
        priority: DOM.previewEditPriority ? DOM.previewEditPriority.value : (AppState.pendingPreviewTask.priority || 'MEDIUM'),
        category: DOM.previewEditCategory ? DOM.previewEditCategory.value : (AppState.pendingPreviewTask.category || 'College'),
        urgent: DOM.previewEditUrgent ? DOM.previewEditUrgent.checked : Boolean(AppState.pendingPreviewTask.urgent),
        raw_transcription: AppState.pendingPreviewTask.raw_transcription || '',
        detected_language: AppState.pendingPreviewTask.detected_language || 'English',
        status: 'pending',
    };

    try {
        const created = await Api.createTask(taskPayload);
        AppState.tasks.unshift(created);
        closeModal('preview-modal');
        renderDashboard();
        showToast('🚀 Task assigned successfully!', 'success');
        AppState.pendingPreviewTask = null;
    } catch (err) {
        showToast(err.message || 'Failed to save task', 'error');
    }
}
