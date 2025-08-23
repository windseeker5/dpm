/**
 * Payment Bot Settings JavaScript
 * Handles test email sending, payment logs display, and UI interactions
 */

document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const enableSwitch = document.getElementById('enable_email_payment_bot');
    const configSection = document.getElementById('email-bot-config');
    const testEmailCard = document.getElementById('test-email-card');
    const paymentLogsCard = document.getElementById('payment-logs-card');
    const thresholdSlider = document.getElementById('threshold-slider');
    const thresholdValue = document.getElementById('threshold-value');
    const testPaymentForm = document.getElementById('test-payment-form');
    const refreshLogsBtn = document.getElementById('refresh-logs-btn');
    const testEmailResult = document.getElementById('test-email-result');
    
    // Auto-refresh interval for payment logs
    let logsRefreshInterval = null;
    
    /**
     * Initialize UI based on bot enable state
     */
    function initializeUI() {
        if (enableSwitch && enableSwitch.checked) {
            showBotSections();
            loadPaymentLogs();
            startLogsAutoRefresh();
        }
    }
    
    /**
     * Show bot configuration sections
     */
    function showBotSections() {
        if (configSection) configSection.style.display = 'block';
        if (testEmailCard) testEmailCard.style.display = 'block';
        if (paymentLogsCard) paymentLogsCard.style.display = 'block';
    }
    
    /**
     * Hide bot configuration sections
     */
    function hideBotSections() {
        if (configSection) configSection.style.display = 'none';
        if (testEmailCard) testEmailCard.style.display = 'none';
        if (paymentLogsCard) paymentLogsCard.style.display = 'none';
        stopLogsAutoRefresh();
    }
    
    /**
     * Handle enable switch toggle
     */
    if (enableSwitch) {
        enableSwitch.addEventListener('change', function() {
            if (this.checked) {
                showBotSections();
                loadPaymentLogs();
                startLogsAutoRefresh();
            } else {
                hideBotSections();
            }
        });
    }
    
    /**
     * Handle threshold slider
     */
    if (thresholdSlider && thresholdValue) {
        thresholdSlider.addEventListener('input', function() {
            thresholdValue.textContent = this.value;
        });
    }
    
    /**
     * Handle test payment form submission
     */
    const sendTestBtn = document.getElementById('send-test-btn');
    if (sendTestBtn) {
        sendTestBtn.addEventListener('click', async function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const senderName = document.getElementById('test-sender-name').value;
            const amount = document.getElementById('test-amount').value;
            
            // Validate inputs
            if (!senderName || !amount) {
                showTestResult('danger', 'Please fill in all required fields');
                return;
            }
            
            // Disable button during send
            this.disabled = true;
            this.innerHTML = '<i class="ti ti-loader-2 me-2"></i> Sending...';
            
            // Clear previous results
            testEmailResult.innerHTML = '';
            
            try {
                const formData = new FormData();
                formData.append('sender_name', senderName);
                formData.append('amount', amount);
                formData.append('csrf_token', getCSRFToken());
                
                const response = await fetch('/api/payment-bot/test-email', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    showTestResult('success', data.message || 'Test email sent successfully!');
                    // Clear form
                    if (testPaymentForm) testPaymentForm.reset();
                } else {
                    showTestResult('danger', data.error || 'Failed to send test email');
                }
            } catch (error) {
                console.error('Error sending test email:', error);
                showTestResult('danger', 'Network error. Please try again.');
            } finally {
                // Re-enable button
                this.disabled = false;
                this.innerHTML = '<i class="ti ti-send me-2"></i> Send Test Payment Email';
            }
        });
    }
    
    /**
     * Show test email result message
     */
    function showTestResult(type, message) {
        const alertClass = type === 'success' ? 'alert-success' : 'alert-danger';
        const icon = type === 'success' ? 'ti-check' : 'ti-x';
        
        testEmailResult.innerHTML = `
            <div class="alert ${alertClass} alert-dismissible" role="alert">
                <div class="d-flex">
                    <div>
                        <i class="ti ${icon} me-2"></i>
                    </div>
                    <div>${message}</div>
                </div>
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            const alert = testEmailResult.querySelector('.alert');
            if (alert) {
                alert.remove();
            }
        }, 5000);
    }
    
    /**
     * Load payment logs from API
     */
    async function loadPaymentLogs() {
        const tbody = document.getElementById('payment-logs-tbody');
        if (!tbody) return;
        
        try {
            const response = await fetch('/api/payment-bot/logs');
            const data = await response.json();
            
            if (response.ok && data.logs) {
                displayPaymentLogs(data.logs);
            } else {
                tbody.innerHTML = '<tr><td colspan="5" class="text-center text-danger">Failed to load payment logs</td></tr>';
            }
        } catch (error) {
            console.error('Error loading payment logs:', error);
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-danger">Error loading payment logs</td></tr>';
        }
    }
    
    /**
     * Display payment logs in table
     */
    function displayPaymentLogs(logs) {
        const tbody = document.getElementById('payment-logs-tbody');
        if (!tbody) return;
        
        if (logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No payment logs found</td></tr>';
            return;
        }
        
        tbody.innerHTML = logs.map(log => `
            <tr>
                <td>${log.date_sent}</td>
                <td>${log.bank_info_name}</td>
                <td>$${log.amount.toFixed(2)}</td>
                <td>
                    ${log.matched_pass ? 
                        '<span class="badge bg-success">Matched</span>' : 
                        '<span class="badge bg-secondary">Unmatched</span>'}
                </td>
                <td>
                    ${log.match_confidence > 0 ? 
                        `<span class="text-${log.match_confidence >= 85 ? 'success' : 'warning'}">${log.match_confidence}%</span>` : 
                        '<span class="text-muted">-</span>'}
                </td>
            </tr>
        `).join('');
    }
    
    /**
     * Start auto-refresh for payment logs
     */
    function startLogsAutoRefresh() {
        // Refresh every 30 seconds
        logsRefreshInterval = setInterval(loadPaymentLogs, 30000);
    }
    
    /**
     * Stop auto-refresh for payment logs
     */
    function stopLogsAutoRefresh() {
        if (logsRefreshInterval) {
            clearInterval(logsRefreshInterval);
            logsRefreshInterval = null;
        }
    }
    
    /**
     * Handle manual refresh button
     */
    if (refreshLogsBtn) {
        refreshLogsBtn.addEventListener('click', function() {
            // Add spinning animation
            this.classList.add('spin');
            loadPaymentLogs().then(() => {
                // Remove spinning after load
                setTimeout(() => {
                    this.classList.remove('spin');
                }, 500);
            });
        });
    }
    
    /**
     * Get CSRF token from form
     */
    function getCSRFToken() {
        const tokenInput = document.querySelector('input[name="csrf_token"]');
        return tokenInput ? tokenInput.value : '';
    }
    
    /**
     * Add spinning animation CSS
     */
    const style = document.createElement('style');
    style.textContent = `
        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        .spin i {
            animation: spin 1s linear infinite;
        }
    `;
    document.head.appendChild(style);
    
    // Initialize on load
    initializeUI();
    
    // Clean up on page unload
    window.addEventListener('beforeunload', function() {
        stopLogsAutoRefresh();
    });
});