class IgusApi {
    constructor(baseUrl = '/api/v1/igus/motor') {
        this.baseUrl = baseUrl;
    }

    // Получить состояние мотора
    async getState() {
        const response = await fetch(`${this.baseUrl}/status`);
        if (!response.ok) throw new Error(await response.text());
        const data = await response.json(); // Вот тут твои данные
        return data;
    }

    // Получить данные мотора (сжатый формат)
    async getData() {
        const response = await fetch(`${this.baseUrl}/status`);
        if (!response.ok) throw new Error(await response.text());
        const data = await response.json(); // Вот тут твои данные
        return data;
    }

    // Универсальная отправка команды
    async sendCommand(type, params = {}) {
        const response = await fetch(`${this.baseUrl}/`+type, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params) // <-- убираем params как обёртку!
        });
        if (!response.ok) throw new Error(await response.text());
        return await response.json();
    }

    // Команда reference (homing)
    async reference() {
        return this.sendCommand('reference');
    }

    // Команда move_to_position
    async moveToPosition(position, velocity = 5000, acceleration = 5000) {
        return this.sendCommand('move', { position, velocity, acceleration });
    }

    // Сброс ошибок
    async faultReset() {
        return this.sendCommand('fault_reset');
    }
}

// Пример использования:
window.igus = new IgusApi();

// Получить состояние
igus.getData().then(console.log).catch(console.error);

// Отправить reference
// igus.reference().then(console.log).catch(console.error);

// Переместить мотор
// igus.moveToPosition(1000, 5000, 5000).then(console.log).catch(console.error);