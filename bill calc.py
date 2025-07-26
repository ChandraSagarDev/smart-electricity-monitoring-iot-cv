from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
# Import Selenium modules for web automation and scraping
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

chrome_options = Options()

chrome_options.add_argument("--headless=new")  # Enables headless mode (runs in background)
chrome_options.add_argument("--disable-gpu")  # Disables GPU acceleration (for stability)
chrome_options.add_argument("--no-sandbox")  # Bypass OS security model
chrome_options.add_argument("--disable-dev-shm-usage")  # Prevent crashes in Docker/Linux
service = Service(executable_path="chromedriver.exe")
driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    driver.get("https://bills.kseb.in")
    reading=int(input("Enter Kwh Reading: "))
    phase=int(input("Three Phase or Single(1/3):"))
    if(phase==1):
        None
    else:
        phase_element = driver.find_element(By.ID, "phase3")
        phase_element.click()
    reading=str(reading)
    input_element = driver.find_element(By.ID, "unit")
    input_element.send_keys(reading + Keys.ENTER)

    wait = WebDriverWait(driver, 10)

    #TOTAL AMOUNT
    element = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".total.blue-tail")))

    text_value = element.text.strip()  # Remove extra spaces
    clean_value = ''.join(filter(str.isdigit, text_value))  # Keep only numbers
    val = int(clean_value) if clean_value else 0  # Convert to integer safely
    val=val/100
   
    time.sleep(5)
    print("==========================")
    print(f"The Amount: {val}")
    print("==========================")

except Exception as e:
    print("Error:", e)

finally:
    driver.quit()
