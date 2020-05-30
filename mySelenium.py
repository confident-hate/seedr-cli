from selenium import webdriver
import time


def call_me_niggas():
    driver = webdriver.Firefox()
    driver.get("https://www.seedr.cc/")
    driver.find_element_by_link_text("Login").click()
    initial_cookies = driver.get_cookies()
    while 1:
        time.sleep(2)
        if initial_cookies != driver.get_cookies():
            print("Login Successfull")
            final_cookies = driver.get_cookies()
            dest = ''
            for item in final_cookies:
                name = item['name']
                value = item['value']
                dest += f'{name}={value};'
            return dest[:-1]


