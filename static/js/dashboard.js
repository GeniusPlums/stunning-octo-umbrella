// Dashboard.js - Main JavaScript for Space Station Cargo Management System

document.addEventListener('DOMContentLoaded', function() {
    // Initialize modals
    setupModalListeners();
    
    // Navigation active state based on current page
    setActiveNavLink();
    
    // Initialize operations listeners
    initializeOperationListeners();
    
    // Initialize containers if needed
    if (document.getElementById('undockingContainerId')) {
        fetchContainers();
    }
    
    // Initialize feather icons for any dynamically added elements
    feather.replace();
});

// Set active navigation link based on current page
function setActiveNavLink() {
    const currentPath = window.location.pathname;
    
    // Find all nav links
    const navLinks = document.querySelectorAll('.sidebar .nav-link');
    
    // Remove active class from all links
    navLinks.forEach(link => {
        link.classList.remove('active');
    });
    
    // Set active class for current page
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href === currentPath) {
            link.classList.add('active');
        }
    });
}

// Set up modal listeners
function setupModalListeners() {
    // New Shipment modal
    document.getElementById('newShipmentBtn')?.addEventListener('click', function() {
        const newShipmentModal = new bootstrap.Modal(document.getElementById('newShipmentModal'));
        newShipmentModal.show();
    });
    
    // Process Shipment button
    document.getElementById('processShipmentBtn')?.addEventListener('click', function() {
        processNewShipment();
    });
    
    // Retrieve Item modal
    document.getElementById('retrieveItemBtn')?.addEventListener('click', function() {
        const retrieveItemModal = new bootstrap.Modal(document.getElementById('retrieveItemModal'));
        retrieveItemModal.show();
    });
    
    // Search Item button
    document.getElementById('searchItemBtn')?.addEventListener('click', function() {
        retrieveItem();
    });
    
    // Waste Disposal modal
    document.getElementById('wasteDisposalBtn')?.addEventListener('click', function() {
        fetchContainers().then(() => {
            const wasteDisposalModal = new bootstrap.Modal(document.getElementById('wasteDisposalModal'));
            wasteDisposalModal.show();
        });
    });
    
    // Generate Disposal Plan button
    document.getElementById('generateDisposalPlanBtn')?.addEventListener('click', function() {
        generateWasteDisposalPlan();
    });
    
    // Undock Container modal
    document.getElementById('undockContainerBtn')?.addEventListener('click', function() {
        fetchContainers().then(() => {
            const undockContainerModal = new bootstrap.Modal(document.getElementById('undockContainerModal'));
            undockContainerModal.show();
        });
    });
    
    // Confirm Undock button
    document.getElementById('confirmUndockBtn')?.addEventListener('click', function() {
        performUndock();
    });
}

// Initialize operation listeners
function initializeOperationListeners() {
    // These are the operational buttons that may be on various pages
    
    // Time simulation buttons on simulation page
    document.getElementById('nextDayBtn')?.addEventListener('click', function() {
        simulateTime(1);
    });
    
    document.getElementById('fastForwardBtn')?.addEventListener('click', function() {
        const daysInput = document.getElementById('fastForwardDays')?.value;
        const days = daysInput ? parseInt(daysInput) : 7;
        
        if (days && !isNaN(days) && days > 0) {
            simulateTime(days);
        } else {
            showAlert('warning', 'Please enter a valid number of days');
        }
    });

    // Add used items selection
    document.getElementById('selectItemsBtn')?.addEventListener('click', function() {
        const selectedItems = [];
        document.querySelectorAll('.item-checkbox:checked').forEach(checkbox => {
            selectedItems.push(checkbox.value);
        });
        
        // Store selected items for simulation
        document.getElementById('selectedItemsCount').textContent = selectedItems.length;
        document.getElementById('selectedItemsDisplay').innerHTML = selectedItems.map(id => 
            `<span class="badge bg-primary me-1">${id}</span>`
        ).join('');
        
        // Store in hidden field
        document.getElementById('usedItemsInput').value = JSON.stringify(selectedItems);
    });
}

