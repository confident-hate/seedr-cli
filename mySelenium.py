import time
from sys import platform
from selenium import webdriver


def call_me_niggas():
    if platform == "linux" or platform == "linux2":
        driver = webdriver.Firefox(service_log_path='/dev/null')
    elif platform == "win32":
        from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
        cap = DesiredCapabilities().FIREFOX
        driver = webdriver.Firefox(capabilities=cap)
    driver.get("https://www.seedr.cc/")
    driver.find_element_by_link_text("Log in").click()
    initial_cookies = driver.get_cookies()
    while 1:
        time.sleep(2)
        final_cookies = driver.get_cookies()
        if initial_cookies != final_cookies:
            print("Login Successfull")
            driver.close()
            return final_cookies
