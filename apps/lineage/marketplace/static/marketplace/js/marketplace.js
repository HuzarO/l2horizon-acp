/**
 * MARKETPLACE.JS - JavaScript do Marketplace de Personagens
 * Versão: 1.0
 */

(function() {
    'use strict';

    // Main initialization
    document.addEventListener('DOMContentLoaded', function() {
        initMarketplace();
    });

    /**
     * Initialize marketplace functionality
     */
    function initMarketplace() {
        // Initialize components
        initConfirmations();
        initFilters();
        initCharacterPreview();
        initFormValidations();
        
        console.log('Marketplace initialized');
    }

    /**
     * Initialize confirmation dialogs for actions
     */
    function initConfirmations() {
        // Cancel sale confirmations
        const cancelForms = document.querySelectorAll('form[action*="cancel"]');
        cancelForms.forEach(form => {
            form.addEventListener('submit', function(e) {
                if (!confirm('Deseja realmente cancelar esta venda?')) {
                    e.preventDefault();
                }
            });
        });

        // Buy confirmations
        const buyForms = document.querySelectorAll('form[action*="buy"]');
        buyForms.forEach(form => {
            form.addEventListener('submit', function(e) {
                if (!confirm('Confirma a compra deste personagem?')) {
                    e.preventDefault();
                }
            });
        });
    }

    /**
     * Initialize filters for marketplace list
     */
    function initFilters() {
        const filterForm = document.getElementById('filterForm');
        if (!filterForm) return;

        // Level filter
        const minLevel = document.getElementById('minLevel');
        const maxLevel = document.getElementById('maxLevel');
        
        if (minLevel && maxLevel) {
            minLevel.addEventListener('change', function() {
                if (parseInt(maxLevel.value) < parseInt(minLevel.value)) {
                    maxLevel.value = minLevel.value;
                }
            });

            maxLevel.addEventListener('change', function() {
                if (parseInt(maxLevel.value) < parseInt(minLevel.value)) {
                    minLevel.value = maxLevel.value;
                }
            });
        }

        // Price filter
        const minPrice = document.getElementById('minPrice');
        const maxPrice = document.getElementById('maxPrice');
        
        if (minPrice && maxPrice) {
            minPrice.addEventListener('change', function() {
                if (parseFloat(maxPrice.value) < parseFloat(minPrice.value)) {
                    maxPrice.value = minPrice.value;
                }
            });

            maxPrice.addEventListener('change', function() {
                if (parseFloat(maxPrice.value) < parseFloat(minPrice.value)) {
                    minPrice.value = maxPrice.value;
                }
            });
        }

        // Apply filters
        filterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            applyFilters();
        });
    }

    /**
     * Apply marketplace filters
     */
    function applyFilters() {
        const form = document.getElementById('filterForm');
        if (!form) return;

        const formData = new FormData(form);
        const params = new URLSearchParams(formData);
        
        // Reload page with filters
        window.location.href = `${window.location.pathname}?${params.toString()}`;
    }

    /**
     * Initialize character preview in sell form
     */
    function initCharacterPreview() {
        const characterSelect = document.getElementById('character_select');
        if (!characterSelect) return;

        characterSelect.addEventListener('change', function() {
            const charId = this.value;
            if (charId) {
                loadCharacterPreview(charId);
            } else {
                hideCharacterPreview();
            }
        });
    }

    /**
     * Load character preview data
     * @param {string} charId - Character ID
     */
    function loadCharacterPreview(charId) {
        // Show loading state
        const preview = document.getElementById('character_preview');
        if (!preview) return;

        preview.style.display = 'block';
        preview.innerHTML = '<div class="text-center"><i class="fas fa-spinner fa-spin"></i> Carregando...</div>';

        // TODO: Make AJAX call to fetch character details
        // For now, show placeholder
        setTimeout(() => {
            preview.innerHTML = `
                <div class="character-preview-content">
                    <h5><i class="fas fa-user me-2"></i>Preview do Personagem</h5>
                    <p class="text-muted">ID: ${charId}</p>
                    <p class="small">Detalhes do personagem serão carregados aqui...</p>
                </div>
            `;
        }, 500);
    }

    /**
     * Hide character preview
     */
    function hideCharacterPreview() {
        const preview = document.getElementById('character_preview');
        if (preview) {
            preview.style.display = 'none';
            preview.innerHTML = '';
        }
    }

    /**
     * Initialize form validations
     */
    function initFormValidations() {
        const sellForm = document.getElementById('sellForm');
        if (!sellForm) return;

        // Character selection validation
        const charSelect = document.getElementById('character_select');
        const priceInput = document.getElementById('price');
        const notesInput = document.getElementById('notes');

        if (charSelect) {
            charSelect.addEventListener('change', function() {
                if (this.value) {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                }
            });
        }

        // Price validation
        if (priceInput) {
            priceInput.addEventListener('blur', function() {
                const price = parseFloat(this.value);
                if (price > 0) {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                } else {
                    this.classList.remove('is-valid');
                    this.classList.add('is-invalid');
                }
            });
        }

        // Notes character limit
        if (notesInput) {
            const maxLength = 500;
            const counter = document.createElement('small');
            counter.className = 'form-text text-muted';
            notesInput.parentNode.appendChild(counter);

            function updateCounter() {
                const remaining = maxLength - notesInput.value.length;
                counter.textContent = `${notesInput.value.length}/${maxLength} caracteres`;
                
                if (remaining < 50) {
                    counter.classList.add('text-warning');
                } else {
                    counter.classList.remove('text-warning');
                }

                if (remaining < 0) {
                    counter.classList.add('text-danger');
                    notesInput.value = notesInput.value.substring(0, maxLength);
                } else {
                    counter.classList.remove('text-danger');
                }
            }

            notesInput.addEventListener('input', updateCounter);
            updateCounter();
        }

        // Form submission
        sellForm.addEventListener('submit', function(e) {
            let isValid = true;

            // Validate character selection
            if (charSelect && !charSelect.value) {
                charSelect.classList.add('is-invalid');
                isValid = false;
            }

            // Validate price
            if (priceInput && parseFloat(priceInput.value) <= 0) {
                priceInput.classList.add('is-invalid');
                isValid = false;
            }

            if (!isValid) {
                e.preventDefault();
                alert('Por favor, preencha todos os campos obrigatórios corretamente.');
            }
        });
    }

    /**
     * Format price display
     * @param {number} price - Price value
     * @param {string} currency - Currency code
     * @returns {string} Formatted price
     */
    function formatPrice(price, currency = 'BRL') {
        const symbols = {
            'BRL': 'R$',
            'USD': '$',
            'EUR': '€'
        };

        const symbol = symbols[currency] || currency;
        return `${symbol} ${parseFloat(price).toFixed(2)}`;
    }

    /**
     * Show loading overlay
     */
    function showLoading() {
        const overlay = document.createElement('div');
        overlay.id = 'marketplace-loading';
        overlay.innerHTML = `
            <div class="loading-spinner">
                <i class="fas fa-spinner fa-spin fa-3x"></i>
                <p class="mt-3">Processando...</p>
            </div>
        `;
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.7);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
        `;
        document.body.appendChild(overlay);
    }

    /**
     * Hide loading overlay
     */
    function hideLoading() {
        const overlay = document.getElementById('marketplace-loading');
        if (overlay) {
            overlay.remove();
        }
    }

    /**
     * Show notification
     * @param {string} message - Message to display
     * @param {string} type - Notification type (success, error, warning, info)
     */
    function showNotification(message, type = 'info') {
        // Check if Bootstrap toast is available
        if (typeof bootstrap !== 'undefined' && bootstrap.Toast) {
            // Use Bootstrap toast
            const toastHTML = `
                <div class="toast align-items-center text-white bg-${type === 'error' ? 'danger' : type} border-0" 
                     role="alert" aria-live="assertive" aria-atomic="true">
                    <div class="d-flex">
                        <div class="toast-body">${message}</div>
                        <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                                data-bs-dismiss="toast" aria-label="Close"></button>
                    </div>
                </div>
            `;
            
            const container = document.querySelector('.toast-container') || createToastContainer();
            container.insertAdjacentHTML('beforeend', toastHTML);
            
            const toastElement = container.lastElementChild;
            const toast = new bootstrap.Toast(toastElement);
            toast.show();
            
            // Remove element after hide
            toastElement.addEventListener('hidden.bs.toast', function() {
                toastElement.remove();
            });
        } else {
            // Fallback to alert
            alert(message);
        }
    }

    /**
     * Create toast container if it doesn't exist
     * @returns {HTMLElement} Toast container
     */
    function createToastContainer() {
        const container = document.createElement('div');
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(container);
        return container;
    }

    // Export functions to global scope if needed
    window.MarketplaceJS = {
        formatPrice,
        showLoading,
        hideLoading,
        showNotification
    };

})();

