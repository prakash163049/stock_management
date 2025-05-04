// Currency Formatting
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(amount);
}

// Update all currency values on the page
function updateCurrencyValues() {
    // Update table cells with currency values
    document.querySelectorAll('td[data-currency]').forEach(cell => {
        const amount = parseFloat(cell.getAttribute('data-currency'));
        if (!isNaN(amount)) {
            cell.textContent = formatCurrency(amount);
        }
    });

    // Update card values with currency
    document.querySelectorAll('.card-value').forEach(element => {
        const amount = parseFloat(element.getAttribute('data-value'));
        if (!isNaN(amount)) {
            element.textContent = formatCurrency(amount);
        }
    });

    // Update form inputs with currency
    document.querySelectorAll('input[data-currency]').forEach(input => {
        const amount = parseFloat(input.value);
        if (!isNaN(amount)) {
            input.value = formatCurrency(amount);
        }
    });
}

// Update stock level indicators
function updateStockLevels() {
    document.querySelectorAll('[data-stock-level]').forEach(element => {
        const quantity = parseInt(element.dataset.quantity);
        const minStock = parseInt(element.dataset.minStock);
        
        if (quantity <= minStock) {
            element.classList.add('stock-low');
        } else if (quantity <= minStock * 2) {
            element.classList.add('stock-medium');
        } else {
            element.classList.add('stock-high');
        }
    });
}

// Initialize Bootstrap tooltips
document.addEventListener('DOMContentLoaded', function() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize stock level indicators
    updateStockLevels();
    
    // Initialize currency formatting
    updateCurrencyValues();
    
    // Initialize alert auto-dismiss
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
});

// Form validation
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return true;
    
    let isValid = true;
    const requiredFields = form.querySelectorAll('[required]');
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            isValid = false;
        } else {
            field.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

// Inventory Management Functions
function filterByCategory() {
    const category = document.getElementById('categoryFilter').value;
    window.location.href = `/inventory?category=${encodeURIComponent(category)}`;
}

function updateQuantity(productId, action) {
    const quantityInput = document.getElementById(`quantity-${productId}`);
    const currentQuantity = parseInt(quantityInput.value);
    
    let newQuantity;
    if (action === 'increase') {
        newQuantity = currentQuantity + 1;
    } else if (action === 'decrease' && currentQuantity > 0) {
        newQuantity = currentQuantity - 1;
    } else {
        return;
    }

    fetch('/update_quantity', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            product_id: productId,
            quantity: newQuantity
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            quantityInput.value = newQuantity;
            updateStatusBadge(productId, newQuantity, data.min_stock);
            updateCategoryStats();
        } else {
            alert('Failed to update quantity. Please try again.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while updating the quantity.');
    });
}

function updateStatusBadge(productId, quantity, minStock) {
    const statusBadge = document.getElementById(`status-${productId}`);
    statusBadge.className = 'status-badge';
    
    if (quantity === 0) {
        statusBadge.classList.add('status-out-of-stock');
        statusBadge.textContent = 'Out of Stock';
    } else if (quantity <= minStock) {
        statusBadge.classList.add('status-low-stock');
        statusBadge.textContent = 'Low Stock';
    } else {
        statusBadge.classList.add('status-in-stock');
        statusBadge.textContent = 'In Stock';
    }
}

function updateCategoryStats() {
    fetch('/get_category_stats')
        .then(response => response.json())
        .then(data => {
            Object.entries(data).forEach(([category, stats]) => {
                const countElement = document.getElementById(`${category}-count`);
                const quantityElement = document.getElementById(`${category}-quantity`);
                const valueElement = document.getElementById(`${category}-value`);
                
                if (countElement) countElement.textContent = stats.count;
                if (quantityElement) quantityElement.textContent = stats.total_quantity;
                if (valueElement) valueElement.textContent = `$${stats.total_value.toFixed(2)}`;
            });
        })
        .catch(error => console.error('Error updating category stats:', error));
}

// Sidebar Toggle
document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.getElementById('sidebar');
    const content = document.getElementById('content');
    const sidebarCollapse = document.getElementById('sidebarCollapse');
    
    // Initialize currency formatting
    updateCurrencyValues();
    
    // Toggle sidebar
    sidebarCollapse.addEventListener('click', function() {
        sidebar.classList.toggle('collapsed');
        content.classList.toggle('expanded');
    });
    
    // Handle mobile sidebar
    function handleMobileSidebar() {
        if (window.innerWidth <= 768) {
            sidebar.classList.add('collapsed');
            content.classList.add('expanded');
        } else {
            sidebar.classList.remove('collapsed');
            content.classList.remove('expanded');
        }
    }
    
    // Initial check
    handleMobileSidebar();
    
    // Check on resize
    window.addEventListener('resize', handleMobileSidebar);
    
    // Add active class to current navigation item
    const currentLocation = location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentLocation) {
            link.classList.add('active');
        }
    });
});

// Add hover effect to cards
document.querySelectorAll('.card').forEach(card => {
    card.addEventListener('mouseenter', function() {
        this.style.transform = 'translateY(-5px)';
    });
    
    card.addEventListener('mouseleave', function() {
        this.style.transform = 'translateY(0)';
    });
});

// Add loading animation for forms
document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function() {
        const submitButton = this.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
            submitButton.disabled = true;
        }
    });
});

// Add tooltips
document.addEventListener('DOMContentLoaded', function() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Add fade-in animation for alerts
document.querySelectorAll('.alert').forEach(alert => {
    alert.style.opacity = '0';
    alert.style.transform = 'translateY(-20px)';
    
    setTimeout(() => {
        alert.style.transition = 'all 0.3s ease';
        alert.style.opacity = '1';
        alert.style.transform = 'translateY(0)';
    }, 100);
});

// Add responsive table functionality
document.querySelectorAll('.table-responsive').forEach(table => {
    const wrapper = document.createElement('div');
    wrapper.className = 'table-responsive-wrapper';
    table.parentNode.insertBefore(wrapper, table);
    wrapper.appendChild(table);
});

// Add search functionality to tables
document.querySelectorAll('input[type="search"]').forEach(searchInput => {
    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        const table = this.closest('.table-responsive').querySelector('table');
        const rows = table.querySelectorAll('tbody tr');
        
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(searchTerm) ? '' : 'none';
        });
    });
});

// Add confirmation for delete actions
document.querySelectorAll('form[data-confirm]').forEach(form => {
    form.addEventListener('submit', function(e) {
        if (!confirm(this.dataset.confirm)) {
            e.preventDefault();
        }
    });
});

// Add smooth scrolling
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        document.querySelector(this.getAttribute('href')).scrollIntoView({
            behavior: 'smooth'
        });
    });
}); 