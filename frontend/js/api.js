/**
 * VOX - REST API Client Module
 * Centralized HTTP communication with Python Flask backend.
 */

const API_BASE_URL = (window.location.protocol.startsWith('http') && window.location.port === '5000')
    ? '/api'
    : 'http://localhost:5000/api';

const Api = {
    /**
     * Check backend server health status
     */
    async checkHealth() {
        try {
            const response = await fetch(`${API_BASE_URL}/health`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Health check failed:', error);
            return { success: false, error: error.message };
        }
    },

    /**
     * Send recorded audio blob to backend for transcription and task understanding
     */
    async transcribeAudio(audioBlob, clientTranscript = '', language = 'auto') {
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.webm');
        if (clientTranscript) {
            formData.append('transcript', clientTranscript);
        }
        if (language) {
            formData.append('language', language);
        }

        try {
            const response = await fetch(`${API_BASE_URL}/transcribe`, {
                method: 'POST',
                body: formData,
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.message || `Server error (${response.status})`);
            }
            return data;
        } catch (error) {
            console.error('Transcription upload failed:', error);
            throw error;
        }
    },

    /**
     * Direct natural language voice prompt parsing without audio
     */
    async parseText(text) {
        try {
            const response = await fetch(`${API_BASE_URL}/tasks/parse`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text }),
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.message || 'Failed to parse task');
            return data;
        } catch (error) {
            console.error('Text parse failed:', error);
            throw error;
        }
    },

    /**
     * Fetch all tasks from backend
     */
    async getTasks() {
        try {
            const response = await fetch(`${API_BASE_URL}/tasks`);
            const data = await response.json();
            if (!response.ok) throw new Error(data.message || 'Failed to fetch tasks');
            return data.data || [];
        } catch (error) {
            console.error('Fetch tasks failed:', error);
            throw error;
        }
    },

    /**
     * Create a new task (manual or after voice preview confirmation)
     */
    async createTask(taskData) {
        try {
            const response = await fetch(`${API_BASE_URL}/tasks`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(taskData),
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.message || 'Failed to create task');
            return data.data;
        } catch (error) {
            console.error('Create task failed:', error);
            throw error;
        }
    },

    /**
     * Update an existing task
     */
    async updateTask(taskId, taskData) {
        try {
            const response = await fetch(`${API_BASE_URL}/tasks/${taskId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(taskData),
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.message || 'Failed to update task');
            return data.data;
        } catch (error) {
            console.error('Update task failed:', error);
            throw error;
        }
    },

    /**
     * Toggle task completion status
     */
    async toggleComplete(taskId) {
        try {
            const response = await fetch(`${API_BASE_URL}/tasks/${taskId}/complete`, {
                method: 'PATCH',
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.message || 'Failed to update task status');
            return data.data;
        } catch (error) {
            console.error('Toggle complete failed:', error);
            throw error;
        }
    },

    /**
     * Delete a task
     */
    async deleteTask(taskId) {
        try {
            const response = await fetch(`${API_BASE_URL}/tasks/${taskId}`, {
                method: 'DELETE',
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.message || 'Failed to delete task');
            return true;
        } catch (error) {
            console.error('Delete task failed:', error);
            throw error;
        }
    }
};
