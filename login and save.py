import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = webdriver.Chrome()
wait = WebDriverWait(driver, 10)

try:
    print("در حال لاگین و دریافت توکن...")
    driver.get('https://mail.chbeta.ir/nui/auth/login')

    # لاگین
    wait.until(
        EC.element_to_be_clickable((By.XPATH, "//input[contains(@placeholder, 'کاربری') or @type='text']"))).send_keys(
        "chtest")
    wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='password']"))).send_keys("Sa-123456")
    wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[@id='loginbtn'] | //button[contains(., 'ورود')]"))).click()

    time.sleep(5)  # مکث برای دریافت کامل توکن‌ها

    # ذخیره سشن
    session_data = {
        "cookies": driver.get_cookies(),
        "local_storage": driver.execute_script(
            "var ls = window.localStorage, items = {}; "
            "for (var i = 0, k; i < ls.length; ++i) { k = ls.key(i); items[k] = ls.getItem(k); } "
            "return items; "
        )
    }

    with open("session.json", "w") as f:
        json.dump(session_data, f)

    print("✅ لاگین موفق! توکن در session.json ذخیره شد.")

finally:
    driver.quit()
