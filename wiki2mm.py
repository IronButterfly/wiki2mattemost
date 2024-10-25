import requests
import json
import time

# Константы
WIKIPEDIA_PAGES = {
    "en": "Ispmanager",
    "ru": "Ispmanager",
    "tr": "Ispmanager",
    # Добавьте другие языки и страницы по необходимости
}

MATTERMOST_URL = "https://mm.yourdomain.tld"
MATTERMOST_CHANNEL_ID = "xxxxxxxxxxxxxxxxxxx"
MATTERMOST_TOKEN = "xxxxxxxxxxxxxxxxxxx"

# Файлы для хранения последних версий по каждому языку
LAST_REVISION_FILE_TEMPLATE = "last_revision_{}.json"

def get_wikipedia_last_revision(language, page):
    url = f"https://{language}.wikipedia.org/w/api.php?action=query&titles={page}&prop=revisions&rvprop=timestamp|user|comment&format=json"
    response = requests.get(url)
    data = response.json()
    
    # Извлекаем идентификатор последней редакции
    page_id = next(iter(data['query']['pages']))
    last_revision = data['query']['pages'][page_id]['revisions'][0]
    return last_revision

def load_last_revision(language):
    file_name = LAST_REVISION_FILE_TEMPLATE.format(language)
    try:
        with open(file_name, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return None

def save_last_revision(language, revision):
    file_name = LAST_REVISION_FILE_TEMPLATE.format(language)
    with open(file_name, 'w') as file:
        json.dump(revision, file)

def send_mattermost_message(message):
    url = f"{MATTERMOST_URL}/api/v4/posts"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {MATTERMOST_TOKEN}'
    }
    payload = {
        'channel_id': MATTERMOST_CHANNEL_ID,
        'message': message
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    return response.status_code == 201

def check_for_updates(language, page):
    # Получаем последнюю ревизию
    current_revision = get_wikipedia_last_revision(language, page)
    
    # Загружаем сохранённую ревизию
    last_revision = load_last_revision(language)
    
    # Сравниваем ревизии
    if last_revision is None or current_revision['timestamp'] != last_revision['timestamp']:
        # Изменения найдены
        article_url = f"https://{language}.wikipedia.org/wiki/{page}"
        history_url = f"https://{language}.wikipedia.org/w/index.php?title={page}&action=history"
        
        message = (
            f"Страница '{page}' на языке '{language}' была изменена пользователем {current_revision['user']} "
            f"с комментарием: {current_revision['comment']}.\n\n"
            f"Ссылка на статью: {article_url}\n"
            f"Ссылка на историю изменений: {history_url}"
        )
        
        # Отправляем сообщение в Mattermost
        if send_mattermost_message(message):
            print(f"Сообщение для страницы {page} ({language}) отправлено в Mattermost.")
            
            # Сохраняем текущую ревизию как последнюю
            save_last_revision(language, current_revision)
        else:
            print(f"Ошибка при отправке сообщения для страницы {page} ({language}) в Mattermost.")
    else:
        print(f"Изменений на странице {page} ({language}) нет.")

if __name__ == "__main__":
    while True:
        # Проверяем изменения для каждой страницы на каждом языке
        for language, page in WIKIPEDIA_PAGES.items():
            check_for_updates(language, page)
        
        # Ждем 24 часа (86400 секунд) перед следующей проверкой
        time.sleep(86400)
