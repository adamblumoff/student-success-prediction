/**
 * Secure DOM Manipulation Utilities
 * Provides XSS-safe methods for DOM manipulation and content rendering
 */

class SecureDOM {
    /**
     * Safely set text content (XSS-safe alternative to innerHTML)
     */
    static setText(element, text) {
        if (element) {
            element.textContent = text || '';
        }
    }

    /**
     * Safely set HTML content with sanitization
     */
    static setHTML(element, htmlContent) {
        if (!element) return;
        
        // Create a temporary container for sanitization
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = htmlContent || '';
        
        // Sanitize the content by removing dangerous elements and attributes
        const sanitized = this.sanitizeHTML(tempDiv);
        
        // Clear and append sanitized content
        element.innerHTML = '';
        element.appendChild(sanitized);
    }

    /**
     * Create a safe HTML template with escaped content
     */
    static createSafeHTML(template, data = {}) {
        let safeHTML = template;
        
        // Replace template variables with escaped content
        Object.keys(data).forEach(key => {
            const value = data[key];
            const placeholder = new RegExp(`{{${key}}}`, 'g');
            const escapedValue = this.escapeHTML(String(value));
            safeHTML = safeHTML.replace(placeholder, escapedValue);
        });
        
        return safeHTML;
    }

    /**
     * Escape HTML special characters to prevent XSS
     */
    static escapeHTML(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Sanitize HTML content by removing dangerous elements and attributes
     */
    static sanitizeHTML(element) {
        const allowedTags = [
            'div', 'span', 'p', 'br', 'strong', 'em', 'b', 'i', 'u',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'ul', 'ol', 'li',
            'table', 'thead', 'tbody', 'tr', 'td', 'th',
            'a', 'img'
        ];
        
        const allowedAttributes = {
            'a': ['href', 'title'],
            'img': ['src', 'alt', 'width', 'height'],
            '*': ['class', 'id', 'data-*']
        };
        
        const clone = element.cloneNode(true);
        this.sanitizeElement(clone, allowedTags, allowedAttributes);
        return clone;
    }

    /**
     * Recursively sanitize an element and its children
     */
    static sanitizeElement(element, allowedTags, allowedAttributes) {
        // Remove dangerous elements
        const dangerousTags = ['script', 'object', 'embed', 'form', 'input', 'button'];
        dangerousTags.forEach(tag => {
            const elements = element.querySelectorAll(tag);
            elements.forEach(el => el.remove());
        });

        // Process all elements
        const allElements = element.querySelectorAll('*');
        allElements.forEach(el => {
            const tagName = el.tagName.toLowerCase();
            
            // Remove disallowed tags
            if (!allowedTags.includes(tagName)) {
                // Replace with span to preserve content
                const span = document.createElement('span');
                span.innerHTML = el.innerHTML;
                el.parentNode.replaceChild(span, el);
                return;
            }
            
            // Sanitize attributes
            Array.from(el.attributes).forEach(attr => {
                const attrName = attr.name.toLowerCase();
                const attrValue = attr.value;
                
                // Remove event handlers
                if (attrName.startsWith('on')) {
                    el.removeAttribute(attr.name);
                    return;
                }
                
                // Remove javascript: URLs
                if (attrValue && attrValue.toLowerCase().includes('javascript:')) {
                    el.removeAttribute(attr.name);
                    return;
                }
                
                // Check allowed attributes
                const tagAllowed = allowedAttributes[tagName] || [];
                const globalAllowed = allowedAttributes['*'] || [];
                const isDataAttribute = attrName.startsWith('data-');
                
                if (!tagAllowed.includes(attrName) && 
                    !globalAllowed.includes(attrName) && 
                    !isDataAttribute) {
                    el.removeAttribute(attr.name);
                }
            });
        });
    }

    /**
     * Safely create a DOM element with attributes
     */
    static createElement(tagName, attributes = {}, textContent = '') {
        const element = document.createElement(tagName);
        
        // Set safe attributes
        Object.keys(attributes).forEach(key => {
            const value = attributes[key];
            
            // Skip dangerous attributes
            if (key.startsWith('on') || key === 'src' && String(value).includes('javascript:')) {
                console.warn(`Blocked potentially dangerous attribute: ${key}="${value}"`);
                return;
            }
            
            element.setAttribute(key, String(value));
        });
        
        // Set safe text content
        if (textContent) {
            element.textContent = String(textContent);
        }
        
        return element;
    }

    /**
     * Safely append multiple child elements
     */
    static appendChildren(parent, children) {
        if (!parent || !Array.isArray(children)) return;
        
        children.forEach(child => {
            if (child instanceof Node) {
                parent.appendChild(child);
            }
        });
    }

    /**
     * Create safe modal content
     */
    static createModalContent(title, content, isHTML = false) {
        const container = document.createElement('div');
        container.className = 'modal-content-safe';
        
        // Create title element
        const titleEl = this.createElement('h3', { class: 'modal-title' }, title);
        
        // Create content element
        const contentEl = document.createElement('div');
        contentEl.className = 'modal-body';
        
        if (isHTML) {
            this.setHTML(contentEl, content);
        } else {
            this.setText(contentEl, content);
        }
        
        this.appendChildren(container, [titleEl, contentEl]);
        return container;
    }

    /**
     * Safe event listener attachment with cleanup tracking
     */
    static addEventListener(element, event, handler, options = false) {
        if (!element || typeof handler !== 'function') return null;
        
        // Create wrapper for cleanup tracking
        const wrappedHandler = function(e) {
            try {
                return handler.call(this, e);
            } catch (error) {
                console.error('Event handler error:', error);
            }
        };
        
        element.addEventListener(event, wrappedHandler, options);
        
        // Return cleanup function
        return () => element.removeEventListener(event, wrappedHandler, options);
    }

    /**
     * Safe form data extraction with validation
     */
    static getFormData(form) {
        if (!(form instanceof HTMLFormElement)) return {};
        
        const formData = new FormData(form);
        const data = {};
        
        for (let [key, value] of formData.entries()) {
            // Sanitize form field names and values
            const safeKey = key.replace(/[^a-zA-Z0-9_-]/g, '');
            const safeValue = this.escapeHTML(String(value));
            
            if (safeKey) {
                data[safeKey] = safeValue;
            }
        }
        
        return data;
    }

    /**
     * Safe URL construction for API calls
     */
    static buildSafeURL(baseURL, params = {}) {
        try {
            const url = new URL(baseURL);
            
            Object.keys(params).forEach(key => {
                const value = params[key];
                if (value !== null && value !== undefined) {
                    url.searchParams.set(key, String(value));
                }
            });
            
            return url.toString();
        } catch (error) {
            console.error('Invalid URL construction:', error);
            return baseURL;
        }
    }

    /**
     * Safe JSON parsing with error handling
     */
    static safeJSONParse(jsonString, defaultValue = null) {
        try {
            return JSON.parse(jsonString);
        } catch (error) {
            console.warn('JSON parse error:', error);
            return defaultValue;
        }
    }

    /**
     * Debounced event handler for performance
     */
    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * Cleanup utility for removing event listeners and preventing memory leaks
     */
    static createCleanupManager() {
        const cleanupFunctions = [];
        
        return {
            add: (cleanupFn) => {
                if (typeof cleanupFn === 'function') {
                    cleanupFunctions.push(cleanupFn);
                }
            },
            cleanup: () => {
                cleanupFunctions.forEach(fn => {
                    try {
                        fn();
                    } catch (error) {
                        console.error('Cleanup error:', error);
                    }
                });
                cleanupFunctions.length = 0;
            }
        };
    }
}

// Make SecureDOM available globally
window.SecureDOM = SecureDOM;