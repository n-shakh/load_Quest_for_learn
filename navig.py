import time
from typing import Any

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.remote.webelement import WebElement
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException
import json
import re

from lists_web import list_web
from alias_types import TextQuestion, TextBlockQuestion, Chrome, DictJsonFile, BufQuestion, URLPicture, \
    IdChapter, DictQuestion, PathJsonFile, PathBufQuestionFile
from config import settings


def get_driver(scale: float = 1.0) -> Chrome:
    """Получает доступ к браузеру с корректировкой масштаба"""
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), chrome_options=chrome_options)
    driver.get('chrome://settings/')
    driver.execute_script(f'chrome.settingsPrivate.setDefaultZoom({scale});')
    return driver


def close_driver(driver: Chrome):
    """Завершает работу с браузером"""
    driver.quit()


def read_json(file: PathJsonFile = settings.db_file) -> DictJsonFile:
    """Возвращает словарь данных файла"""
    with open(file, 'r') as f:
        return json.load(f)


def write_json(db: DictJsonFile, file: PathJsonFile = settings.db_file):
    """Записывает словарь значений в файл с поддержкой руского языка"""
    with open(file, 'w') as f:
        json.dump(db, f, indent=4, separators=(',', ': '), ensure_ascii=False)


def get_block_quest(driver: Chrome) -> WebElement:
    """Возвращает блок с элементами вопроса и ответов"""
    try:
        element = driver.find_element(By.XPATH, '//*[@id="main-panel"]/div[2]/div')
    except NoSuchElementException:
        time.sleep(2)
        element = driver.find_element(By.XPATH, '//*[@id="main-panel"]/div[2]/div')
    return element


def avail_picture(block_quest: WebElement) -> URLPicture:
    """Если есть картинка, от возвращает ссылку на неё"""
    try:
        return block_quest.find_element(By.TAG_NAME, 'img').get_attribute('src')
    except NoSuchElementException:
        return ""


def decor_new_question(driver: Chrome) -> DictQuestion:
    """Возвращает сформированный из вопроса словарь"""
    question = dict.fromkeys(['text', 'picture', 'choice', 'answer', 'check'])

    block_quest = get_block_quest(driver)
    question['text'] = past_text_question(block_quest.text)

    list_answer = block_quest.find_element(By.TAG_NAME, 'ul')
    list_choices = list_answer.find_elements(By.TAG_NAME, 'li')
    mchoice = {str(i): '' for i in range(1, len(list_choices) + 1)}

    i = 1
    for choice in list_choices:
        mchoice[str(i)] = choice.text
        i += 1

    question['choice'] = mchoice
    question['answer'] = 1
    question['picture'] = avail_picture(block_quest)
    question['check'] = False

    return question


def add_new_question(driver: Chrome, chapter: IdChapter):
    """Добавляет новый вопрос в файл"""
    db = read_json()
    dict_quest = decor_new_question(driver)
    db[chapter].append(dict_quest)
    write_json(db)


def upload_in_buffer(text: TextQuestion, picture: URLPicture, col_quests: int,
                     file: PathBufQuestionFile = settings.buf_file):
    """Записывает вопрос в буферный файл для будущей проверки"""
    with open(file, 'w') as f:
        f.write(f"{{'text': \'{text}\', 'picture': \'{picture}\', 'col_quests': \'{col_quests}\'}}")


def download_in_buffer(file: PathBufQuestionFile = settings.buf_file) -> BufQuestion:
    """Возвращает записанный вопрос из буферыного файла"""
    with open(file, 'r') as f:
        return eval(f.read())


def check_answer(grade: str, chapter: IdChapter):
    """
    Если ответ верный, то статус вопроса меняется. Иначе - выбирвается следующий пункт.
     """
    int_grade: list[Any] = re.findall(r'-?\d+\.?\d*', grade)
    db = read_json()
    current_quest = download_in_buffer()
    for quest in db[chapter]:
        if quest['text'] == current_quest['text'] and quest['picture'] == current_quest['picture'] \
                and len(quest['choice']) == int(current_quest['col_quests']):
            if not quest['check']:
                if '0' not in int_grade:
                    quest['check'] = True
                else:
                    if len(quest['choice']) > quest['answer']:
                        quest['answer'] += 1
                    else:
                        quest['answer'] = 1

            break
    write_json(db)


