from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
import pandas as pd
import urllib.parse
import time
import gspread
from gspread_dataframe import set_with_dataframe

def parse_parklot_prices(url):
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        time.sleep(10)
        page.wait_for_selector("div.text-right.w-full", timeout=10000)
        items = page.query_selector_all("div.text-right.w-full")
        results = []
        for item in items:
            try:
                price_text = item.query_selector("span.font-bold").inner_text().strip()
                m = price_text.replace('\xa0zł','')
                price = float(m.replace(",", "."))

                results.append(price)
            except Exception as e:
                continue

        browser.close()

    results = sorted(results)[:5]
    return results



if __name__ == "__main__":
    while True:
        all_prices = {}
        base_url = "https://nextpark.pl/pl/parking-lotnisko-okecie/"

        now = datetime.now()
        minute = now.minute
        if minute < 30:
            rounded = now.replace(minute=0, second=0, microsecond=0)
        else:
            rounded = now.replace(minute=30, second=0, microsecond=0)
        arrival_dt = rounded + timedelta(minutes=30)
        for day_offset in range(1, 32):
            departure_dt = arrival_dt + timedelta(days=day_offset)
            url = f"{base_url}?arrival={arrival_dt.strftime('%Y%m%d%H%M')}&departure={departure_dt.strftime('%Y%m%d%H%M')}"
            top5 = parse_parklot_prices(url)
            all_prices[f"Day {day_offset}"] = top5

        df = pd.DataFrame(all_prices)
        gc = gspread.service_account(filename="credentials.json")
        sh = gc.open_by_url('https://docs.google.com/spreadsheets/d/1P7DpfclEhIC7G7Eok_2xTglpQ2lF7Rmduc70oZTpnjs/edit?gid=0#gid=0')
        worksheet = sh.worksheet("Nextpark")
        worksheet.clear()
        set_with_dataframe(worksheet, df)
        time.sleep(5400)