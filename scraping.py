import sqlite3
from sqlite3 import Error

import self as self
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver import Chrome
from datetime import datetime, timedelta
import time
import re

database_name = r"scraping.db"
scrape_url = "https://website.com/"
web_driver_path = "chromedriver.exe"


def main():
    conn = create_connection(database_name)
    driver = Chrome()
    driver.get(scrape_url)
    time.sleep(10)
    driver.find_element_by_class_name('auth__form-btn.enter').click()

    username = self.driver.find_element_by_name("login")
    password = self.driver.find_element_by_name("password")
    username.send_keys("###")
    password.send_keys("###")
    # driver.find_element_by_xpath("//input[@name='commit']").click()
    driver.find_elements_by_class_name('btn-green')[2].click()

    last_refresh_page_time = datetime.now()
    time.sleep(2)
    is_exist = False
    while True:
        if datetime.now() >= last_refresh_page_time + timedelta(minutes=3):
            last_refresh_page_time = datetime.now()
            driver.refresh()
            print(last_refresh_page_time)
        if check_exists_by_class_name(driver, 'danger'):
            if not is_exist:
                try:
                    danger = str(driver.find_element_by_class_name('danger').text).replace('\n', ' ').replace('х', 'x')
                except NoSuchElementException:
                    continue
                except StaleElementReferenceException:
                    continue
                pattern = "The game stopped at \d+\.\d+x"
                if re.match(pattern, danger):
                    coefficient = float(re.findall("\d+\.\d+", danger)[0])
                    game_info = str(driver.find_elements_by_class_name('chart-block')[0].text).split('\n')
                    game_number = 0
                    if game_info[0].__len__() != 'Game №'.__len__():
                        game_number = int(game_info[0].replace('Game №', ''))
                    count_bets = 0
                    if game_info[1].__len__() != 'Rates: '.__len__():
                        count_bets = int(game_info[1].replace('Rates: ', ''))
                    bids_amount = float(
                        re.findall("\d+\.\d+", str(driver.find_elements_by_class_name('chart-block')[1].text))[0])
                    current_time = datetime.now()
                    game = (game_number, count_bets, bids_amount, coefficient, current_time)
                    game_id = insert_into_games_history(conn, game)
                    print(coefficient)
                    if check_exists_by_class_name(driver, 'tab-row'):
                        users = driver.find_elements_by_class_name('tab-row')
                        i = 1
                        while i <= (len(users) - 1):
                            users_data = users[i].find_elements_by_class_name('tab-cell')
                            user_name = str(users_data[0].text)
                            user_bid_amount = float(users_data[1].text)
                            if str(users_data[2].text):
                                user_coefficient = float(str(users_data[2].text).replace('х', ''))
                                if user_coefficient <= coefficient:
                                    user_win_amount = float(users_data[3].text) - user_bid_amount
                                else:
                                    user_win_amount = -user_bid_amount
                            else:
                                user_coefficient = 0
                                user_win_amount = -user_bid_amount
                            bids = (game_id, user_name, user_bid_amount, user_coefficient, user_win_amount)
                            insert_into_bids(conn, bids)
                            i += 1
                    is_exist = True
                elif 'The game will start in ' in danger:
                    is_exist = False
        else:
            is_exist = False
        time.sleep(1)


def insert_into_games_history(conn, game):
    c = conn.cursor()
    c.execute("INSERT INTO games_history VALUES (null, ?, ?, ?, ?, ?)", game)
    conn.commit()
    c.execute("SELECT id FROM games_history ORDER BY id DESC LIMIT 1")
    rows = c.fetchall()
    for row in rows:
        return int(row[0])


def insert_into_bids(conn, bids):
    c = conn.cursor()
    c.execute("INSERT INTO bids VALUES (null, ?, ?, ?, ?, ?)", bids)
    conn.commit()


def check_exists_by_class_name(driver, name):
    try:
        driver.find_element_by_class_name(name)
    except NoSuchElementException:
        return False
    return True


def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        sql = 'CREATE TABLE IF NOT EXISTS games_history (id INTEGER PRIMARY KEY AUTOINCREMENT, game_number INTEGER, ' \
              'count_bets INTEGER, bids_amount REAL, coefficient REAL, time DATETIME)'
        c.execute(sql)
        sql = 'CREATE TABLE IF NOT EXISTS bids (id INTEGER PRIMARY KEY AUTOINCREMENT, game_id INTEGER, ' \
              'name VARCHAR(25), bid_amount REAL, coefficient REAL, win_amount REAL)'
        c.execute(sql)
    except Error as e:
        print(e)
    return conn


if __name__ == '__main__':
    main()