// Process a new shipment
function processNewShipment() {
    const itemsTextarea = document.getElementById('shipmentItems');
    
    try {
        const items = JSON.parse(itemsTextarea.value);
        
        if (!Array.isArray(items)) {
            throw new Error('Items must be an array');
        }
        
        // Get containers
        fetch('/api/containers')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Prepare request payload
                    const payload = {
                        items: items,
                        containers: data.containers
                    };
                    
                    // Send request to API
                    fetch('/api/placement', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(payload)
                    })
                    .then(response => response.json())
                    .then(result => {
                        if (result.success) {
                            showAlert('success', `Successfully placed ${result.placements.length} items`);
                            
                            // Close modal
                            const modal = bootstrap.Modal.getInstance(document.getElementById('newShipmentModal'));
                            modal.hide();
                            
                            // Clear textarea
                            itemsTextarea.value = '';
                            
                            // Refresh data if on the items page
                            if (window.location.pathname === '/items') {
                                setTimeout(() => {
                                    window.location.reload();
                                }, 1000);
                            }
                        } else {
                            showAlert('danger', result.message || 'Failed to place items');
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        showAlert('danger', 'An error occurred while processing the shipment');
                    });
                } else {
                    showAlert('danger', 'Failed to fetch containers');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showAlert('danger', 'An error occurred while fetching containers');
            });
    } catch (error) {
        console.error('Error parsing JSON:', error);
        showAlert('danger', 'Invalid JSON format: ' + error.message);
    }
}

// Retrieve an item
function retrieveItem() {
    const itemName = document.getElementById('itemNameSearch').value;
    const astronautId = document.getElementById('astronautId').value;
    
    if (!itemName) {
        showAlert('warning', 'Please enter an item name');
        return;
    }
    
    // Prepare URL with query parameters
    const url = new URL('/api/search', window.location.origin);
    url.searchParams.append('name', itemName);
    if (astronautId) {
        url.searchParams.append('astronautId', astronautId);
    }
    
    // Send request
    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Show retrieval instructions
                const retrievalResults = document.getElementById('retrievalResults');
                retrievalResults.classList.remove('d-none');
                
                const retrievalSteps = document.getElementById('retrievalSteps');
                
                // Create steps HTML
                let stepsHtml = '';
                
                if (data.retrievalSteps.length === 0) {
                    stepsHtml = `
                        <div class="alert alert-success mb-0">
                            <i data-feather="check-circle"></i> This item is directly accessible!
                        </div>
                        <div class="mt-3">
                            <strong>Item:</strong> ${data.item.name}<br>
                            <strong>Container:</strong> ${data.container.containerId} (${data.container.zone})<br>
                            <strong>Position:</strong> Width: ${data.item.width}cm, 
                                                      Depth: ${data.item.depth}cm, 
                                                      Height: ${data.item.height}cm
                        </div>
                    `;
                } else {
                    stepsHtml = '<div class="timeline">';
                    
                    data.retrievalSteps.forEach((step, index) => {
                        const isLast = index === data.retrievalSteps.length - 1;
                        const statusClass = isLast ? 'active' : '';
                        
                        stepsHtml += `
                            <div class="timeline-item ${statusClass}">
                                <div class="card">
                                    <div class="card-body">
                                        <h6 class="card-title">Step ${step.step}: ${capitalizeFirstLetter(step.action)}</h6>
                                        <p class="card-text">
                                            ${getStepDescription(step, data)}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        `;
                    });
                    
                    stepsHtml += '</div>';
                }
                
                retrievalSteps.innerHTML = stepsHtml;
                
                // Initialize feather icons for dynamically added elements
                feather.replace();
                
                // If item is now waste, show alert
                if (data.isNowWaste) {
                    showAlert('warning', `Item ${data.item.name} has become waste and should be disposed of`);
                }
            } else {
                showAlert('danger', data.message || 'Failed to find item');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('danger', 'An error occurred while retrieving the item');
        });
}

// Generate step description for retrieval
function getStepDescription(step, data) {
    switch(step.action) {
        case 'remove':
            return `Remove item from container ${step.containerId}`;
        case 'retrieve':
            return `Retrieve ${data.item.name} from container ${step.containerId}`;
        case 'place':
            return `Place item back in container ${step.containerId}`;
        default:
            return `${capitalizeFirstLetter(step.action)} item`;
    }
}

