import requests
import time
import hashlib
from mattermostdriver import Driver

# Конфигурация Mattermost
MATTERMOST_URL = 'your_mattermost_url'
MATTERMOST_TOKEN = 'auth_token'
MATTERMOST_CHANNEL_ID = 'channel_id'  # ID канала

# URL статьи на Википедии (замените 'Example' на нужную вам статью)
ARTICLE_TITLE = 'Example'
WIKIPEDIA_API_URL = f'https://ru.wikipedia.org/w/api.php?action=query&prop=revisions&titles={ARTICLE_TITLE}&rvprop=content&format=json'
WIKIPEDIA_ARTICLE_URL = f'https://ru.wikipedia.org/wiki/{ARTICLE_TITLE}'

# Время ожидания между проверками (в секундах)
CHECK_INTERVAL = 86400  # 24 часа

def get_wikipedia_content(url):
    response = requests.get(url)
    if response.status_code == 200:
        pages = response.json().get('query', {}).get('pages', {})
        for page_id, page_info in pages.items():
            revisions = page_info.get('revisions', [])
            if revisions:
                return revisions[0].get('*', '')
    return None

def send_mattermost_notification(driver, channel_id, message):
    driver.posts.create_post({
        'channel_id': channel_id,
        'message': message
    })

def main():
    driver = Driver({
        'url': MATTERMOST_URL,
        'token': MATTERMOST_TOKEN,
        'scheme': 'https',
        'port': 443,
        'basepath': '/api/v4',
        'verify': True,
        'timeout': 30,
        'debug': False
    })

    driver.login()

    previous_hash = None

    while True:
        content = get_wikipedia_content(WIKIPEDIA_API_URL)
        if content:
            current_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            if previous_hash and current_hash != previous_hash:
                message = f"Статья на Википедии была изменена: {WIKIPEDIA_ARTICLE_URL}"
                send_mattermost_notification(driver, MATTERMOST_CHANNEL_ID, message)
                print("Уведомление успешно отправлено")
            previous_hash = current_hash
        else:
            print("Не удалось получить содержимое статьи")
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
