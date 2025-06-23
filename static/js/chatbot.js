/**
 * AI Analytics Chatbot JavaScript
 * Handles real-time messaging, UI interactions, and data visualization
 */

class ChatBot {
    constructor() {
        this.config = {};
        this.isProcessing = false;
        this.sessionStats = {
            queries: 0,
            tokens: 0,
            cost: 0,
            totalTime: 0
        };
        this.charts = {};
        this.currentRequest = null;
    }

    /**
     * Initialize the chatbot with configuration
     */
    init(config) {
        console.log('🤖 ChatBot initializing...', config);
        this.config = config;
        this.bindEvents();
        this.updateUI();
        this.loadSessionStats();
        console.log('✅ ChatBot initialized successfully');
    }

    /**
     * Bind event listeners
     */
    bindEvents() {
        console.log('🔗 Binding events...');
        
        // Chat form submission
        const chatForm = document.getElementById('chat-form');
        if (chatForm) {
            console.log('✅ Found chat form, binding submit event');
            chatForm.addEventListener('submit', (e) => {
                console.log('📤 Form submit triggered');
                this.handleSubmit(e);
            });
        } else {
            console.error('❌ Chat form not found!');
        }

        // Message input events
        const messageInput = document.getElementById('message-input');
        if (messageInput) {
            console.log('✅ Found message input, binding events');
            messageInput.addEventListener('input', (e) => this.handleInputChange(e));
            messageInput.addEventListener('keydown', (e) => this.handleKeyDown(e));
        } else {
            console.error('❌ Message input not found!');
        }

        // Auto-resize textarea
        this.autoResizeTextarea();

        // Provider status refresh
        setInterval(() => this.refreshProviderStatus(), 30000); // Every 30 seconds
        
        console.log('✅ Events bound successfully');
    }

    /**
     * Handle form submission
     */
    async handleSubmit(e) {
        console.log('🚀 handleSubmit called');
        e.preventDefault();

        if (this.isProcessing) {
            console.log('⏳ Already processing, skipping');
            return;
        }

        const messageInput = document.getElementById('message-input');
        const question = messageInput.value.trim();
        console.log('💬 Question:', question);

        if (!question) {
            console.log('❌ Empty question, returning');
            return;
        }

        // Validate question length
        if (question.length > 500) {
            console.log('❌ Question too long');
            this.showError('Question is too long (max 500 characters)');
            return;
        }

        try {
            console.log('🔄 Starting processing...');
            this.setProcessing(true);
            messageInput.value = '';
            this.updateCharCount();

            // Add user message to chat
            this.addMessage('user', question);

            // Show typing indicator
            this.showTypingIndicator();

            // Send request to backend
            console.log('📡 Sending message to backend...');
            const response = await this.sendMessage(question);
            console.log('📨 Response received:', response);

            // Hide typing indicator
            this.hideTypingIndicator();

            if (response.success) {
                // Add assistant response
                this.addAssistantMessage(response);
                
                // Update session stats
                this.updateSessionStats(response);
            } else {
                console.error('❌ Response error:', response.error);
                this.addMessage('error', response.error || 'An error occurred');
            }

        } catch (error) {
            console.error('💥 Error sending message:', error);
            this.hideTypingIndicator();
            this.addMessage('error', `Failed to send message: ${error.message}. Please check your connection and try again.`);
        } finally {
            console.log('✅ Processing complete');
            this.setProcessing(false);
            messageInput.focus();
        }
    }