// Generate waste disposal plan
function generateWasteDisposalPlan() {
    const containerId = document.getElementById('undockingContainerId').value;
    const weightLimit = document.getElementById('weightLimit').value;
    
    if (!containerId) {
        showAlert('warning', 'Please select a container');
        return;
    }
    
    // Prepare request payload
    const payload = {
        undockingContainerId: containerId
    };
    
    if (weightLimit && !isNaN(weightLimit)) {
        payload.weightLimit = parseFloat(weightLimit);
    }
    
    // Send request
    fetch('/api/waste/disposal', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show disposal details
            const disposalResults = document.getElementById('disposalResults');
            disposalResults.classList.remove('d-none');
            
            const disposalDetails = document.getElementById('disposalDetails');
            
            // Create details HTML
            const plan = data.disposalPlan;
            let detailsHtml = `
                <div class="mb-3">
                    <h6>Disposal Summary</h6>
                    <ul class="list-group">
                        <li class="list-group-item d-flex justify-content-between align-items-center">
                            Container
                            <span class="badge bg-primary">${plan.undockingContainer}</span>
                        </li>
                        <li class="list-group-item d-flex justify-content-between align-items-center">
                            Total Items
                            <span class="badge bg-primary">${plan.totalItems}</span>
                        </li>
                        <li class="list-group-item d-flex justify-content-between align-items-center">
                            Total Mass
                            <span class="badge bg-primary">${plan.totalMass} kg</span>
                        </li>
                    </ul>
                </div>
            `;
            
            if (plan.disposalSteps.length > 0) {
                detailsHtml += '<h6>Required Steps</h6><div class="timeline">';
                
                plan.disposalSteps.forEach((step, index) => {
                    detailsHtml += `
                        <div class="timeline-item">
                            <div class="card">
                                <div class="card-body">
                                    <h6 class="card-title">Step ${step.step}: ${capitalizeFirstLetter(step.action)}</h6>
                                    <p class="card-text">
                                        ${step.action === 'remove' 
                                            ? `Remove item ${step.itemId} from container ${step.fromContainer}` 
                                            : `Place item ${step.itemId} in container ${step.toContainer}`}
                                    </p>
                                </div>
                            </div>
                        </div>
                    `;
                });
                
                detailsHtml += '</div>';
            } else {
                detailsHtml += `
                    <div class="alert alert-info">
                        <i data-feather="info"></i> No steps required. All waste items are already in the undocking container.
                    </div>
                `;
            }
            
            // Add manifest
            detailsHtml += `
                <h6 class="mt-3">Cargo Manifest</h6>
                <div class="table-responsive">
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>Item ID</th>
                                <th>Name</th>
                                <th>Mass (kg)</th>
                            </tr>
                        </thead>
                        <tbody>
            `;
            
            if (plan.manifest.length > 0) {
                plan.manifest.forEach(item => {
                    detailsHtml += `
                        <tr>
                            <td>${item.itemId}</td>
                            <td>${item.name}</td>
                            <td>${item.mass}</td>
                        </tr>
                    `;
                });
            } else {
                detailsHtml += `
                    <tr>
                        <td colspan="3" class="text-center">No items in manifest</td>
                    </tr>
                `;
            }
            
            detailsHtml += `
                        </tbody>
                    </table>
                </div>
            `;
            
            disposalDetails.innerHTML = detailsHtml;
            
            // Initialize feather icons for dynamically added elements
            feather.replace();
        } else {
            showAlert('danger', data.message || 'Failed to generate disposal plan');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('danger', 'An error occurred while generating the disposal plan');
    });
}

// Perform container undocking
function performUndock() {
    const containerId = document.getElementById('undockContainerId').value;
    
    if (!containerId) {
        showAlert('warning', 'Please select a container');
        return;
    }
    
    // Send request
    fetch('/api/undock', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            containerId: containerId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', data.message || 'Container undocked successfully');
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('undockContainerModal'));
            modal.hide();
            
            // Refresh data if on containers page
            if (window.location.pathname === '/containers') {
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            }
        } else {
            showAlert('danger', data.message || 'Failed to undock container');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('danger', 'An error occurred while undocking the container');
    });
}

// Simulate time advancement
function simulateTime(days, usedItems = []) {
    // Get used items from input if available
    const usedItemsInput = document.getElementById('usedItemsInput');
    if (usedItemsInput && usedItemsInput.value) {
        try {
            usedItems = JSON.parse(usedItemsInput.value);
        } catch (e) {
            console.error('Error parsing used items:', e);
        }
    }
    
    // Send request
    fetch('/api/simulation/time', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            days: days,
            usedItems: usedItems
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const newWaste = data.newWasteItems || 0;
            const expiredItems = data.changes?.expiredItems?.length || 0;
            const usedUpItems = data.changes?.usedUpItems?.length || 0;
            
            showAlert('success', `Advanced time by ${days} day(s). ${expiredItems} items expired. ${usedUpItems} items used up.`);
            
            // Update simulation results if on simulation page
            if (document.getElementById('simulationResults')) {
                updateSimulationResults(data);
            }
            
            // Reset used items
            if (usedItemsInput) {
                usedItemsInput.value = '[]';
                document.getElementById('selectedItemsCount').textContent = '0';
                document.getElementById('selectedItemsDisplay').innerHTML = '';
                
                // Uncheck all checkboxes
                document.querySelectorAll('.item-checkbox').forEach(checkbox => {
                    checkbox.checked = false;
                });
            }
        } else {
            showAlert('danger', data.message || 'Failed to simulate time');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('danger', 'An error occurred while simulating time');
    });
}

