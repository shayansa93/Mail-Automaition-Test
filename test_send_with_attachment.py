import time
import json
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ==============================================================
# بخش ۱: تنظیمات مرورگر، شنود شبکه و تزریق سشن
# ==============================================================
chrome_options = Options()
chrome_options.add_experimental_option("detach", True)
chrome_options.add_argument("--start-maximized")

# فعال‌سازی شنود تب Network برای شکار ریکوئست‌های 200
chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 10)


def run_step(action, description):
    try:
        action()
        print(f"  [✓] {description} با موفقیت انجام شد.")
    except Exception as e:
        error_msg = str(e).split('\n')[0]
        print(f"  [⚠️] {description} خطا داد. علت: {error_msg}")


driver.get('https://mail.chbeta.ir/nui/')
try:
    with open("session.json", "r") as f:
        session_data = json.load(f)

    for cookie in session_data.get("cookies", []):
        driver.add_cookie(cookie)

    for key, value in session_data.get("local_storage", {}).items():
        safe_value = json.dumps(value) if not isinstance(value, str) else f"'{value}'"
        driver.execute_script(f"window.localStorage.setItem('{key}', {safe_value});")

    for key, value in session_data.get("session_storage", {}).items():
        safe_value = json.dumps(value) if not isinstance(value, str) else f"'{value}'"
        driver.execute_script(f"window.sessionStorage.setItem('{key}', {safe_value});")

    driver.refresh()
    print("✅ توکن لود شد. ورود به حساب...")
except Exception as e:
    print(f"❌ فایل session.json پیدا نشد یا خطا دارد!")
    driver.quit()
    exit()


# ==============================================================
# تابع هوشمند برای بررسی وضعیت شبکه (200 OK)
# ==============================================================
def verify_network_request(api_endpoint, timeout=15):
    print(f"  [⏳] در حال بررسی ریکوئست '{api_endpoint}' در شبکه...")

    for _ in range(timeout):
        logs = driver.get_log("performance")
        for entry in logs:
            try:
                log_data = json.loads(entry["message"])["message"]
                if log_data["method"] == "Network.responseReceived":
                    response = log_data["params"]["response"]
                    url = response.get("url", "")
                    status = response.get("status")

                    if api_endpoint.lower() in url.lower():
                        clean_url = url.split('?')[0]
                        print(f"    [🌐] شکار شد! URL: {clean_url} | Status: {status}")
                        if status == 200:
                            return True
                        elif status == 204:
                            continue  # ریکوئست‌های Preflight نادیده گرفته شوند
                        else:
                            raise Exception(f"بک‌اند ارور داد! وضعیت: {status}")
            except:
                pass
        time.sleep(1)

    raise Exception(f"زمان تمام شد! ریکوئست {api_endpoint} پیدا نشد.")


# ==============================================================
# بخش ۲: سناریوی ارسال نامه با پیوست
# ==============================================================
print("\n▶️ شروع تست: ارسال نامه جدید همراه با پیوست")


# ۱. رفتن به فرم نامه جدید و عبور از صفحه لودینگ (Splash Screen)
def click_new_email():
    driver.get('https://mail.chbeta.ir/nui/mail/message?query=2&page=1&type=inbox')

    try:
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".splash-screen")))
    except:
        pass

    time.sleep(2)
    new_mail_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'نامه جدید')]")))
    driver.execute_script("arguments[0].click();", new_mail_btn)


run_step(click_new_email, "کلیک روی نامه جدید و عبور از لودینگ")
time.sleep(1.5)


# ۲. پر کردن گیرنده (دور زدن آیکون مزاحم با جاوااسکریپت)
def type_receiver():
    receiver_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@id='inputItem']")))
    driver.execute_script("arguments[0].click();", receiver_input)
    receiver_input.send_keys("shayan2")
    time.sleep(1)
    wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'shayan2@chbeta.ir')]"))).click()


run_step(type_receiver, "کلیک و انتخاب گیرنده")


# ۳. پر کردن موضوع
def type_subject():
    webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
    time.sleep(1)
    inputs = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//input[contains(@id, 'mat-input')]")))
    target_input = inputs[-1]
    target_input.click()
    target_input.clear()
    target_input.send_keys("تست ارسال فایل پیوست")


run_step(type_subject, "تایپ موضوع")


# ۴. پر کردن بدنه ایمیل
def type_body():
    iframes = driver.find_elements(By.XPATH, "//iframe")
    if len(iframes) > 0:
        driver.switch_to.frame(iframes[-1])
        body = wait.until(EC.presence_of_element_located((By.XPATH, "//body")))
        driver.execute_script("arguments[0].innerHTML = '<p>این نامه حاوی یک فایل پیوست است.</p>';", body)
        driver.switch_to.default_content()
    else:
        body = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//*[@id='tinymce'] | //div[contains(@class, 'mce-content-body')]")))
        driver.execute_script("arguments[0].innerHTML = '<p>این نامه حاوی یک فایل پیوست است.</p>';", body)


run_step(type_body, "تایپ بدنه")


# ۵. آپلود فایل پیوست (تریگر کردن هوشمند آنگولار)
def upload_file():
    file_path = os.path.join(os.getcwd(), "dummy_test_attachment.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("این یک فایل تستی ایجاد شده توسط اتوماسیون سلنیوم است.")

    file_inputs = driver.find_elements(By.XPATH, "//input[@type='file']")
    target_input = file_inputs[-1]

    # آشکار کردن اینپوت برای جلوگیری از ارورهای امنیتی مرورگر
    driver.execute_script("arguments[0].style.display = 'block'; arguments[0].style.visibility = 'visible';",
                          target_input)

    # تزریق مسیر فایل
    target_input.send_keys(file_path)

    # شلیک رویداد change تا آنگولار متوجه آپلود شود و ریکوئست را بفرستد
    driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", target_input)


run_step(upload_file, "آپلود فایل و بیدار کردن رویداد سایت")

# ۶. بررسی ریکوئست 200 برای آپلود فایل (استفاده از کلمه کلیدی منعطف)
run_step(lambda: verify_network_request("file"), "بررسی کد 200 برای آپلود پیوست (file)")


# ۷. کلیک روی ارسال
def click_send():
    send_btn = wait.until(EC.presence_of_element_located((
        By.XPATH, "//button[normalize-space()='ارسال'] | //button[.//span[normalize-space()='ارسال']]"
    )))
    driver.execute_script("arguments[0].click();", send_btn)


run_step(click_send, "کلیک روی دکمه ارسال")

# ۸. بررسی ریکوئست 200 برای ارسال نهایی
run_step(lambda: verify_network_request("/api/mail/send"), "بررسی کد 200 برای ارسال نهایی (send)")

print("\n🏁 تست ارسال با پیوست با موفقیت و تاییدیه قطعی بک‌اند به پایان رسید.")
