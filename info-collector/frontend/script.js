const API_URL = 'http://127.0.0.1:8000';

const form = document.querySelector('#collect-form');
const statusElement = document.querySelector('#status');
const resultsElement = document.querySelector('#results');
const historyElement = document.querySelector('#history');

function setStatus(message, type = '') {
    statusElement.textContent = message;
    statusElement.className = `status ${type}`;
}

function formatDate(value) {
    return new Date(value).toLocaleString('ru-RU');
}

function escapeHtml(value) {
    const div = document.createElement('div');
    div.textContent = value;
    return div.innerHTML;
}

function renderResult(result) {
    const fragments = result.fragments.length
        ? result.fragments.map((text) => `<p class="fragment">${escapeHtml(text)}</p>`).join('')
        : '<p>По запросу не найдено подходящих абзацев.</p>';

    resultsElement.innerHTML = `
        <h3>${escapeHtml(result.title)}</h3>
        <p><strong>Дата сбора:</strong> ${formatDate(result.collected_at)}</p>
        <p><strong>URL источника:</strong> <a href="${escapeHtml(result.url)}" target="_blank">${escapeHtml(result.url)}</a></p>
        <p><strong>Количество найденных ссылок:</strong> ${result.links_count}</p>
        <h4>Найденные фрагменты текста</h4>
        ${fragments}
    `;
}

async function loadHistory() {
    const response = await fetch(`${API_URL}/history`);
    const history = await response.json();

    if (!history.length) {
        historyElement.innerHTML = '<p>История пока пуста.</p>';
        return;
    }

    historyElement.innerHTML = history.map((item) => `
        <article class="history-item">
            <h3>${escapeHtml(item.title)}</h3>
            <p><strong>Запрос:</strong> ${escapeHtml(item.query)}</p>
            <p><strong>Дата:</strong> ${formatDate(item.collected_at)}</p>
            <p><strong>URL:</strong> ${escapeHtml(item.url)}</p>
            <p><strong>Ссылок найдено:</strong> ${item.links_count}</p>
            <div class="history-actions">
                <button class="secondary" onclick="showSavedResult(${item.id})">Показать</button>
                <button class="danger" onclick="deleteResult(${item.id})">Удалить</button>
            </div>
        </article>
    `).join('');
}

async function showSavedResult(id) {
    const response = await fetch(`${API_URL}/results/${id}`);
    const result = await response.json();
    renderResult(result);
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

async function deleteResult(id) {
    await fetch(`${API_URL}/results/${id}`, { method: 'DELETE' });
    await loadHistory();
    setStatus('Запись удалена.', 'success');
}

form.addEventListener('submit', async (event) => {
    event.preventDefault();
    setStatus('Идёт сбор информации...');

    const formData = new FormData(form);
    const payload = {
        query: formData.get('query'),
        url: formData.get('url'),
    };

    try {
        const response = await fetch(`${API_URL}/collect`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Ошибка сбора данных');
        }

        const result = await response.json();
        renderResult(result);
        await loadHistory();
        setStatus('Информация успешно собрана и сохранена.', 'success');
    } catch (error) {
        setStatus(error.message, 'error');
    }
});

loadHistory();
