// arduinoApi.js

window.IgusController = {
  module: null, // Переменная для хранения экземпляра класса IgusApi

  // Инициализация модуля
  init: function() {
      if (!this.module) {
          this.module = new IgusApi(); // Создаем экземпляр только один раз
      }
  },

  // Метод для отправки команды
  async sendCommand(command, value = null, velocity = null) {
      if (!this.module) {
          this.init(); // Если модуль не инициализирован, инициализируем его
      }
      return await this.module.sendCommand(command, value, velocity);
  },

  // Метод для проверки состояния Reference
  async checkReferenceStatus() {
      if (!this.module) {
          this.init(); // Инициализация, если модуль не был инициализирован
      }
      return await this.module.checkReferenceStatus();
  },
  // Метод для проверки состояния Reference
  async checkActualPosition() {
    if (!this.module) {
        this.init(); // Инициализация, если модуль не был инициализирован
    }
    return await this.module.checkActualPosition();
  },
  async sendJogCommand(direction,velocity) {
    let result = "";
    if (direction =="lift-z-decrease")
        result ="JOG_DOWN"
    else if (direction =="lift-z-increase")
        result ="JOG_UP"
    else
        result ="STOP"
    return await this.sendCommand(result,null,velocity);
  },

  // Пример метода для отправки команды 'failure'
  async sendResetCommand() {
      return await this.sendCommand('RESET');
  },

  async sendWarnResetCommand() {
    return await this.sendCommand('WARN_RESET');
  },
  // Пример метода для отправки команды 'error'
  async sendReferenceCommand() {
      return await this.sendCommand('REFERENCE');
  },

  // Пример метода для отправки команды 'idle'
  async sendABSCommand(value,velocity) {
      return await this.sendCommand('ABS', value, velocity);
  },
};
const baseURL = 'http://' + location.hostname + ':8020';
const posturl = baseURL+'/api/igus';
// Класс IgusApi
class IgusApi {
    async checkActualPosition() {
      try {
          const response = await fetch(posturl + '/get-actual-position');
          
          // Ensure that the server returns a successful response
          if (response.ok) {
              const data = await response.json();
              // Now checking the "Position" field as it is returned by the server
              return data["Position"];  // Assuming that the response contains a "Position" field
          } else {
              const errorData = await response.json();
              return false;
          }
      } catch (error) {
          return false;
      }
  }

  // Метод для проверки состояния Reference
  async checkReferenceStatus() {
    try {
        const response = await fetch(posturl + '/get-reference-status');
        const data = await response.json();

        if (response.ok) {
            return data.isActive; // Возвращаем состояние активности
        } else {
            return false;
        }
    } catch (error) {
        return false;
    }
}
  // Метод для отправки команды на сервер
  async sendCommand(command, value = null, velocity=null) {
      const body = JSON.stringify({ command, value, velocity }); // Добавляем value в тело запроса

      try {
          const response = await fetch(posturl+"/send_command", {
              method: 'POST',
              body: body,
          });

          const data = await response.json();

          if (!response.ok) {
              throw new Error(data.error || 'Unknown error');
          }
          return true
      } catch (error) {
          return { error: error.message };
      }
  }
}

// Инициализируем модуль при загрузке
window.IgusController.init();
