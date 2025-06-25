function KeyboardControl() {
    this.activeKey = null;
    this.keyMap = this.loadKeyMap();
    this.isKeyDown = false;
    this.interval = null;
    this.lastAction = null;

    // Listen for key binding updates from the config iframe
    window.addEventListener('message', (event) => {
        if (event.data.type === 'keyBindingsUpdated') {
            this.keyMap = this.getKeyActionMap(event.data.keyMap);
        }
    });
}

KeyboardControl.prototype = {
    loadKeyMap: function() {
        // Load saved bindings or use defaults
        const savedBindings = localStorage.getItem('keyboardBindings');
        const keyBindings = savedBindings ? JSON.parse(savedBindings) : {
            'coord-x-increase': 'I',
            'coord-x-decrease': 'K',
            'coord-y-increase': 'J',
            'coord-y-decrease': 'L',
            'coord-z-increase': 'U',
            'coord-z-decrease': 'O',
            'coord-rx-increase': 'Y',
            'coord-rx-decrease': 'H',
            'coord-ry-increase': 'T',
            'coord-ry-decrease': 'G',
            'coord-rz-increase': 'B',
            'coord-rz-decrease': 'N',
            'lift-z-increase': 'W',
            'lift-z-decrease': 'S',
            'reference': 'R',
            'fault-reset': 'F'
        };
        
        // Convert to key -> action map for faster lookups
        return this.getKeyActionMap(keyBindings);
    },

    getKeyActionMap: function(actionKeyMap) {
        // Convert action->key map to key->action map
        const keyActionMap = {};
        for (let action in actionKeyMap) {
            const key = actionKeyMap[action];
            keyActionMap[key.toLowerCase()] = action;
        }
        return keyActionMap;
    },

    handleKeyDown: function(event) {
        // Get action for this key
        const action = this.keyMap[event.key.toLowerCase()];
        
        // If this key is mapped, prevent default behavior
        if (action) {
            event.preventDefault();
        }

        // Only allow one key at a time for safety
        if (this.activeKey) {
            return;
        }

        if (action) {
            this.activeKey = event.key;
            this.isKeyDown = true;
            this.lastAction = action;
            this.triggerAction(action);
        }
    },

    handleKeyUp: function(event) {
        if (this.activeKey === event.key) {
            this.isKeyDown = false;
            this.stopAction();
            this.activeKey = null;
            this.lastAction = null;
        }
    },

    triggerAction: function(action) {
        switch(action) {
            // Lift controls
            case 'lift-z-increase':
            case 'lift-z-decrease':
                this.startMovement(action);
                break;
            case 'reference':
                this.handleReference();
                break;
            case 'fault-reset':
                this.handleReset();
                break;

            // Coordinate controls
            case 'coord-x-increase':
            case 'coord-x-decrease':
            case 'coord-y-increase':
            case 'coord-y-decrease':
            case 'coord-z-increase':
            case 'coord-z-decrease':
            case 'coord-rx-increase':
            case 'coord-rx-decrease':
            case 'coord-ry-increase':
            case 'coord-ry-decrease':
            case 'coord-rz-increase':
            case 'coord-rz-decrease':
                this.startCoordinateMovement(action);
                break;
        }
    },

    startMovement: function(action) {
        const t = this;
        const speed = window.CommandsRobotSocket.model.robot.state.remote.speedPercent * 10000;
        const direction = action === 'lift-z-increase' ? 1 : -1;
        
        this.interval = setInterval(async function() {
            if (t.isKeyDown) {
                try {
                    await window.igusController.moveToPosition(0, speed * direction, speed);
                } catch (error) {
                    console.error('Movement error:', error);
                    t.stopAction();
                }
            }
        }, 200);
    },

    startCoordinateMovement: function(action) {
        const t = this;
        const speed = window.CommandsRobotSocket.model.robot.state.remote.speedPercent * 10000;
        const [axis, direction] = action.split('-').slice(1);
        const multiplier = direction === 'increase' ? 1 : -1;
        
        this.interval = setInterval(async function() {
            if (t.isKeyDown) {
                try {
                    // Get current position
                    const currentPos = await window.igusController.getPosition();
                    const newPos = { ...currentPos };
                    
                    // Update the appropriate axis
                    switch(axis) {
                        case 'x': newPos.x += 1 * multiplier; break;
                        case 'y': newPos.y += 1 * multiplier; break;
                        case 'z': newPos.z += 1 * multiplier; break;
                        case 'rx': newPos.rx += 1 * multiplier; break;
                        case 'ry': newPos.ry += 1 * multiplier; break;
                        case 'rz': newPos.rz += 1 * multiplier; break;
                    }
                    
                    await window.igusController.moveToPosition(newPos, speed, speed);
                } catch (error) {
                    console.error('Coordinate movement error:', error);
                    t.stopAction();
                }
            }
        }, 200);
    },

    stopAction: function() {
        if (this.interval) {
            clearInterval(this.interval);
            this.interval = null;
        }
        
        const speed = window.CommandsRobotSocket.model.robot.state.remote.speedPercent * 10000;
        try {
            window.igusController.sendCommand({
                command: "shutdown",
                position: 0,
                velocity: speed,
                acceleration: speed
            });
        } catch (error) {
            console.error('Shutdown error:', error);
        }
    },

    handleReference: async function() {
        try {
            await window.igusController.homing();
        } catch (error) {
            console.error("Reference error:", error);
        }
    },

    handleReset: async function() {
        try {
            await window.igusController.sendCommand({ command: "fault_reset" });
            await window.igusController.sendCommand({ command: "shutdown" });
        } catch (error) {
            console.error("Reset error:", error);
        }
    },

    mounted: function() {
        window.addEventListener('keydown', this.handleKeyDown.bind(this));
        window.addEventListener('keyup', this.handleKeyUp.bind(this));
    },

    beforeDestroy: function() {
        window.removeEventListener('keydown', this.handleKeyDown.bind(this));
        window.removeEventListener('keyup', this.handleKeyUp.bind(this));
        this.stopAction();
    }
};

// ... existing code ...
window.KeyboardControl = KeyboardControl;