from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
import pandas as pd
import gspread
from gspread_dataframe import set_with_dataframe
import time

while True:
        
    base_url = "https://parkingi.pl/pl/parking_przy_lotnisku_chopina_warszawa_okecie.html?id_sort=lowest_price&data_from={from_date}&data_to={to_date}"

    today = datetime.today()

    all_prices = {}
    urls = []
    for i in range(1, 32):
        from_date = today.strftime("%Y-%m-%d")
        to_date = (today + timedelta(days=i)).strftime("%Y-%m-%d")
        url = base_url.format(from_date=from_date, to_date=to_date)
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url)

            while True:
                items = page.query_selector_all("li.card mb-4 border-0 overflow-hidden border-radius transition_anim_fast hover_list_pro shadow-3".replace(' ','.'))
                if len(items) >= 5:
                    break
                page.evaluate("window.scrollBy(0, 500)")
                page.wait_for_timeout(800)

            prices = []
            for item in items:
                price_el = item.query_selector(".text-danger.font-size-25 span")
                if not price_el:
                    price_el = item.query_selector(".font-weight-bold.text-dark.font-size-25")
                if price_el:
                    text = price_el.inner_text().replace("zł", "").replace(",", ".").strip()
                    try:
                        prices.append(float(text))
                    except ValueError:
                        pass

            top_5 = sorted(prices)[:5]
            all_prices[f"Day {i}"] = top_5

            browser.close()
    df = pd.DataFrame(all_prices)
    gc = gspread.service_account(filename="credentials.json")
    sh = gc.open_by_url('https://docs.google.com/spreadsheets/d/1P7DpfclEhIC7G7Eok_2xTglpQ2lF7Rmduc70oZTpnjs/edit?gid=1818324742#gid=1818324742')
    worksheet = sh.worksheet("Parkingi")
    worksheet.clear()
    set_with_dataframe(worksheet, df)
    time.sleep(5400)