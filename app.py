from flask import Flask, render_template, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import requests
import json
import schedule
import time
import sqlite3
import google.generativeai as genai

# Configure Gemini API
genai.configure(api_key="AIzaSyByVR9XKpvvWDzshhxUKidy3WFFaV--sio")  # Replace with your Gemini API key

# Initialize Gemini model
model = genai.GenerativeModel('gemini-pro')

# Initialize Flask app
app = Flask(__name__)

# Function to handle CAPTCHA using Gemini
def handle_captcha(image_url):
    response = model.generate_content(f"Solve the CAPTCHA in this image: {image_url}")
    return response.text

# Function to fill forms using Selenium
def fill_form(url, form_data):
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        driver.get(url)
        data = json.loads(form_data)
        for key, value in data.items():
            driver.find_element(By.NAME, key).send_keys(value)
        driver.find_element(By.NAME, "submit").click()
        return "Form filled successfully!"
    except Exception as e:
        return f"Error filling form: {e}"
    finally:
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
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        driver.get(url)
        
        # Parse the actions JSON string into a Python object
        actions = json.loads(actions)
        
        # Ensure actions is a list of dictionaries
        if isinstance(actions, list):
            for action in actions:
                if action["type"] == "click":
                    driver.find_element(By.XPATH, action["element"]).click()
                elif action["type"] == "input":
                    driver.find_element(By.XPATH, action["element"]).send_keys(action["value"])
            return "Navigation completed successfully!"
        else:
            return "Error: Actions must be a list of dictionaries."
    except Exception as e:
        return f"Error navigating website: {e}"
    finally:
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