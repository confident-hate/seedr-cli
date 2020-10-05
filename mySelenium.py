import time
from selenium import webdriver


def call_me_niggas():
    driver = webdriver.Firefox()
    driver.get("https://www.seedr.cc/")
    driver.find_element_by_link_text("Login").click()
    initial_cookies = driver.get_cookies()
    while 1:
        time.sleep(2)
        final_cookies = driver.get_cookies()
        if initial_cookies != final_cookies:
            print("Login Successfull")
            driver.close()
            return final_cookies
