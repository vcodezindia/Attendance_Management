// Main JavaScript file for Attendance Management System

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    const popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Form validation enhancement
    const forms = document.querySelectorAll('.needs-validation');
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Attendance marking enhancements
    enhanceAttendanceForm();

    // Export functionality
    setupExportButtons();

    // Auto-save functionality for forms
    setupAutoSave();

    // Search functionality
    setupSearch();
});

// Enhance attendance marking form
function enhanceAttendanceForm() {
    const attendanceForm = document.querySelector('form[action*="mark_attendance"]');
    if (!attendanceForm) return;

    // Add visual feedback when marking attendance
    const radioButtons = attendanceForm.querySelectorAll('input[type="radio"]');
    radioButtons.forEach(function(radio) {
        radio.addEventListener('change', function() {
            const row = this.closest('tr');
            const status = this.value;
            
            // Remove all status classes
            row.classList.remove('table-success', 'table-danger', 'table-warning');
            
            // Add appropriate class based on status
            if (status === 'Present') {
                row.classList.add('table-success');
            } else if (status === 'Absent') {
                row.classList.add('table-danger');
            } else if (status === 'Late') {
                row.classList.add('table-warning');
            }
            
            // Show save reminder
            showSaveReminder();
        });
    });

    // Bulk actions for attendance
    window.markAllPresent = function() {
        const presentRadios = attendanceForm.querySelectorAll('input[type="radio"][value="Present"]');
        presentRadios.forEach(function(radio) {
            radio.checked = true;
            radio.dispatchEvent(new Event('change'));
        });
        showNotification('All students marked as Present', 'success');
    };

    window.markAllAbsent = function() {
        const absentRadios = attendanceForm.querySelectorAll('input[type="radio"][value="Absent"]');
        absentRadios.forEach(function(radio) {
            radio.checked = true;
            radio.dispatchEvent(new Event('change'));
        });
        showNotification('All students marked as Absent', 'warning');
    };

    // Confirm before submitting attendance
    attendanceForm.addEventListener('submit', function(event) {
        const checkedRadios = attendanceForm.querySelectorAll('input[type="radio"]:checked');
        const totalStudents = attendanceForm.querySelectorAll('input[type="radio"][value="Present"]').length;
        
        if (checkedRadios.length === 0) {
            event.preventDefault();
            showNotification('Please mark attendance for at least one student', 'error');
            return;
        }
        
        if (checkedRadios.length < totalStudents) {
            if (!confirm(`You have only marked attendance for ${checkedRadios.length} out of ${totalStudents} students. Continue?`)) {
                event.preventDefault();
                return;
            }
        }
        
        // Show loading state
        const submitBtn = attendanceForm.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Saving...';
        submitBtn.disabled = true;
        
        // Re-enable button after form submission (in case of errors)
        setTimeout(function() {
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }, 5000);
    });
}

// Setup export buttons
function setupExportButtons() {
    const exportButtons = document.querySelectorAll('[href*="export"]');
    exportButtons.forEach(function(button) {
        button.addEventListener('click', function(event) {
            const originalText = button.innerHTML;
            button.innerHTML = '<i class="bi bi-hourglass-split"></i> Exporting...';
            button.classList.add('disabled');
            
            // Re-enable button after a delay
            setTimeout(function() {
                button.innerHTML = originalText;
                button.classList.remove('disabled');
            }, 3000);
        });
    });
}

// Setup auto-save functionality
function setupAutoSave() {
    const forms = document.querySelectorAll('form[data-autosave]');
    forms.forEach(function(form) {
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(function(input) {
            input.addEventListener('change', function() {
                saveFormData(form);
            });
        });
        
        // Load saved data on page load
        loadFormData(form);
    });
}

// Save form data to localStorage
function saveFormData(form) {
    const formData = new FormData(form);
    const data = {};
    for (let [key, value] of formData.entries()) {
        data[key] = value;
    }
    localStorage.setItem('form_' + form.id, JSON.stringify(data));
}