    /**
     * Send message to backend
     */
    async sendMessage(question) {
        const payload = {
            question: question,
            conversation_id: this.config.conversationId,
            provider: this.getSelectedProvider(),
            model: this.getSelectedModel()
        };

        // Create AbortController for request cancellation
        const controller = new AbortController();
        this.currentRequest = controller;

        const response = await fetch('/chatbot/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.config.csrfToken
            },
            body: JSON.stringify(payload),
            signal: controller.signal
        });

        this.currentRequest = null;

        if (!response.ok) {
            let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
            try {
                const errorData = await response.json();
                errorMessage = errorData.error || errorMessage;
            } catch (e) {
                console.warn('Could not parse error response as JSON');
            }
            throw new Error(errorMessage);
        }

        return await response.json();
    }

    /**
     * Add message to chat
     */
    addMessage(type, content, metadata = {}) {
        const messagesContainer = document.getElementById('chat-messages');
        const messageElement = this.createMessageElement(type, content, metadata);
        
        // Insert before typing indicator
        const typingIndicator = document.getElementById('typing-indicator');
        messagesContainer.insertBefore(messageElement, typingIndicator);
        
        this.scrollToBottom();
        return messageElement;
    }

    /**
     * Add assistant message with SQL and chart data
     */
    addAssistantMessage(response) {
        let content = `Found ${response.row_count || 0} results`;
        
        // Add table data if available
        if (response.rows && response.rows.length > 0) {
            content += '\n\n' + this.generateResultsTable(response.columns, response.rows);
        }
        
        const messageElement = this.addMessage('assistant', content, {
            chartData: response.chart_suggestion,
            provider: response.ai_provider,
            model: response.ai_model,
            tokens: response.tokens_used || 0,
            time: response.processing_time_ms || 0,
            hasTable: response.rows && response.rows.length > 0
        });

        // Add chart if available
        if (response.chart_suggestion && response.rows && response.rows.length > 0) {
            this.addChart(messageElement, response);
        }
    }

    /**
     * Create message element
     */
    createMessageElement(type, content, metadata = {}) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        const timestamp = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        let messageHTML = `
            <div class="message-content">
                <div class="message-bubble">
                    <div class="message-text">${metadata.hasTable ? content : this.escapeHtml(content)}</div>
        `;

        // SQL is hidden from users - they don't need to see it

        messageHTML += `</div>`;

        // Add metadata
        if (type === 'assistant' || type === 'user') {
            messageHTML += `
                <div class="message-meta">
                    <span class="message-time">${timestamp}</span>
            `;
            
            if (metadata.provider) {
                messageHTML += `<span class="badge bg-blue-lt text-blue">${metadata.provider}</span>`;
            }
            
            if (metadata.tokens > 0) {
                messageHTML += `<span class="text-muted small">${metadata.tokens} tokens</span>`;
            }
            
            if (metadata.time > 0) {
                messageHTML += `<span class="text-muted small">${metadata.time}ms</span>`;
            }
            
            messageHTML += `</div>`;
        }

        messageHTML += `</div>`;
        messageDiv.innerHTML = messageHTML;
        
        // Add chart container if needed
        if (metadata.chartData) {
            const chartContainer = document.createElement('div');
            chartContainer.className = 'message-chart';
            chartContainer.innerHTML = `<canvas id="chart-${Date.now()}" width="400" height="200"></canvas>`;
            messageDiv.querySelector('.message-bubble').appendChild(chartContainer);
        }

        return messageDiv;
    }

    /**
     * Add chart to message
     */
    addChart(messageElement, response) {
        const chartCanvas = messageElement.querySelector('canvas');
        if (!chartCanvas || !response.chart_suggestion) return;

        const chartConfig = this.generateChartConfig(
            response.chart_suggestion,
            response.columns,
            response.rows
        );

        try {
            const chart = new Chart(chartCanvas.getContext('2d'), chartConfig);
            this.charts[chartCanvas.id] = chart;
        } catch (error) {
            console.error('Error creating chart:', error);
        }
    }

    /**
     * Generate Chart.js configuration
     */
    generateChartConfig(suggestion, columns, rows) {
        const chartType = suggestion.type || 'bar';
        const xColumn = suggestion.x_column || columns[0];
        const yColumn = suggestion.y_column || columns[1];

        const labels = rows.map(row => String(row[columns.indexOf(xColumn)] || ''));
        const data = rows.map(row => row[columns.indexOf(yColumn)] || 0);

        const config = {
            type: chartType,
            data: {
                labels: labels,
                datasets: [{
                    label: yColumn.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
                    data: data,
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: suggestion.title || 'Data Visualization'
                    },
                    legend: {
                        display: chartType === 'pie'
                    }
                },
                scales: chartType !== 'pie' ? {
                    y: {
                        beginAtZero: true
                    }
                } : {}
            }
        };

        // Color schemes
        if (chartType === 'bar') {
            config.data.datasets[0].backgroundColor = 'rgba(54, 162, 235, 0.5)';
            config.data.datasets[0].borderColor = 'rgba(54, 162, 235, 1)';
        } else if (chartType === 'line') {
            config.data.datasets[0].backgroundColor = 'rgba(255, 99, 132, 0.1)';
            config.data.datasets[0].borderColor = 'rgba(255, 99, 132, 1)';
            config.data.datasets[0].fill = true;
        } else if (chartType === 'pie') {
            config.data.datasets[0].backgroundColor = [
                'rgba(255, 99, 132, 0.8)',
                'rgba(54, 162, 235, 0.8)',
                'rgba(255, 205, 86, 0.8)',
                'rgba(75, 192, 192, 0.8)',
                'rgba(153, 102, 255, 0.8)',
                'rgba(255, 159, 64, 0.8)'
            ];
        }

        return config;
    }


    /**
     * Generate results table HTML for chat messages
     */
    generateResultsTable(columns, rows) {
        // For small result sets, show as a simple table
        if (rows.length <= 10) {
            let html = `<div class="table-responsive mt-3">
                <table class="table table-sm table-bordered">
                    <thead class="table-light">
                        <tr>`;
            
            columns.forEach(col => {
                html += `<th class="fw-bold">${this.escapeHtml(col)}</th>`;
            });
            
            html += `</tr></thead><tbody>`;
            
            rows.forEach(row => {
                html += '<tr>';
                row.forEach(cell => {
                    html += `<td>${this.escapeHtml(String(cell || ''))}</td>`;
                });
                html += '</tr>';
            });
            
            html += `</tbody></table></div>`;
            return html;
        }
        
        // For larger result sets, show summary with expandable table
        let html = `<div class="mt-3">
            <div class="d-flex align-items-center mb-2">
                <strong>Results (${rows.length} rows)</strong>
                <button class="btn btn-sm btn-outline-primary ms-auto" onclick="this.nextElementSibling.classList.toggle('d-none')">
                    <i class="ti ti-eye me-1"></i>View Table
                </button>
            </div>
            <div class="table-responsive d-none">
                <table class="table table-sm table-bordered">
                    <thead class="table-light">
                        <tr>`;
        
        columns.forEach(col => {
            html += `<th class="fw-bold">${this.escapeHtml(col)}</th>`;
        });
        
        html += `</tr></thead><tbody>`;
        
        // Show first 50 rows
        rows.slice(0, 50).forEach(row => {
            html += '<tr>';
            row.forEach(cell => {
                html += `<td>${this.escapeHtml(String(cell || ''))}</td>`;
            });
            html += '</tr>';
        });
        
        html += `</tbody></table>`;
        
        if (rows.length > 50) {
            html += `<div class="text-muted small">Showing first 50 of ${rows.length} rows</div>`;
        }
        
        html += `</div></div>`;
        
        return html;
    }

    /**
     * Show/hide typing indicator
     */
    showTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.style.display = 'flex';
            this.scrollToBottom();
        }
    }

    hideTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.style.display = 'none';
        }
    }

    /**
     * Set processing state
     */
    setProcessing(processing) {
        this.isProcessing = processing;
        
        const sendButton = document.getElementById('send-button');
        const stopButton = document.getElementById('stop-button');
        const messageInput = document.getElementById('message-input');
        
        if (sendButton) {
            sendButton.disabled = processing;
            sendButton.classList.toggle('button-loading', processing);
        }
        
        if (stopButton) {
            stopButton.style.display = processing ? 'block' : 'none';
        }
        
        if (messageInput) {
            messageInput.disabled = processing;
        }
    }

    /**
     * Handle input changes
     */
    handleInputChange(e) {
        this.updateCharCount();
        this.autoResizeTextarea();
    }

    /**
     * Handle keyboard shortcuts
     */
    handleKeyDown(e) {
        const messageInput = document.getElementById('message-input');
        
        // Send message on Ctrl+Enter or Cmd+Enter
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            if (!this.isProcessing) {
                document.getElementById('chat-form').dispatchEvent(new Event('submit'));
            }
        }
        
        // Auto-resize on input
        if (e.key === 'Enter' && !e.ctrlKey && !e.metaKey) {
            setTimeout(() => this.autoResizeTextarea(), 0);
        }
    }

    /**
     * Update character count
     */
    updateCharCount() {
        const messageInput = document.getElementById('message-input');
        const charCount = document.getElementById('char-count');
        
        if (messageInput && charCount) {
            const count = messageInput.value.length;
            charCount.textContent = count;
            charCount.style.color = count > 450 ? '#dc2626' : count > 400 ? '#f59e0b' : '';
        }
    }

    /**
     * Auto-resize textarea
     */
    autoResizeTextarea() {
        const messageInput = document.getElementById('message-input');
        if (messageInput) {
            messageInput.style.height = 'auto';
            messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + 'px';
        }
    }

    /**
     * Scroll to bottom of messages
     */
    scrollToBottom() {
        const messagesContainer = document.getElementById('chat-messages');
        if (messagesContainer) {
            setTimeout(() => {
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }, 100);
        }
    }

    /**
     * Update session statistics
     */
    updateSessionStats(response) {
        this.sessionStats.queries++;
        this.sessionStats.tokens += response.tokens_used || 0;
        this.sessionStats.cost += response.cost_cents || 0;
        this.sessionStats.totalTime += response.processing_time_ms || 0;

        this.displaySessionStats();
    }

    /**
     * Display session statistics
     */
    displaySessionStats() {
        const queriesEl = document.getElementById('queries-count');
        const tokensEl = document.getElementById('tokens-count');
        const costEl = document.getElementById('cost-total');
        const avgTimeEl = document.getElementById('avg-time');

        if (queriesEl) queriesEl.textContent = this.sessionStats.queries;
        if (tokensEl) tokensEl.textContent = this.formatNumber(this.sessionStats.tokens);
        if (costEl) costEl.textContent = this.formatCost(this.sessionStats.cost);
        if (avgTimeEl) {
            const avgTime = this.sessionStats.queries > 0 
                ? Math.round(this.sessionStats.totalTime / this.sessionStats.queries)
                : 0;
            avgTimeEl.textContent = `${avgTime}ms`;
        }
    }

    /**
     * Load session statistics from storage
     */
    loadSessionStats() {
        try {
            const stored = localStorage.getItem('chatbot-session-stats');
            if (stored) {
                this.sessionStats = JSON.parse(stored);
                this.displaySessionStats();
            }
        } catch (error) {
            console.warn('Failed to load session stats:', error);
        }
    }

    /**
     * Save session statistics to storage
     */
    saveSessionStats() {
        try {
            localStorage.setItem('chatbot-session-stats', JSON.stringify(this.sessionStats));
        } catch (error) {
            console.warn('Failed to save session stats:', error);
        }
    }

    /**
     * Refresh provider status
     */
    async refreshProviderStatus() {
        try {
            const response = await fetch('/chatbot/status');
            if (response.ok) {
                const status = await response.json();
                this.updateProviderStatus(status);
            }
        } catch (error) {
            console.warn('Failed to refresh provider status:', error);
        }
    }

    /**
     * Update provider status display
     */
    updateProviderStatus(status) {
        const indicator = document.getElementById('provider-indicator');
        const statusContainer = document.getElementById('provider-status');

        // Update main indicator
        if (indicator) {
            const hasOnline = Object.values(status).some(s => s.available);
            indicator.className = hasOnline 
                ? 'badge bg-green-lt text-green'
                : 'badge bg-red-lt text-red';
            indicator.innerHTML = hasOnline 
                ? '<i class="ti ti-circle-filled"></i> AI Ready'
                : '<i class="ti ti-circle-filled"></i> AI Offline';
        }

        // Update detailed status
        if (statusContainer) {
            let html = '';
            Object.entries(status).forEach(([name, info]) => {
                html += `
                    <div class="d-flex align-items-center mb-2">
                        <span class="badge bg-${info.available ? 'green' : 'red'}-lt text-${info.available ? 'green' : 'red'} me-2">
                            <i class="ti ti-circle-filled"></i>
                        </span>
                        <div class="flex-grow-1">
                            <strong>${name.charAt(0).toUpperCase() + name.slice(1)}</strong>
                            <div class="text-muted small">
                                ${info.available ? `${info.models?.length || 0} models available` : 'Offline'}
                            </div>
                        </div>
                    </div>
                `;
            });
            statusContainer.innerHTML = html;
        }
    }

    /**
     * Utility methods
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    formatNumber(num) {
        if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
        if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
        return num.toString();
    }

    formatCost(cents) {
        if (cents === 0) return 'Free';
        const dollars = cents / 100;
        return dollars < 0.01 ? `${cents}¢` : `$${dollars.toFixed(2)}`;
    }

    getSelectedProvider() {
        // Default to ollama for now
        return 'ollama';
    }

    getSelectedModel() {
        // Get selected model from header dropdown
        const modelSelector = document.getElementById('model-selector-header');
        if (modelSelector && modelSelector.value) {
            return modelSelector.value;
        }
        // Default to first available model
        return this.config.availableModels?.[0]?.model || 'dolphin-mistral:latest';
    }

    /**
     * Public methods for global access
     */
    static copySQL(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            navigator.clipboard.writeText(element.textContent).then(() => {
                // Show success feedback
                const button = element.parentElement.querySelector('button');
                if (button) {
                    const originalHTML = button.innerHTML;
                    button.innerHTML = '<i class="ti ti-check"></i>';
                    setTimeout(() => {
                        button.innerHTML = originalHTML;
                    }, 1000);
                }
            }).catch(err => {
                console.error('Failed to copy SQL:', err);
            });
        }
    }

    static scrollToBottom() {
        if (window.ChatBot) {
            window.ChatBot.scrollToBottom();
        }
    }

    showError(message) {
        this.addMessage('error', message);
    }

    updateUI() {
        this.displaySessionStats();
        this.updateCharCount();
    }
}

