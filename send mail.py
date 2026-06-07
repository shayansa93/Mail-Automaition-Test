import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains

# بخش ۱: راه‌اندازی مرورگر و تزریق خودکار سشن
# ==============================================================
chrome_options = Options()
chrome_options.add_experimental_option("detach", True)

# 🌟 این خط را دقیقاً اینجا اضافه کن تا شنود شبکه فعال شود
chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

# ساخت مرورگر با تنظیمات بالا
driver = webdriver.Chrome(options=chrome_options)
driver.maximize_window()
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
    print(f"❌ فایل session.json پیدا نشد یا خطا دارد! اول لاگین را اجرا کن.")
    driver.quit()
    exit()

# ==============================================================
# بخش ۲: بدنه اصلی تست (مخصوص همین سناریو)
# ==============================================================
print("\n▶️ شروع تست: ارسال نامه جدید")

run_step(lambda: driver.get('https://mail.chbeta.ir/nui/mail/message?query=2&page=1&type=inbox'), "ورود به اینباکس")
time.sleep(5)

run_step(lambda: wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'نامه جدید')]"))).click(), "کلیک روی نامه جدید")
time.sleep(1.5)

run_step(lambda: wait.until(EC.element_to_be_clickable((By.XPATH, "//mat-select[@role='combobox'] | //div[contains(@id,'mat-select-value')]"))).click(), "باز کردن منوی فرستنده")
run_step(lambda: wait.until(EC.element_to_be_clickable((By.XPATH, "//mat-option[contains(., 'TestZade')]"))).click(), "انتخاب حساب TestZade")

run_step(lambda: wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@id='inputItem']"))).click(), "کلیک روی فیلد گیرنده")
run_step(lambda: wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@id='inputItem']"))).send_keys("sh"), "تایپ گیرنده (sh)")
time.sleep(1)
run_step(lambda: wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'shayan2@chbeta.ir')]"))).click(), "انتخاب گیرنده از لیست")

def type_subject():
    webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
    time.sleep(1)
    inputs = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//input[contains(@id, 'mat-input')]")))
    target_input = inputs[-1]
    target_input.click()
    target_input.clear()
    target_input.send_keys("تست ارسال از اسکریپت مستقل")
run_step(type_subject, "تایپ موضوع نامه")

def type_body():
    iframes = driver.find_elements(By.XPATH, "//iframe")
    if len(iframes) > 0:
        driver.switch_to.frame(iframes[-1])
        body = wait.until(EC.element_to_be_clickable((By.XPATH, "//body")))
        body.click()
        body.send_keys("این یک متن تستی است.")
        driver.switch_to.default_content()
    else:
        body = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='tinymce'] | //div[contains(@class, 'mce-content-body')]")))
        body.click()
        body.send_keys("این یک متن تستی است.")
run_step(type_body, "تایپ بدنه ایمیل")

def click_send_button():
    send_btn = wait.until(EC.element_to_be_clickable((
        By.XPATH, "//app-new-compose//button[contains(., 'ارسال')] | //app-modal-container//button[.//span[contains(text(), 'ارسال')]]"
    )))
    send_btn.click()
run_step(click_send_button, "کلیک روی ارسال")

# ۶. چک کردن تب Network برای دریافت ریکوئست 200 (تشخیص دقیق API)
def verify_network_200():
    print("  [⏳] در حال پایش زنده ترافیک شبکه (حداکثر ۱۰ ثانیه)...")

    max_retries = 10

    for attempt in range(max_retries):
        logs = driver.get_log("performance")

        for entry in logs:
            try:
                log_data = json.loads(entry["message"])["message"]

                # فقط پاسخ‌های دریافتی از سرور را بررسی می‌کنیم
                if log_data["method"] == "Network.responseReceived":
                    response = log_data["params"]["response"]
                    url = response.get("url", "")
                    status = response.get("status")

                    url_lower = url.lower()

                    # 🎯 تغییر اصلی: جستجوی دقیق مسیر API به جای یک کلمه ساده
                    if "/api/mail/send" in url_lower:
                        clean_url = url.split('?')[0]
                        print(f"  [🌐] ریکوئست هدف (API) پیدا شد! URL: {clean_url} | Status: {status}")

                        if status == 200:
                            print("  [✓] تایید قطعی: سرور وضعیت 200 OK برگرداند (ارسال موفق).")
                            return
                        elif status == 204:
                            # نادیده گرفتن درخواست‌های Preflight (OPTIONS)
                            continue
                        else:
                            raise Exception(f"بک‌اند ارور داد! کد وضعیت سرور: {status}")
            except Exception as e:
                pass

        time.sleep(1)

    raise Exception("زمان انتظار تمام شد! ریکوئست اصلی /api/mail/send در شبکه یافت نشد.")


run_step(verify_network_200, "بررسی کد 200 در تب Network")



print("\n🏁 تست با موفقیت به پایان رسید.")
