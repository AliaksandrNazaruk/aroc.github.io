
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
          let msg = 'Unknown error';
          let details = null;

          if (typeof data.detail === 'string') {
            msg = data.detail;
          } else if (data.detail && typeof data.detail === 'object') {
            msg = data.detail.message || msg;
            details = data.detail.states;
          } else if (data.error) {
            msg = data.error;
          }

          showError(msg, details);

          throw new Error(msg);
        }

        // Если команда успешно отправлена
        return {
          status: data.status,
          result: data.result,
        };
      } catch (error) {
        console.error('Ошибка при отправке команды:', error);

        showError(error.message);

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
          let msg = 'Unknown error';

          if (typeof data.detail === 'string') {
            msg = data.detail;
          } else if (data.detail && typeof data.detail === 'object') {
            msg = data.detail.message || msg;
          }

          throw new Error(msg);
        }
  
        // Если команда успешно отправлена
        return {
          status: data.result
        };
      } catch (error) {
        console.error('Ошибка при отправке команды:', error);
        showError(error.message);
        return { error: error.message };
      }
    }
  }
  // Инициализируем модуль при загрузке
  window.robotServer.init();

  function showError(message, details = null) {
    let modal = document.getElementById('error-modal');
    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'error-modal';
      modal.style.position = 'fixed';
      modal.style.top = '0';
      modal.style.left = '0';
      modal.style.width = '100%';
      modal.style.height = '100%';
      modal.style.display = 'flex';
      modal.style.alignItems = 'center';
      modal.style.justifyContent = 'center';
      modal.style.backgroundColor = 'rgba(0,0,0,0.5)';
      const box = document.createElement('div');
      box.style.background = '#fff';
      box.style.padding = '20px';
      box.style.borderRadius = '8px';
      box.style.minWidth = '200px';
      box.style.textAlign = 'center';
      const text = document.createElement('div');
      text.id = 'error-modal-text';
      text.style.marginBottom = '10px';
      box.appendChild(text);
      const detailsEl = document.createElement('pre');
      detailsEl.id = 'error-modal-details';
      detailsEl.style.marginBottom = '10px';
      detailsEl.style.textAlign = 'left';
      detailsEl.style.display = 'none';
      box.appendChild(detailsEl);
      const btn = document.createElement('button');
      btn.textContent = 'OK';
      btn.onclick = () => modal.remove();
      box.appendChild(btn);
      modal.appendChild(box);
      document.body.appendChild(modal);
    }
    modal.querySelector('#error-modal-text').textContent = message;
    const detailsEl = modal.querySelector('#error-modal-details');
    if (detailsEl) {
      if (details) {
        detailsEl.style.display = 'block';
        detailsEl.textContent = JSON.stringify(details, null, 2);
      } else {
        detailsEl.style.display = 'none';
        detailsEl.textContent = '';
      }
    }
  }