// Global functions for template access
window.insertQuickQuery = function(query) {
    const messageInput = document.getElementById('message-input');
    if (messageInput) {
        messageInput.value = query;
        messageInput.focus();
        if (window.ChatBot) {
            window.ChatBot.updateCharCount();
            window.ChatBot.autoResizeTextarea();
        }
    }
};

window.clearMessages = function() {
    const messagesContainer = document.getElementById('chat-messages');
    if (messagesContainer && confirm('Clear all messages?')) {
        // Keep only typing indicator
        const typingIndicator = document.getElementById('typing-indicator');
        messagesContainer.innerHTML = '';
        if (typingIndicator) {
            messagesContainer.appendChild(typingIndicator);
        }
        
        // Reset session stats
        if (window.ChatBot) {
            window.ChatBot.sessionStats = { queries: 0, tokens: 0, cost: 0, totalTime: 0 };
            window.ChatBot.displaySessionStats();
            window.ChatBot.saveSessionStats();
        }
    }
};

window.newConversation = function() {
    if (confirm('Start a new conversation? This will clear the current chat.')) {
        window.location.reload();
    }
};

window.stopGeneration = function() {
    if (window.ChatBot && window.ChatBot.currentRequest) {
        window.ChatBot.currentRequest.abort();
        window.ChatBot.setProcessing(false);
        window.ChatBot.hideTypingIndicator();
        window.ChatBot.addMessage('system', 'Generation stopped by user');
    }
};

