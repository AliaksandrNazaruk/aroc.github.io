
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
//   // В sendCommand и xarmSendCommand
// console.log('Response:', data);
// console.log('Details:', data.detail && data.detail.states);

// // Перед showError
// showError(msg, details);
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
//   // В sendCommand и xarmSendCommand
// console.log('Response:', data);
// console.log('Details:', data.detail && data.detail.states);

// // Перед showError
// showError(msg, details);
        // showError(error.message);

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
        // showError(error.message);
        return { error: error.message };
      }
    }
  }
  // Инициализируем модуль при загрузке
window.robotServer.init();
function formatDeviceState(devices) {
  if (!devices || typeof devices !== 'object') return '';
  let html = '';
  for (const [dev, state] of Object.entries(devices)) {
    html += `
      <div style="border-bottom:1px solid #ececec;text-align:left;">
        <div style="font-weight:bold;color:#2563eb;font-size:18px;letter-spacing:1px;">${dev.toUpperCase()}</div>
        <div style="margin-top:1px;">${formatDetails(state)}</div>
      </div>
    `;
  }
  return html;
}

function formatDetails(details) {
  if (!details) return '';
  if (typeof details === 'string') return details;

  // Если details — это ошибка с traceback
  if (typeof details === 'object' && details.traceback) {
    let html = '';
    if (details.type) html += `<span style="color:#8b5cf6"><b>${details.type}</b></span>: `;
    if (details.msg) html += `<span style="color:#c026d3">${details.msg}</span><br>`;
    if (details.traceback) {
      html += `<pre style="background:#f3f4f6;color:#222;border-radius:6px;margin-top:1px;white-space:pre-wrap;">${details.traceback.join('')}</pre>`;
    }
    return html;
  }

  // Если details — просто объект (например, стейт устройства)
  if (typeof details === 'object' && !Array.isArray(details)) {
    let html = '<ul style="padding-left:16px;margin:0;">';
    for (const [key, val] of Object.entries(details)) {
      if (typeof val === 'object') {
        html += `<li><b>${key}:</b><div style="margin-left:10px;">${formatDetails(val)}</div></li>`;
      } else {
        html += `<li><b>${key}:</b> <span style="color:#64748b;">${val}</span></li>`;
      }
    }
    html += '</ul>';
    return html;
  }

  // fallback
  return `<pre>${JSON.stringify(details, null, 2)}</pre>`;
}


function showError(message, details = null) {


  let modal = document.getElementById('error-modal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'error-modal';
    modal.style.position = 'fixed';
    modal.style.top = '0';
    modal.style.left = '0';
    modal.style.zIndex = '2000';
    modal.style.width = '100%';
    modal.style.height = '100%';
    modal.style.display = 'flex';
    modal.style.alignItems = 'center';
    modal.style.justifyContent = 'center';
    modal.style.backgroundColor = 'rgba(0,0,0,0.5)';

    const box = document.createElement('div');
    box.style.background = '#fff';
    box.style.padding = '32px 36px';
    box.style.borderRadius = '18px';
    box.style.width = '600px';
    box.style.maxWidth = '90vw';
    box.style.boxShadow = '0 8px 32px rgba(0,0,0,0.20)';
    box.style.textAlign = 'center';
    box.style.display = 'flex';
    box.style.flexDirection = 'column';
    box.style.alignItems = 'center';

    const text = document.createElement('div');
    text.id = 'error-modal-text';
    // text.style.marginBottom = '18px';
    text.style.fontSize = '20px';
    text.style.color = '#22223b';
    box.appendChild(text);

    // Кнопка "Показать детали"
    const detailsToggle = document.createElement('button');
    detailsToggle.textContent = 'Show details';
    detailsToggle.style.padding = '20px';
    detailsToggle.style.fontSize = '15px';
    detailsToggle.style.display = 'none';
    // detailsToggle.style.marginBottom = '10px';
    detailsToggle.style.background = 'none';
    detailsToggle.style.border = 'none';
    detailsToggle.style.color = '#2563eb';
    detailsToggle.style.cursor = 'pointer';
    detailsToggle.style.fontWeight = 'bold';
    box.appendChild(detailsToggle);

    const detailsEl = document.createElement('pre');
    detailsEl.id = 'error-modal-details';
    // detailsEl.style.marginBottom = '18px';
    detailsEl.style.textAlign = 'left';
    detailsEl.style.display = 'none';
    detailsEl.style.width = '500px';
    detailsEl.style.whiteSpace = 'pre-wrap';
    detailsEl.style.background = '#f7f7fa';
    // detailsEl.style.padding = '10px';
    detailsEl.style.borderRadius = '8px';
    detailsEl.style.fontSize = '15px';
    detailsEl.style.color = '#3a3a3a';
    box.appendChild(detailsEl);

    const btn = document.createElement('button');
    btn.textContent = 'OK';
    btn.onclick = () => modal.remove();
    btn.style.padding = '12px 34px';
    btn.style.fontSize = '17px';
    btn.style.border = 'none';
    btn.style.borderRadius = '8px';
    btn.style.background = '#2563eb';
    btn.style.color = '#fff';
    btn.style.fontWeight = 'bold';
    btn.style.cursor = 'pointer';
    btn.style.boxShadow = '0 2px 8px rgba(37,99,235,0.10)';
    btn.style.transition = 'background 0.2s, box-shadow 0.2s';
    btn.onmouseover = () => {
      btn.style.background = '#1d4ed8';
      btn.style.boxShadow = '0 4px 16px rgba(37,99,235,0.20)';
    };
    btn.onmouseout = () => {
      btn.style.background = '#1e40af';
      btn.style.boxShadow = '0 2px 8px rgba(37,99,235,0.10)';
    };
    box.appendChild(btn);

    modal.appendChild(box);
    document.body.appendChild(modal);
  }
  modal.querySelector('#error-modal-text').textContent = message;

  const detailsToggle = modal.querySelector('button:nth-child(2)');
  const detailsEl = modal.querySelector('#error-modal-details');
 if (detailsEl) {
  if (details) {
    detailsToggle.style.display = 'block';
    let expanded = false;
    detailsToggle.onclick = () => {
      expanded = !expanded;
      detailsEl.style.display = expanded ? 'block' : 'none';
      detailsToggle.textContent = expanded ? 'hide' : 'Show details';
    };
    detailsEl.innerHTML = formatDeviceState(details); // вот тут!
  } else {
    detailsToggle.style.display = 'none';
    detailsEl.style.display = 'none';
    detailsEl.innerHTML = '';
  }
}

}

