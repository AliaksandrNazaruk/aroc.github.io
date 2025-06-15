
window.robotServer = {
    module: null, // Переменная для хранения экземпляра класса ArduinoApi
    
    // Инициализация модуля
    init: function() {
      if (!this.module) {
        this.module = new robotServerApi(); // Создаем экземпляр только один раз
      }
    },
    async xarm_command(command) {
      return await this.module.xarmSendCommand(command);
    },
    async robot_script(data) {
      return await this.module.sendCommand(data);
    },
    // Пример метода для отправки команды 'success'
    async getPosition(name) {
      return await this.module.sendCommand('/xarm_positions',name);
    },
  };

  class robotServerApi {
    constructor(baseURL = 'http://' + location.hostname + ':8000') {
      this.baseURL = baseURL;
    }
  
    // Метод для отправки команды на сервер
    async sendCommand(data) {
      const url = `${this.baseURL}/run_script`;
      const body = JSON.stringify(data);
  
      try {
        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: body,
        });
  
        const data = await response.json();
  
        if (!response.ok) {
          throw new Error(data.error || 'Unknown error');
        }
  
        // Если команда успешно отправлена
        return {
          status: data.status,
          command: data.command,
        };
      } catch (error) {
        console.error('Ошибка при отправке команды:', error);
        return { error: error.message };
      }
    }
    // Метод для отправки команды на сервер
    async xarmSendCommand(command) {
      const url = `${this.baseURL}/api/xarm/command`;
      const body = JSON.stringify({ command });
  
      try {
        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: body,
        });
  
        const data = await response.json();
  
        if (!response.ok) {
          throw new Error(data.detail || 'Unknown error');
        }
  
        // Если команда успешно отправлена
        return {
          status: data.result
        };
      } catch (error) {
        console.error('Ошибка при отправке команды:', error);
        return { error: error.message };
      }
    }
  }
  // Инициализируем модуль при загрузке
  window.robotServer.init();
  