window.showProviderStatus = function() {
    const modal = new bootstrap.Modal(document.getElementById('provider-status-modal'));
    modal.show();
};

window.showConversationHistory = function() {
    const modal = new bootstrap.Modal(document.getElementById('conversation-history-modal'));
    modal.show();
};

window.exportResults = function(format) {
    console.log(`Exporting results as ${format}`);
    // TODO: Implement export functionality
};

window.exportChart = function() {
    console.log('Exporting chart');
    // TODO: Implement chart export
};

window.validateModel = async function(modelName) {
    console.log('🔄 Validating model:', modelName);
    const statusIndicator = document.getElementById('status-indicator');
    const statusText = document.getElementById('status-text');
    
    if (!statusIndicator || !statusText) {
        console.error('❌ Status elements not found');
        return;
    }
    
    // Show yellow/loading state
    statusIndicator.className = 'badge bg-yellow-lt text-yellow me-2';
    statusIndicator.innerHTML = '<i class="ti ti-circle-filled"></i>';
    statusText.textContent = 'Validating...';
    console.log('🟡 Status set to validating');
    
    try {
        const response = await fetch('/chatbot/status');
        if (response.ok) {
            const status = await response.json();
            console.log('📡 Status response:', status);
            
            // Check if the selected model is available
            let modelAvailable = false;
            for (const [provider, info] of Object.entries(status)) {
                if (info.available && info.models && info.models.includes(modelName)) {
                    modelAvailable = true;
                    console.log('✅ Model found in provider:', provider);
                    break;
                }
            }
            
            if (modelAvailable) {
                statusIndicator.className = 'badge bg-green-lt text-green me-2';
                statusIndicator.innerHTML = '<i class="ti ti-circle-filled"></i>';
                statusText.textContent = 'Model Ready';
                console.log('🟢 Status set to ready');
            } else {
                statusIndicator.className = 'badge bg-red-lt text-red me-2';
                statusIndicator.innerHTML = '<i class="ti ti-circle-filled"></i>';
                statusText.textContent = 'Model Offline';
                console.log('🔴 Status set to offline');
            }
        } else {
            statusIndicator.className = 'badge bg-red-lt text-red me-2';
            statusIndicator.innerHTML = '<i class="ti ti-circle-filled"></i>';
            statusText.textContent = 'Connection Error';
            console.log('🔴 Connection error');
        }
    } catch (error) {
        console.error('💥 Validation error:', error);
        statusIndicator.className = 'badge bg-red-lt text-red me-2';
        statusIndicator.innerHTML = '<i class="ti ti-circle-filled"></i>';
        statusText.textContent = 'Connection Error';
    }
};

