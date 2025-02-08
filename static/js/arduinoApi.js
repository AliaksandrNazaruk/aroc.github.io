// arduinoApi.js

window.lightController = {
  module: null, // Переменная для хранения экземпляра класса ArduinoApi
  
  // Инициализация модуля
  init: function() {
    if (!this.module) {
      this.module = new ArduinoApi(); // Создаем экземпляр только один раз
    }
  },

  // Метод для отправки команды
  async sendCommand(command) {
    if (!this.module) {
      this.init(); // Если модуль не инициализирован, инициализируем его
    }
    return await this.module.sendCommand(command);
  },





  // Пример метода для отправки команды 'success'
  async sendSuccessCommand() {
    return await this.sendCommand(1);
  },
  // Пример метода для отправки команды 'stop'
  async sendStopLightCommand() {
    return await this.sendCommand(20);
  },

  // Пример метода для отправки команды 'failure'
  async sendFailureCommand() {
    return await this.sendCommand(2);
  },

  // Пример метода для отправки команды 'error'
  async sendErrorCommand() {
    return await this.sendCommand(4);
  },

  // Пример метода для отправки команды 'idle'
  async sendIdleCommand() {
    return await this.sendCommand(5);
  },

  // Пример метода для отправки команды 'manual'
  async sendManualCommand() {
    return await this.sendCommand(6);
  },

  // Пример метода для отправки команды 'running'
  async sendRunningCommand() {
    return await this.sendCommand(3);
  },
};

// Класс ArduinoApi, который теперь можно использовать
class ArduinoApi {
  constructor(baseURL = 'http://' + location.hostname + ':8000') {
    this.baseURL = baseURL;
  }

  // Метод для отправки команды на сервер
  async sendCommand(command) {
    const url = `${this.baseURL}/send`;
    const body = JSON.stringify({ command });

    try {
      const response = await fetch(url, {
        method: 'POST',
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
}

// Инициализируем модуль при загрузке
window.lightController.init();
