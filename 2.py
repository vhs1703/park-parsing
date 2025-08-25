from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
import pandas as pd
import urllib.parse
import gspread
from gspread_dataframe import set_with_dataframe
import time

def parse_parklot_prices(url):
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_selector("div.offer__price", timeout=10000)
        items = page.query_selector_all("div.offer__price")
        results = []
        for item in items:
            try:
                price_text = item.inner_text().strip()
                m = price_text.split(' ')[0]
                price = float(m.replace(",", "."))

                results.append(price)
            except Exception as e:
                continue

        browser.close()

    results = sorted(results)[:5]
    return results

def round_up_time(dt):
    dt += timedelta(minutes=30)
    if dt.minute < 30:
        dt = dt.replace(minute=30, second=0, microsecond=0)
    else:
        dt = dt.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    return dt

if __name__ == "__main__":
    while True:
        all_prices = {}
        now = datetime.now()
        rounded_time = round_up_time(now)
        time_str = urllib.parse.quote(rounded_time.strftime("%H:%M"))
        base_url = "https://www.parklot.pl/pl/parking-lotnisko-okecie/?od={od}&p={time}&do={do}&o={time}"
        today = datetime.today()
        od_str = today.strftime("%d.%m.%Y")
        urls = []
        for i in range(1, 32):
            date_to = today + timedelta(days=i)
            do_str = date_to.strftime("%d.%m.%Y")
            url = base_url.format(od=od_str, do=do_str, time=time_str)
            urls.append(url)
            top5 = parse_parklot_prices(url)
            all_prices[f"Day {i}"] = top5
        df = pd.DataFrame(all_prices)
        gc = gspread.service_account(filename="credentials.json")
        sh = gc.open_by_url('https://docs.google.com/spreadsheets/d/1P7DpfclEhIC7G7Eok_2xTglpQ2lF7Rmduc70oZTpnjs/edit?gid=1818324742#gid=1818324742')
        worksheet = sh.worksheet("Parklot")
        worksheet.clear()
        set_with_dataframe(worksheet, df)
        time.sleep(5400)