window.clearSession = function() {
    if (confirm('Clear the entire chat session? This cannot be undone.')) {
        // Clear messages container
        const messagesContainer = document.getElementById('chat-messages');
        if (messagesContainer) {
            // Keep only typing indicator
            const typingIndicator = document.getElementById('typing-indicator');
            messagesContainer.innerHTML = '';
            if (typingIndicator) {
                messagesContainer.appendChild(typingIndicator);
            }
        }
        
        // Reset session stats
        if (window.ChatBot) {
            window.ChatBot.sessionStats = { queries: 0, tokens: 0, cost: 0, totalTime: 0 };
            window.ChatBot.displaySessionStats();
            window.ChatBot.saveSessionStats();
        }
        
        // Reset query counter in header
        const queriesCount = document.getElementById('queries-count');
        if (queriesCount) {
            queriesCount.textContent = '0';
        }
        
        // Focus on input
        const messageInput = document.getElementById('message-input');
        if (messageInput) {
            messageInput.focus();
        }
    }
};

// Initialize global ChatBot instance
window.ChatBot = new ChatBot();

// Auto-save session stats periodically
setInterval(() => {
    if (window.ChatBot) {
        window.ChatBot.saveSessionStats();
    }
}, 30000); // Every 30 seconds

// Save stats before page unload
window.addEventListener('beforeunload', () => {
    if (window.ChatBot) {
        window.ChatBot.saveSessionStats();
    }
});