// Load form data from localStorage
function loadFormData(form) {
    const savedData = localStorage.getItem('form_' + form.id);
    if (savedData) {
        const data = JSON.parse(savedData);
        for (let [key, value] of Object.entries(data)) {
            const input = form.querySelector(`[name="${key}"]`);
            if (input) {
                input.value = value;
            }
        }
    }
}

// Setup search functionality
function setupSearch() {
    const searchInputs = document.querySelectorAll('[data-search]');
    searchInputs.forEach(function(input) {
        const targetSelector = input.dataset.search;
        const targets = document.querySelectorAll(targetSelector);
        
        input.addEventListener('input', function() {
            const query = this.value.toLowerCase();
            targets.forEach(function(target) {
                const text = target.textContent.toLowerCase();
                const row = target.closest('tr') || target;
                
                if (text.includes(query)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    });
}

// Show notification
function showNotification(message, type = 'info') {
    const alertContainer = document.querySelector('.container');
    const alert = document.createElement('div');
    alert.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    alertContainer.insertBefore(alert, alertContainer.firstChild);
    
    // Auto-hide after 3 seconds
    setTimeout(function() {
        const bsAlert = new bootstrap.Alert(alert);
        bsAlert.close();
    }, 3000);
}

// Show save reminder
function showSaveReminder() {
    const reminder = document.getElementById('save-reminder');
    if (reminder) {
        reminder.style.display = 'block';
    } else {
        const newReminder = document.createElement('div');
        newReminder.id = 'save-reminder';
        newReminder.className = 'alert alert-warning position-fixed top-0 end-0 m-3';
        newReminder.style.zIndex = '9999';
        newReminder.innerHTML = `
            <i class="bi bi-exclamation-triangle"></i> Don't forget to save your changes!
            <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
        `;
        document.body.appendChild(newReminder);
        
        // Auto-hide after 5 seconds
        setTimeout(function() {
            if (newReminder.parentElement) {
                newReminder.remove();
            }
        }, 5000);
    }
}

// Date picker enhancement
function setupDatePickers() {
    const datePickers = document.querySelectorAll('input[type="date"]');
    datePickers.forEach(function(picker) {
        // Set max date to today for attendance dates
        if (picker.name === 'date' || picker.classList.contains('attendance-date')) {
            picker.max = new Date().toISOString().split('T')[0];
        }
    });
}

// Initialize date pickers when DOM is loaded
document.addEventListener('DOMContentLoaded', setupDatePickers);

// Keyboard shortcuts
document.addEventListener('keydown', function(event) {
    // Ctrl/Cmd + S to save forms
    if ((event.ctrlKey || event.metaKey) && event.key === 's') {
        event.preventDefault();
        const submitBtn = document.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.click();
        }
    }
    
    // Escape to close modals
    if (event.key === 'Escape') {
        const openModal = document.querySelector('.modal.show');
        if (openModal) {
            const modal = bootstrap.Modal.getInstance(openModal);
            modal.hide();
        }
    }
});

// Print functionality
function printPage() {
    window.print();
}

// Export functionality helpers
function exportTableToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const csv = [];
    const rows = table.querySelectorAll('tr');
    
    for (let i = 0; i < rows.length; i++) {
        const row = [];
        const cols = rows[i].querySelectorAll('td, th');
        
        for (let j = 0; j < cols.length; j++) {
            let text = cols[j].innerText;
            text = text.replace(/"/g, '""'); // Escape quotes
            row.push('"' + text + '"');
        }
        
        csv.push(row.join(','));
    }
    
    downloadCSV(csv.join('\n'), filename);
}

function downloadCSV(csvContent, filename) {
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    
    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

// Theme toggle (if needed)
function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-bs-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    html.setAttribute('data-bs-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}

// Load saved theme
function loadTheme() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        document.documentElement.setAttribute('data-bs-theme', savedTheme);
    }
}

// Initialize theme on page load
document.addEventListener('DOMContentLoaded', loadTheme);