// Update simulation results display
function updateSimulationResults(data) {
    const resultsDiv = document.getElementById('simulationResults');
    
    if (!resultsDiv) {
        return;
    }
    
    resultsDiv.classList.remove('d-none');
    
    const changesDiv = document.getElementById('simulationChanges');
    
    // Create results HTML
    const changes = data.changes;
    let changesHtml = `
        <div class="alert alert-info">
            <strong>Time Advanced:</strong> ${changes.date.from} → ${changes.date.to}
        </div>
    `;
    
    // Expired items
    if (changes.expiredItems.length > 0) {
        changesHtml += `
            <div class="card mb-3">
                <div class="card-header bg-warning text-dark">
                    <h6 class="mb-0">Expired Items (${changes.expiredItems.length})</h6>
                </div>
                <div class="card-body p-0">
                    <ul class="list-group list-group-flush">
        `;
        
        changes.expiredItems.forEach(item => {
            changesHtml += `
                <li class="list-group-item d-flex justify-content-between align-items-center">
                    ${item.name}
                    <span class="badge bg-warning text-dark">Expired on ${new Date(item.expiryDate).toLocaleDateString()}</span>
                </li>
            `;
        });
        
        changesHtml += `
                    </ul>
                </div>
            </div>
        `;
    }
    
    // Used up items
    if (changes.usedUpItems.length > 0) {
        changesHtml += `
            <div class="card mb-3">
                <div class="card-header bg-danger">
                    <h6 class="mb-0">Used Up Items (${changes.usedUpItems.length})</h6>
                </div>
                <div class="card-body p-0">
                    <ul class="list-group list-group-flush">
        `;
        
        changes.usedUpItems.forEach(item => {
            changesHtml += `
                <li class="list-group-item d-flex justify-content-between align-items-center">
                    ${item.name}
                    <span class="badge bg-danger">No uses remaining</span>
                </li>
            `;
        });
        
        changesHtml += `
                    </ul>
                </div>
            </div>
        `;
    }
    
    // No changes
    if (changes.expiredItems.length === 0 && changes.usedUpItems.length === 0) {
        changesHtml += `
            <div class="alert alert-success">
                <i data-feather="check-circle"></i> No items expired or were used up during this time period.
            </div>
        `;
    }
    
    changesDiv.innerHTML = changesHtml;
    
    // Initialize feather icons for dynamically added elements
    feather.replace();
}

// Fetch containers for select dropdowns
function fetchContainers() {
    return new Promise((resolve, reject) => {
        fetch('/api/containers')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update container select dropdowns
                    const containerSelects = [
                        document.getElementById('undockingContainerId'),
                        document.getElementById('undockContainerId')
                    ];
                    
                    containerSelects.forEach(select => {
                        if (!select) return;
                        
                        // Clear existing options
                        select.innerHTML = '';
                        
                        // Add default option
                        const defaultOption = document.createElement('option');
                        defaultOption.value = '';
                        defaultOption.textContent = 'Select a container...';
                        select.appendChild(defaultOption);
                        
                        // Add container options
                        data.containers.forEach(container => {
                            const option = document.createElement('option');
                            option.value = container.containerId;
                            option.textContent = `${container.containerId} (${container.zone})`;
                            select.appendChild(option);
                        });
                    });
                    
                    resolve(data.containers);
                } else {
                    showAlert('danger', data.message || 'Failed to fetch containers');
                    reject(new Error(data.message || 'Failed to fetch containers'));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showAlert('danger', 'An error occurred while fetching containers');
                reject(error);
            });
    });
}

// Show an alert message
function showAlert(type, message) {
    const alertContainer = document.getElementById('alertContainer');
    
    if (!alertContainer) {
        console.error('Alert container not found');
        return;
    }
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    alertContainer.appendChild(alertDiv);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        const alertInstance = bootstrap.Alert.getInstance(alertDiv);
        if (alertInstance) {
            alertInstance.close();
        } else {
            alertDiv.remove();
        }
    }, 5000);
}

// Helper function to capitalize first letter
function capitalizeFirstLetter(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}
