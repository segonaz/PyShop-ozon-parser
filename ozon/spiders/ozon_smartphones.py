import json

import scrapy
import undetected_chromedriver as uc
from scrapy.http import HtmlResponse
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from ozon.items import OzonItem


class OzonSmartPhoneSpider(scrapy.Spider):
    product_count = 0
    total_product_count = 100
    page_number = 1
    name = "ozon_smartphones"
    allowed_domains = ["www.ozon.ru"]
    start_urls = ["https://www.ozon.ru/category/smartfony-15502/?sorting=rating"]
    handle_httpstatus_list = [403]

    def selenium_request(self, url, need_scroll=None):
        self.path = "./driver/chrome/chromedriver"
        options = uc.ChromeOptions()
        options.headless = True
        chrome_prefs = {}
        options.experimental_options["prefs"] = chrome_prefs
        chrome_prefs["profile.default_content_settings"] = {"images": 2}
        chrome_prefs["profile.managed_default_content_settings"] = {"images": 2}
        self.driver = uc.Chrome(options=options, use_subprocess=True, driver_executable_path=self.path)
        self.driver.get(url)

        if need_scroll:
            try:
                self.driver.execute_script("window.scrollTo(0,document.body.scrollHeight);")
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//span[text()='Операционная система']"))
                )
            except TimeoutException:
                return

        content = self.driver.page_source
        self.driver.quit()

        return HtmlResponse(url, encoding="utf-8", body=content)

    def convert_category_url_to_api(self, url):
        API_URL = "https://www.ozon.ru/api/composer-api.bx/page/json/v2?url="
        return f"{API_URL}{url}"

    def get_full_product_path(self, url):
        BASE_URL = "https://www.ozon.ru"
        return f"{BASE_URL}{url}"

    def start_requests(self):
        response = self.selenium_request(self.convert_category_url_to_api(self.start_urls[0]))
        yield scrapy.Request(
            url="https://example.com",
            callback=self.parse_page,
            meta={"ozon_data": response},
        )

    def parse_page(self, response: HtmlResponse):
        def find_items(data):
            for key, value in data["widgetStates"].items():
                if "searchResultsV2" in key:
                    return json.loads(value)

        def get_next_page_state(data):
            for key, value in data["widgetStates"].items():
                if "megaPaginator" in key:
                    next_page_data = json.loads(value)["nextPage"].split(";")
                    page_state = next_page_data[-1]
                    return page_state

        start_json_position = response.meta["ozon_data"].text.find("{")
        end_json_position = response.meta["ozon_data"].text.rfind("}")
        category_data = json.loads(response.meta["ozon_data"].text[start_json_position : end_json_position + 1])

        items = find_items(category_data)

        for item in items["items"]:
            if self.product_count >= self.total_product_count:
                break
            product_link = item["action"]["link"]
            product_page_data = self.selenium_request(url=self.get_full_product_path(product_link), need_scroll=True)
            if product_page_data:
                self.product_count += 1
                yield scrapy.Request(
                    url="https://example.com",
                    callback=self.parse_product,
                    meta={"ozon_data": product_page_data},
                    dont_filter=True,
                )

        if self.product_count >= self.total_product_count:
            return

        tf_state = get_next_page_state(category_data)
        if tf_state:
            self.page_number += 1
            url = f"{self.start_urls[0]}&page={self.page_number}&{tf_state}"
            response = self.selenium_request(self.convert_category_url_to_api(url))
            yield scrapy.Request(
                url="https://example.com",
                callback=self.parse_page,
                meta={"ozon_data": response},
                dont_filter=True,
            )
        return

    def parse_product(self, response: HtmlResponse):
        element = "//span[text()='Операционная система']/following::dd/a/text()"
        os_name = response.meta["ozon_data"].xpath(element).get()

        element = f"//span[text()='Версия {os_name}']/following::dd/a[contains(text(), '{os_name}')]/text()"
        os_version = response.meta["ozon_data"].xpath(element).get()

        if not os_version:
            element = f"//span[text()='Версия {os_name}']/following::dd[contains(text(), '{os_name}')]/text()"
            os_version = response.meta["ozon_data"].xpath(element).get()

        yield OzonItem(os_name=os_name, os_version=os_version)
