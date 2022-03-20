import os
from dotenv import load_dotenv

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from twilio.rest import Client
from apscheduler.schedulers.blocking import BlockingScheduler


# Setup variables and constants
load_dotenv()
CHROME_DRIVER_PATH = os.getenv('CHROME_DRIVER_PATH')
AURION_URL = "https://aurion.junia.com/"
AURION_EMAIL = os.getenv('AURION_EMAIL')
AURION_PASSWORD = os.getenv('AURION_PASSWORD')
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
MY_PHONE_NUMBER = os.getenv('MY_PHONE_NUMBER')

current_number_of_grades = 0


def send_sms_notification():
    account = TWILIO_ACCOUNT_SID
    token = TWILIO_AUTH_TOKEN
    client = Client(account, token)
    client.messages.create(to=MY_PHONE_NUMBER, from_=TWILIO_PHONE_NUMBER,
                           body="Une nouvelle note est disponible sur Aurion ! Va vite voir: https://aurion.junia.com")


def routine():
    # Initialise browser
    driver = webdriver.Chrome(CHROME_DRIVER_PATH)
    driver.get(AURION_URL)

    # Wait login page to be displayed
    try:
        element_to_check = EC.presence_of_element_located(
            (By.XPATH, '//input[@id="username"]'))
        WebDriverWait(driver, 10).until(element_to_check)
    except TimeoutException:
        print('Timed out waiting for page to load')
    # Fill username
    username_input = driver.find_element(By.ID, 'username')
    username_input.send_keys(AURION_EMAIL)
    # Fill password
    password_input = driver.find_element(By.ID, 'password')
    password_input.send_keys(AURION_PASSWORD)
    # Submit form
    driver.find_element(By.ID, 'j_idt28').click()

    # Wait home page to be displayed
    try:
        element_to_check = EC.presence_of_element_located(
            (By.ID, 'form:j_idt753'))
        WebDriverWait(driver, 10).until(element_to_check)
    except TimeoutException:
        print('Timed out waiting for page to load')
    # Navigate to scolarity submenu
    driver.find_element(
        By.XPATH, """ //li[@role='menuitem']//span[contains(text(), 'Scolarité')] """).click()
    # Wait submenu to be displayed
    try:
        element_to_check = EC.presence_of_element_located(
            (By.XPATH, """ //li[@role='menuitem']//span[text()='Mes notes'] """))
        WebDriverWait(driver, 10).until(element_to_check)
    except TimeoutException:
        print('Timed out waiting for page to load')
    # Navigate to grades page
    driver.find_element(
        By.XPATH, """ //li[@role='menuitem']//span[text()='Mes notes'] """).click()

    # Wait grades page to be displayed
    try:
        element_to_check = EC.presence_of_element_located(
            (By.XPATH, """ //button[@id="form:search"] """))
        WebDriverWait(driver, 10).until(element_to_check)
    except TimeoutException:
        print('Timed out waiting for page to load')
    # Open search result alert
    driver.find_element(
        By.XPATH, """ //button[@id="form:search"] """).click()
    # Wait alert to be displayed
    try:
        element_to_check = EC.presence_of_element_located(
            (By.XPATH, """ //div[@id="form:messages"]//span[@class="ui-messages-info-summary"] """))
        WebDriverWait(driver, 10).until(element_to_check)
    except TimeoutException:
        print('Timed out waiting for alert to load')
    raw_text = driver.find_element(
        By.XPATH, """ //div[@id="form:messages"]//span[@class="ui-messages-info-summary"] """).text
    new_number_of_grades = [int(s)
                            for s in raw_text .split() if s.isdigit()][0]
    print("Grades found:", new_number_of_grades)

    driver.close()

    # Process data
    global current_number_of_grades
    if new_number_of_grades > current_number_of_grades:
        print("A new grave is available!")
        current_number_of_grades = new_number_of_grades
        send_sms_notification()


# Execute the routine each hours
scheduler = BlockingScheduler()
scheduler.add_job(routine, 'interval', minutes=20)
scheduler.start()
