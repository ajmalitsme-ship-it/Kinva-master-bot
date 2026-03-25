// ============================================
// Kinva Master Bot - Editor JavaScript
// Author: @funnytamilan
// Version: 3.0
// ============================================

class KinvaEditor {
    constructor() {
        this.sessionId = null;
        this.fileType = null;
        this.originalImageUrl = null;
        this.currentEffects = [];
        this.socket = null;
        this.quality = '1080p';
        this.history = [];
        this.historyIndex = -1;
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.initSocket();
        this.loadSavedState();
    }
    
    bindEvents() {
        // File upload
        const fileInput = document.getElementById('fileInput');
        if (fileInput) {
            fileInput.addEventListener('change', (e) => this.uploadFile(e));
        }
        
        // Quality selector
        const qualityBtns = document.querySelectorAll('.quality-badge');
        qualityBtns.forEach(btn => {
            btn.addEventListener('click', () => this.setQuality(btn.dataset.quality));
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));
    }
    
    initSocket() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('Connected to server');
        });
        
        this.socket.on('edit_result', (data) => {
            console.log('Edit result:', data);
            if (data.result && data.result.preview_url) {
                this.updatePreview(data.result.preview_url);
            }
        });
        
        this.socket.on('error', (data) => {
            this.showNotification(data.message, 'error');
        });
    }
    
    async uploadFile(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        const formData = new FormData();
        formData.append('file', file);
        formData.append('user_id', this.getUserId());
        
        this.showLoading();
        
        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.sessionId = data.session_id;
                this.fileType = data.file_type;
                this.originalImageUrl = data.preview_url;
                this.updatePreview(data.preview_url);
                this.saveToHistory(data.preview_url);
                this.showNotification('File uploaded successfully!', 'success');
                document.getElementById('qualitySelector').style.display = 'block';
            } else {
                this.showNotification(data.error || 'Upload failed', 'error');
            }
        } catch (error) {
            console.error('Upload error:', error);
            this.showNotification('Upload failed. Please try again.', 'error');
        }
        
        this.hideLoading();
    }
    
    async applyFilter(filter) {
        if (!this.sessionId) {
            this.showNotification('Please upload a file first', 'error');
            return;
        }
        
        this.showLoading();
        
        try {
            const response = await fetch('/api/apply_filter', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    session_id: this.sessionId,
                    filter: filter
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.updatePreview(data.preview_url);
                this.saveToHistory(data.preview_url);
                this.showNotification(`Applied ${filter} filter!`, 'success');
            }
        } catch (error) {
            console.error('Filter error:', error);
            this.showNotification('Failed to apply filter', 'error');
        }
        
        this.hideLoading();
    }
    
    async applyEffect(effect) {
        if (!this.sessionId) {
            this.showNotification('Please upload a file first', 'error');
            return;
        }
        
        this.showLoading();
        
        try {
            const response = await fetch('/api/apply_filter', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    session_id: this.sessionId,
                    filter: effect
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.updatePreview(data.preview_url);
                this.saveToHistory(data.preview_url);
                this.showNotification(`Applied ${effect} effect!`, 'success');
            }
        } catch (error) {
            console.error('Effect error:', error);
            this.showNotification('Failed to apply effect', 'error');
        }
        
        this.hideLoading();
    }
    
    async adjust(type, value) {
        if (!this.sessionId || this.fileType !== 'image') return;
        
        const endpoint = {
            'brightness': '/api/adjust_brightness',
            'contrast': '/api/adjust_contrast',
            'saturation': '/api/adjust_saturation',
            'sharpness': '/api/adjust_sharpness'
        }[type];
        
        if (!endpoint) return;
        
        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    session_id: this.sessionId,
                    factor: parseFloat(value)
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.updatePreview(data.preview_url);
            }
        } catch (error) {
            console.error('Adjust error:', error);
        }
    }
    
    async removeBackground() {
        if (!this.sessionId || this.fileType !== 'image') {
            this.showNotification('Please upload an image first', 'error');
            return;
        }
        
        this.showLoading();
        
        try {
            const response = await fetch('/api/remove_background', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({session_id: this.sessionId})
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.updatePreview(data.preview_url);
                this.saveToHistory(data.preview_url);
                this.showNotification('Background removed!', 'success');
            }
        } catch (error) {
            console.error('Background removal error:', error);
            this.showNotification('Failed to remove background', 'error');
        }
        
        this.hideLoading();
    }
    
    async resizeImage() {
        const width = prompt('Enter width (pixels):', '800');
        const height = prompt('Enter height (pixels):', '600');
        
        if (!width || !height) return;
        
        this.showLoading();
        
        try {
            const response = await fetch('/api/resize', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    session_id: this.sessionId,
                    width: parseInt(width),
                    height: parseInt(height)
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.updatePreview(data.preview_url);
                this.saveToHistory(data.preview_url);
                this.showNotification('Image resized!', 'success');
            }
        } catch (error) {
            console.error('Resize error:', error);
            this.showNotification('Failed to resize', 'error');
        }
        
        this.hideLoading();
    }
    
    async rotateImage(angle = 90) {
        if (!this.sessionId) return;
        
        this.showLoading();
        
        try {
            const response = await fetch('/api/rotate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    session_id: this.sessionId,
                    angle: angle
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.updatePreview(data.preview_url);
                this.saveToHistory(data.preview_url);
                this.showNotification('Image rotated!', 'success');
            }
        } catch (error) {
            console.error('Rotate error:', error);
        }
        
        this.hideLoading();
    }
    
    async flipImage(direction) {
        if (!this.sessionId) return;
        
        this.showLoading();
        
        try {
            const response = await fetch('/api/flip', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    session_id: this.sessionId,
                    direction: direction
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.updatePreview(data.preview_url);
                this.saveToHistory(data.preview_url);
                this.showNotification(`Flipped ${direction}!`, 'success');
            }
        } catch (error) {
            console.error('Flip error:', error);
        }
        
        this.hideLoading();
    }
    
    async addText() {
        const text = prompt('Enter text:', 'Kinva Master');
        if (!text) return;
        
        this.showLoading();
        
        try {
            const response = await fetch('/api/add_text', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    session_id: this.sessionId,
                    text: text,
                    position: 'center',
                    font_size: 40
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.updatePreview(data.preview_url);
                this.saveToHistory(data.preview_url);
                this.showNotification('Text added!', 'success');
            }
        } catch (error) {
            console.error('Add text error:', error);
        }
        
        this.hideLoading();
    }
    
    async resetImage() {
        if (!this.sessionId) return;
        
        this.showLoading();
        
        try {
            const response = await fetch('/api/reset', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({session_id: this.sessionId})
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.updatePreview(data.preview_url);
                this.saveToHistory(data.preview_url);
                this.showNotification('Reset to original!', 'success');
            }
        } catch (error) {
            console.error('Reset error:', error);
        }
        
        this.hideLoading();
    }
    
    async setQuality(quality) {
        this.quality = quality;
        this.showNotification(`Quality set to ${quality}`, 'success');
    }
    
    async exportFile() {
        if (!this.sessionId) {
            this.showNotification('No file to export', 'error');
            return;
        }
        
        this.showLoading();
        
        try {
            const response = await fetch('/api/export', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    session_id: this.sessionId,
                    quality: this.quality
                })
            });
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `kinva_export_${Date.now()}.${this.fileType === 'image' ? 'jpg' : 'mp4'}`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                this.showNotification('Export completed!', 'success');
            } else {
                const error = await response.json();
                this.showNotification(error.error || 'Export failed', 'error');
            }
        } catch (error) {
            console.error('Export error:', error);
            this.showNotification('Export failed', 'error');
        }
        
        this.hideLoading();
    }
    
    updatePreview(url) {
        const img = document.getElementById('previewImage');
        const video = document.getElementById('previewVideo');
        const uploadArea = document.querySelector('.upload-area');
        
        if (uploadArea) uploadArea.style.display = 'none';
        
        if (this.fileType === 'image') {
            img.src = url + '?t=' + Date.now();
            img.style.display = 'block';
            if (video) video.style.display = 'none';
        } else {
            video.src = url + '?t=' + Date.now();
            video.style.display = 'block';
            if (img) img.style.display = 'none';
        }
    }
    
    saveToHistory(url) {
        // Remove future history if we're not at the end
        if (this.historyIndex < this.history.length - 1) {
            this.history = this.history.slice(0, this.historyIndex + 1);
        }
        
        this.history.push(url);
        this.historyIndex = this.history.length - 1;
        
        // Keep only last 50 states
        if (this.history.length > 50) {
            this.history.shift();
            this.historyIndex--;
        }
    }
    
    undo() {
        if (this.historyIndex > 0) {
            this.historyIndex--;
            this.updatePreview(this.history[this.historyIndex]);
            this.showNotification('Undo', 'info');
        } else {
            this.showNotification('Nothing to undo', 'warning');
        }
    }
    
    redo() {
        if (this.historyIndex < this.history.length - 1) {
            this.historyIndex++;
            this.updatePreview(this.history[this.historyIndex]);
            this.showNotification('Redo', 'info');
        } else {
            this.showNotification('Nothing to redo', 'warning');
        }
    }
    
    handleKeyboard(e) {
        if (e.ctrlKey || e.metaKey) {
            switch(e.key) {
                case 'z':
                    e.preventDefault();
                    this.undo();
                    break;
                case 'y':
                    e.preventDefault();
                    this.redo();
                    break;
                case 's':
                    e.preventDefault();
                    this.exportFile();
                    break;
                case 'u':
                    e.preventDefault();
                    this.uploadFile();
                    break;
            }
        }
    }
    
    showNotification(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast-notification toast-${type}`;
        toast.innerHTML = `
            <i class="fas ${type === 'success' ? 'fa-check-circle' : 
                          type === 'error' ? 'fa-exclamation-circle' : 
                          type === 'warning' ? 'fa-exclamation-triangle' : 'fa-info-circle'}"></i>
            <span>${message}</span>
        `;
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
    
    showLoading() {
        const previewArea = document.querySelector('.preview-area');
        if (!previewArea) return;
        
        const loader = document.createElement('div');
        loader.className = 'loading-overlay';
        loader.innerHTML = '<div class="spinner"></div>';
        previewArea.style.position = 'relative';
        previewArea.appendChild(loader);
    }
    
    hideLoading() {
        const loader = document.querySelector('.loading-overlay');
        if (loader) loader.remove();
    }
    
    getUserId() {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get('user') || localStorage.getItem('userId') || 'anonymous';
    }
    
    loadSavedState() {
        const savedSession = localStorage.getItem('kinva_session');
        if (savedSession) {
            try {
                const data = JSON.parse(savedSession);
                if (data.sessionId && data.fileType) {
                    this.sessionId = data.sessionId;
                    this.fileType = data.fileType;
                    this.updatePreview(data.previewUrl);
                }
            } catch(e) {}
        }
    }
    
    saveState() {
        if (this.sessionId) {
            localStorage.setItem('kinva_session', JSON.stringify({
                sessionId: this.sessionId,
                fileType: this.fileType,
                previewUrl: document.getElementById('previewImage').src
            }));
        }
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    window.editor = new KinvaEditor();
});
