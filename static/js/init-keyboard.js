// Initialize keyboard control
window.addEventListener('load', function() {
    // Create and initialize keyboard control instance
    const keyboardControl = new window.KeyboardControl();
    keyboardControl.mounted();
    
    // Store the instance for cleanup
    window.keyboardControlInstance = keyboardControl;
    
    // Debug log
    console.log('Keyboard control initialized');
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (window.keyboardControlInstance) {
        window.keyboardControlInstance.beforeDestroy();
    }
}); 