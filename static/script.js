class ProofreaderApp {
    constructor() {
        this.corrections = [];
        this.originalSentences = [];
        this.initializeElements();
        this.bindEvents();
    }

    initializeElements() {
        this.textInput = document.getElementById('text-input');
        this.proofreadBtn = document.getElementById('proofread-btn');
        this.clearBtn = document.getElementById('clear-btn');
        this.resultsSection = document.getElementById('results-section');
        this.correctionsContainer = document.getElementById('corrections-container');
        this.correctionsCount = document.getElementById('corrections-count');
        this.acceptAllBtn = document.getElementById('accept-all-btn');
        this.rejectAllBtn = document.getElementById('reject-all-btn');
        this.copyResultBtn = document.getElementById('copy-result-btn');
        this.finalText = document.getElementById('final-text');
        this.btnText = this.proofreadBtn.querySelector('.btn-text');
        this.loadingSpinner = this.proofreadBtn.querySelector('.loading-spinner');
    }

    bindEvents() {
        this.proofreadBtn.addEventListener('click', () => this.proofreadText());
        this.clearBtn.addEventListener('click', () => this.clearInput());
        // Hide sentence-diff actions for now
        this.acceptAllBtn.style.display = 'none';
        this.rejectAllBtn.style.display = 'none';
        this.copyResultBtn.addEventListener('click', () => this.copyFinalText());
        
        // Enable Enter+Ctrl to proofread
        this.textInput.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                e.preventDefault();
                this.proofreadText();
            }
        });
    }

    async proofreadText() {
        const text = this.textInput.value.trim();
        if (!text) {
            alert('Please enter some text to proofread.');
            return;
        }

        this.setLoading(true);
        
        try {
            const response = await fetch('/api/proofread', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: text,
                    llm_provider: 'mock'
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            this.showFinalResult(data.final_text, data.total_changes);
            
        } catch (error) {
            console.error('Error proofreading text:', error);
            alert('An error occurred while proofreading. Please try again.');
        } finally {
            this.setLoading(false);
        }
    }

    setLoading(isLoading) {
        this.proofreadBtn.disabled = isLoading;
        if (isLoading) {
            this.btnText.style.display = 'none';
            this.loadingSpinner.style.display = 'block';
        } else {
            this.btnText.style.display = 'block';
            this.loadingSpinner.style.display = 'none';
        }
    }

    showFinalResult(finalText, totalChanges) {
        // Hide diff UI
        this.correctionsContainer.style.display = 'none';
        this.acceptAllBtn.style.display = 'none';
        this.rejectAllBtn.style.display = 'none';

        // Set total change count and final text
        this.correctionsCount.textContent = `Total changes: ${totalChanges}`;
        this.finalText.textContent = finalText;

        // Show results
        this.resultsSection.style.display = 'block';
        this.resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    async copyFinalText() {
        const textToCopy = this.finalText.textContent;
        
        try {
            // Try modern clipboard API first
            if (navigator.clipboard && window.isSecureContext) {
                await navigator.clipboard.writeText(textToCopy);
                this.showCopySuccess();
                return;
            }
            
            // Fallback to legacy method
            this.copyTextFallback(textToCopy);
            this.showCopySuccess();
            
        } catch (err) {
            console.error('Failed to copy text:', err);
            // Try fallback method as last resort
            try {
                this.copyTextFallback(textToCopy);
                this.showCopySuccess();
            } catch (fallbackErr) {
                console.error('Fallback copy also failed:', fallbackErr);
                alert('Failed to copy text to clipboard. Please select and copy the text manually.');
            }
        }
    }

    copyTextFallback(text) {
        // Create a temporary textarea element
        const textArea = document.createElement('textarea');
        textArea.value = text;
        
        // Make it invisible but not display:none (which would prevent selection)
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        textArea.setAttribute('readonly', '');
        
        document.body.appendChild(textArea);
        
        // Select and copy the text
        textArea.select();
        textArea.setSelectionRange(0, 99999); // For mobile devices
        
        const successful = document.execCommand('copy');
        document.body.removeChild(textArea);
        
        if (!successful) {
            throw new Error('document.execCommand copy failed');
        }
    }

    showCopySuccess() {
        // Visual feedback
        const originalText = this.copyResultBtn.textContent;
        this.copyResultBtn.textContent = 'Copied!';
        this.copyResultBtn.style.background = '#10b981';
        
        setTimeout(() => {
            this.copyResultBtn.textContent = originalText;
            this.copyResultBtn.style.background = '';
        }, 2000);
    }

    clearInput() {
        this.textInput.value = '';
        this.resultsSection.style.display = 'none';
        this.corrections = [];
        this.originalSentences = [];
        this.textInput.focus();
    }
}

// Initialize the app when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new ProofreaderApp();
    
    // Add some sample text for demo purposes
    const sampleText = `This is a sample text with some common erors. The begining of this sentence has a mistake, and teh word "recieve" is spelled incorrectly. i think this tool will be very usefull for proofreading documents.`;
    
    // Uncomment the next line to load sample text on startup
    // document.getElementById('text-input').value = sampleText;
});