def search_quest(driver: Chrome, chapter: IdChapter) -> int:
    """Возвращает номер пункта ответа"""
    try:
        driver.switch_to.frame("qti-player-frame")
    except NoSuchElementException:
        time.sleep(2)
        driver.switch_to.frame("qti-player-frame")
    block_quest = get_block_quest(driver)
    text_question = past_text_question(block_quest.text)
    link_picture = avail_picture(block_quest)
    number_of_questions = num_quest(block_quest.text)
    upload_in_buffer(text_question, link_picture, number_of_questions)
    answer = 1
    mquest = read_json()[chapter]
    if text_question in [mquest[i]['text'] for i in range(len(mquest))]:
        for quest in mquest:
            if quest['text'] == text_question and quest['picture'] == link_picture \
                    and len(quest['choice']) == number_of_questions:
                answer = quest['answer']
                break
    else:
        add_new_question(driver, chapter)

    return answer


def past_text_question(text: TextBlockQuestion) -> TextQuestion:
    """Возвращает первый абзац текста"""
    return text.split('\n')[0]


def num_quest(text: TextBlockQuestion) -> int:
    """Возвращает количество вопросов"""
    return len(text.split('\n')) - 1


def load_question(driver: Chrome, chapter: IdChapter):
    """Основные действия с вопросам"""
    # начать тест
    driver.find_element(By.ID, 'btnStartLesson').click()
    time.sleep(2)  # нужно 2 сек
    # проверка вопроса и возврат ответа
    answer = search_quest(driver, chapter)
    try:
        driver.find_element(By.XPATH, f'//ul/li[{answer}]/span/input').click()
    except NoSuchElementException:
        time.sleep(1)
        driver.find_element(By.XPATH, f'//ul/li[{answer}]/span/input').click()
    # принятие ответа
    try:
        driver.find_element(By.ID, 'commit-button').click()
    except ElementNotInteractableException:
        print('Коллизия')
    # закрытие теста
    driver.switch_to.default_content()
    driver.find_element(By.XPATH, '//*[@id="e4-library-LessonPanel-closeButton"]').click()
    time.sleep(1)
    driver.switch_to.alert.accept()
    time.sleep(1)
    # анализ ответа
    try:
        grade = str(driver.find_element(
            By.XPATH, '//*[@class="lesson-result x-component"]/tbody/tr[2]/td[1]/table/tbody/tr[2]/td/span').text)
    except NoSuchElementException:
        time.sleep(2)
        grade = str(driver.find_element(
            By.XPATH, '//*[@class="lesson-result x-component"]/tbody/tr[2]/td[1]/table/tbody/tr[2]/td/span').text)
    check_answer(grade, chapter)
    # переход на начальную страницу
    driver.find_element(By.XPATH, '//*[@id="e4-library-LessonStatsPanel-StartAgainButton"]/div').click()


def available_false_check(chapter: IdChapter, col: int) -> bool:
    """Проверяет наличие непроверенных ответов"""
    m_quest = read_json()[chapter]
    num_quest_in_json = len(m_quest)
    if num_quest_in_json == 0:
        return True
    else:
        if False in [m_quest[i]['check'] for i in range(num_quest_in_json)] or num_quest_in_json < col:
            return True
        else:
            return False


def add_new_chapter(chapter: IdChapter):
    """При необходимости добавляет новый раздел в файл"""
    m_quest = read_json()
    if chapter not in m_quest.keys():
        m_quest.update({chapter: []})
    write_json(m_quest)


def moving() -> None:
    driver = get_driver(0.5)

    site = settings.site
    driver.get(site)

    time.sleep(2)

    login = driver.find_element(By.ID, 'x-auto-24-input')
    password = driver.find_element(By.ID, 'x-auto-25-input')

    login.send_keys(settings.login)
    password.send_keys(settings.password, Keys.ENTER)

    time.sleep(2)

    for key in list_web:
        col = list_web[key]  # количество вопросов в блоке
        driver.get(f'{site}#id={key}&type=4&view=projector')
        add_new_chapter(key)
        time.sleep(1)

        i = 0  # для интереса сколько раз повоторяется вопросов

        while available_false_check(key, col):
            load_question(driver, key)
            i += 1
            time.sleep(1)

        with open(settings.analiz_file, 'a') as f:
            f.write(f'{key}:{i};\n' if i > 0 else '')
    close_driver(driver)


if __name__ == '__main__':
    moving()
