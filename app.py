from flask import Flask, render_template, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import requests
import json
import schedule
import time
import sqlite3
import random
from twocaptcha import TwoCaptcha

# Configure 2Captcha API
solver = TwoCaptcha("your-2captcha-api-key")  # Replace with your 2Captcha API key

# Initialize Flask app
app = Flask(__name__)

# Function to solve CAPTCHA using 2Captcha
def solve_captcha(sitekey, url):
    try:
        result = solver.recaptcha(sitekey=sitekey, url=url)
        return result["code"]
    except Exception as e:
        return f"Error solving CAPTCHA: {e}"

# Function to fill forms using Selenium
def fill_form(url, form_data):
    driver = None
    try:
        # Configure Chrome options
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        # Use selenium-stealth to avoid detection
        from selenium_stealth import stealth
        stealth(
            driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )

        driver.get(url)

        # Parse the form data
        data = json.loads(form_data)
        for key, value in data.items():
            # Wait for the input field to be present
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, key))
            )
            element.send_keys(value)
            time.sleep(random.uniform(1, 3))  # Add a random delay

        # Submit the form
        submit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.NAME, "submit"))
        )
        submit_button.click()
        return "Form filled successfully!"
    except Exception as e:
        return f"Error filling form: {e}"
    finally:
        if driver:
            driver.quit()

# Function to scrape data using BeautifulSoup
def scrape_data(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        headings = [h.text for h in soup.find_all("h1")]
        return f"Scraped Data: {headings}"
    except Exception as e:
        return f"Error scraping data: {e}"

# Function to navigate websites using Selenium
def navigate_website(url, actions):
    driver = None
    try:
        # Configure Chrome options
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        # Use selenium-stealth to avoid detection
        from selenium_stealth import stealth
        stealth(
            driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )

        driver.get(url)

        # Parse the actions JSON string into a Python object
        actions = json.loads(actions)

        # Ensure actions is a list of dictionaries
        if isinstance(actions, list):
            for action in actions:
                if action["type"] == "input":
                    # Wait for the input field to be present
                    element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, action["element"]))
                    )
                    element.send_keys(action["value"])
                    time.sleep(random.uniform(1, 3))  # Add a random delay
                elif action["type"] == "click":
                    # Wait for the button to be clickable
                    element = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, action["element"]))
                    )
                    element.click()
                    time.sleep(random.uniform(1, 3))  # Add a random delay
            return "Navigation completed successfully!"
        else:
            return "Error: Actions must be a list of dictionaries."
    except Exception as e:
        return f"Error navigating website: {e}"
    finally:
        if driver:
            driver.quit()

# Function to schedule tasks
def schedule_task(task_type, url, data, time):
    try:
        if task_type == "Form Filling":
            schedule.every().day.at(time).do(fill_form, url, data)
        elif task_type == "Data Scraping":
            schedule.every().day.at(time).do(scrape_data, url)
        elif task_type == "Website Navigation":
            schedule.every().day.at(time).do(navigate_website, url, data)
        return f"Task scheduled for {time}!"
    except Exception as e:
        return f"Error scheduling task: {e}"

# Function to save task configurations to SQLite
def save_task_to_db(task_type, url, data, time):
    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, type TEXT, url TEXT, data TEXT, time TEXT)")
    cursor.execute("INSERT INTO tasks (type, url, data, time) VALUES (?, ?, ?, ?)", (task_type, url, data, time))
    conn.commit()
    conn.close()

# Flask Routes
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/run_task", methods=["POST"])
def run_task():
    task_type = request.form.get("task_type")
    url = request.form.get("url")
    data = request.form.get("data")
    time = request.form.get("time")

    try:
        if task_type == "Form Filling":
            result = fill_form(url, data)
        elif task_type == "Data Scraping":
            result = scrape_data(url)
        elif task_type == "Website Navigation":
            # Validate JSON data before passing it to navigate_website
            try:
                json.loads(data)  # Check if data is valid JSON
                result = navigate_website(url, data)
            except json.JSONDecodeError:
                result = "Error: Invalid JSON data for navigation actions."
        elif task_type == "Task Scheduling":
            result = schedule_task(task_type, url, data, time)
            save_task_to_db(task_type, url, data, time)
        else:
            result = "Invalid task type."
    except Exception as e:
        result = f"An error occurred: {e}"

    return jsonify({"result": result})

# Run scheduled tasks in the background
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    # Start the scheduler in a separate thread
    import threading
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()

    # Start the Flask app
    app.run(debug=True)