/**
 * Base Component Class
 * Provides common functionality for UI components
 */

class Component {
  constructor(selector, appState) {
    this.element = document.querySelector(selector);
    this.appState = appState;
    this.boundMethods = new Set();
    
    if (!this.element) {
      console.warn(`Component element not found: ${selector}`);
      return;
    }
    
    this.init();
  }

  init() {
    // Override in subclasses
  }

  bindEvent(element, event, handler) {
    const boundHandler = handler.bind(this);
    element.addEventListener(event, boundHandler);
    this.boundMethods.add(() => element.removeEventListener(event, boundHandler));
    return boundHandler;
  }

  destroy() {
    this.boundMethods.forEach(cleanup => cleanup());
    this.boundMethods.clear();
  }

  show() {
    if (this.element) this.element.classList.remove('hidden');
  }

  hide() {
    if (this.element) this.element.classList.add('hidden');
  }

  setContent(content) {
    if (this.element) this.element.innerHTML = content;
  }
}

// Make Component available globally
window.Component = Component;