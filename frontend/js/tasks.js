/**
 * VOX - All Tasks Page Controller
 * Advanced sorting, category filters, and task management.
 */

const TasksState = {
    tasks: [],
    searchQuery: '',
    sortBy: 'smart',
    categoryFilter: 'all',
};

const TaskDOM = {
    tasksContainer: document.getElementById('tasks-container'),
    emptyState: document.getElementById('tasks-empty-state'),
    searchInput: document.getElementById('task-search-input'),
    sortSelect: document.getElementById('sort-select'),
    categoryFilterSelect: document.getElementById('category-filter-select'),
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
    deleteTaskId: document.getElementById('delete-task-id'),
    confirmDeleteBtn: document.getElementById('confirm-delete-btn'),
};

document.addEventListener('DOMContentLoaded', () => {
    loadTasks();
    setupTasksListeners();
});

async function loadTasks() {
    try {
        const tasks = await Api.getTasks();
        TasksState.tasks = tasks;
        renderTasksList();
    } catch (err) {
        console.warn('Could not load tasks:', err);
        TasksState.tasks = [];
        renderTasksList();
    }
}

function setupTasksListeners() {
    if (TaskDOM.searchInput) {
        TaskDOM.searchInput.addEventListener('input', debounce((e) => {
            TasksState.searchQuery = e.target.value.toLowerCase().trim();
            renderTasksList();
        }, 200));
    }

    if (TaskDOM.sortSelect) {
        TaskDOM.sortSelect.addEventListener('change', (e) => {
            TasksState.sortBy = e.target.value;
            renderTasksList();
        });
    }

    if (TaskDOM.categoryFilterSelect) {
        TaskDOM.categoryFilterSelect.addEventListener('change', (e) => {
            TasksState.categoryFilter = e.target.value;
            renderTasksList();
        });
    }

    if (TaskDOM.openAddBtn) {
        TaskDOM.openAddBtn.addEventListener('click', openCreateModal);
    }

    if (TaskDOM.taskForm) {
        TaskDOM.taskForm.addEventListener('submit', handleTaskFormSubmit);
    }

    if (TaskDOM.confirmDeleteBtn) {
        TaskDOM.confirmDeleteBtn.addEventListener('click', handleConfirmDelete);
    }
}

function sortTasks(tasks) {
    const priorityWeight = { 'CRITICAL': 4, 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1 };

    return [...tasks].sort((a, b) => {
        if (TasksState.sortBy === 'smart') {
            // Completed tasks always at the bottom
            if (a.status === 'completed' && b.status !== 'completed') return 1;
            if (a.status !== 'completed' && b.status === 'completed') return -1;

            // Urgent first
            if (a.urgent && !b.urgent) return -1;
            if (!a.urgent && b.urgent) return 1;

            // Overdue next
            const aOverdue = isTaskOverdue(a.due_date, a.due_time);
            const bOverdue = isTaskOverdue(b.due_date, b.due_time);
            if (aOverdue && !bOverdue) return -1;
            if (!aOverdue && bOverdue) return 1;

            // Due date ascending
            if (a.due_date && b.due_date) {
                return a.due_date.localeCompare(b.due_date);
            }
            if (a.due_date) return -1;
            if (b.due_date) return 1;

            // Priority
            return (priorityWeight[b.priority] || 0) - (priorityWeight[a.priority] || 0);
        }

        if (TasksState.sortBy === 'dueDate') {
            if (!a.due_date) return 1;
            if (!b.due_date) return -1;
            return a.due_date.localeCompare(b.due_date);
        }

        if (TasksState.sortBy === 'priority') {
            return (priorityWeight[b.priority] || 0) - (priorityWeight[a.priority] || 0);
        }

        if (TasksState.sortBy === 'created') {
            return (b.created_at || '').localeCompare(a.created_at || '');
        }

        return 0;
    });
}

