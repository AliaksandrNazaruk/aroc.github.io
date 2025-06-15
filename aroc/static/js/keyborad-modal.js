window.KeyboardSettingsModal = {
    template: `
        <div class="keyboard-settings-modal" v-if="visible">
            <div class="modal-overlay" @click="close"></div>
            <div class="modal-container">
                <div class="modal-header">
                    <h2>Keyboard Settings</h2>
                    <button class="close-button" @click="close">&times;</button>
                </div>
                <div class="modal-content">
                    <iframe src="./static/js/keyboard-config.html" frameborder="0"></iframe>
                </div>
            </div>
        </div>
    `,
    
    data() {
        return {
            visible: false
        }
    },
    
    methods: {
        show() {
            this.visible = true;
        },
        
        close() {
            this.visible = false;
        }
    },
    
    mounted() {
        // Add modal styles
        const style = document.createElement('style');
        style.textContent = `
            .keyboard-settings-modal {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                z-index: 1000;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            
            .modal-overlay {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0, 0, 0, 0.5);
            }
            
            .modal-container {
                position: relative;
                width: 90%;
                max-width: 800px;
                max-height: 90vh;
                background-color: #fff;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.33);
                display: flex;
                flex-direction: column;
                z-index: 1001;
            }
            
            .modal-header {
                padding: 15px 20px;
                border-bottom: 1px solid #eee;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .modal-header h2 {
                margin: 0;
                font-size: 1.5em;
                color: #333;
            }
            
            .close-button {
                background: none;
                border: none;
                font-size: 1.5em;
                cursor: pointer;
                padding: 0 5px;
                color: #666;
            }
            
            .close-button:hover {
                color: #333;
            }
            
            .modal-content {
                flex: 1;
                padding: 20px;
                overflow: auto;
            }
            
            .modal-content iframe {
                width: 100%;
                height: 100%;
                min-height: 500px;
                border: none;
            }
        `;
        document.head.appendChild(style);
    }
}; 