function renderTasksList() {
    let list = TasksState.tasks.filter(task => {
        // Search
        const matchesSearch = !TasksState.searchQuery ||
            (task.title && task.title.toLowerCase().includes(TasksState.searchQuery)) ||
            (task.description && task.description.toLowerCase().includes(TasksState.searchQuery));

        if (!matchesSearch) return false;

        // Category
        if (TasksState.categoryFilter !== 'all') {
            if ((task.category || '').toLowerCase() !== TasksState.categoryFilter.toLowerCase()) {
                return false;
            }
        }

        return true;
    });

    list = sortTasks(list);

    const existingCards = TaskDOM.tasksContainer.querySelectorAll('.task-card');
    existingCards.forEach(c => c.remove());

    if (list.length === 0) {
        TaskDOM.emptyState.style.display = 'block';
        return;
    }

    TaskDOM.emptyState.style.display = 'none';

    list.forEach(task => {
        const card = createTaskCardElement(task);
        TaskDOM.tasksContainer.appendChild(card);
    });
}

function createTaskCardElement(task) {
    const card = document.createElement('div');
    const isCompleted = task.status === 'completed';
    const isOverdue = !isCompleted && isTaskOverdue(task.due_date, task.due_time);

    card.className = `task-card ${isCompleted ? 'completed' : ''}`;
    card.dataset.id = task.task_id;

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

async function toggleTaskCompletion(taskId) {
    try {
        const updated = await Api.toggleComplete(taskId);
        const idx = TasksState.tasks.findIndex(t => t.task_id === taskId);
        if (idx !== -1) {
            TasksState.tasks[idx] = updated;
            renderTasksList();
            showToast(updated.status === 'completed' ? 'Task marked as completed' : 'Task reopened', 'success');
        }
    } catch {
        showToast('Failed to update task status', 'error');
    }
}

function openCreateModal() {
    TaskDOM.formModalTitle.textContent = 'Create New Task';
    TaskDOM.formTaskId.value = '';
    TaskDOM.taskForm.reset();
    TaskDOM.formPriority.value = 'MEDIUM';
    TaskDOM.formCategory.value = 'College';
    openModal('task-form-modal');
}

function editTask(taskId) {
    const task = TasksState.tasks.find(t => t.task_id === taskId);
    if (!task) return;

    TaskDOM.formModalTitle.textContent = 'Edit Task';
    TaskDOM.formTaskId.value = task.task_id;
    TaskDOM.formTitle.value = task.title || '';
    TaskDOM.formDescription.value = task.description || '';
    TaskDOM.formDueDate.value = task.due_date || '';
    TaskDOM.formDueTime.value = task.due_time || '';
    TaskDOM.formPriority.value = task.priority || 'MEDIUM';
    TaskDOM.formCategory.value = task.category || 'Other';
    TaskDOM.formUrgent.checked = Boolean(task.urgent);

    openModal('task-form-modal');
}

async function handleTaskFormSubmit(e) {
    e.preventDefault();
    const taskId = TaskDOM.formTaskId.value;
    const taskPayload = {
        title: TaskDOM.formTitle.value.trim(),
        description: TaskDOM.formDescription.value.trim(),
        due_date: TaskDOM.formDueDate.value || null,
        due_time: TaskDOM.formDueTime.value || null,
        priority: TaskDOM.formPriority.value,
        category: TaskDOM.formCategory.value,
        urgent: TaskDOM.formUrgent.checked,
    };

    if (!taskPayload.title) {
        showToast('Task title is required', 'error');
        return;
    }

    try {
        if (taskId) {
            const updated = await Api.updateTask(taskId, taskPayload);
            const idx = TasksState.tasks.findIndex(t => t.task_id === taskId);
            if (idx !== -1) TasksState.tasks[idx] = updated;
            showToast('Task updated', 'success');
        } else {
            const created = await Api.createTask(taskPayload);
            TasksState.tasks.unshift(created);
            showToast('Task created', 'success');
        }
        closeModal('task-form-modal');
        renderTasksList();
    } catch (err) {
        showToast(err.message || 'Error saving task', 'error');
    }
}

function confirmDeleteTask(taskId) {
    TaskDOM.deleteTaskId.value = taskId;
    openModal('delete-modal');
}

async function handleConfirmDelete() {
    const taskId = TaskDOM.deleteTaskId.value;
    if (!taskId) return;

    try {
        await Api.deleteTask(taskId);
        TasksState.tasks = TasksState.tasks.filter(t => t.task_id !== taskId);
        closeModal('delete-modal');
        renderTasksList();
        showToast('Task deleted', 'info');
    } catch {
        showToast('Failed to delete task', 'error');
    }
}
