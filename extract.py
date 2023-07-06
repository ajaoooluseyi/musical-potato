import csv
import time

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By


class CachedWebElement:
    def __init__(self, locator):
        self.locator = locator
        self.element = None

    def find_element(self, driver):
        if self.element is None or self.is_stale():
            self.element = driver.find_element(*self.locator)
        return self.element

    def is_stale(self):
        try:
            self.element.is_enabled()
            return False
        except StaleElementReferenceException:
            return True


# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument(
    "--headless"
)  # Run in headless mode to avoid opening a browser window

# Set up the Chrome driver
webdriver_service = Service(
    "path_to_chrome_driver"
)  # Replace 'path_to_chrome_driver' with the actual path to your Chrome driver executable
driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)

# Initialize CSV file and writer
csv_file = open("scraped_data.csv", "w", newline="", encoding="utf-8")
csv_writer = csv.writer(csv_file)
csv_writer.writerow(
    [
        "Product URL",
        "Product Name",
        "Product Price",
        "Rating",
        "Number of Reviews",
        "Description",
        "ASIN",
        "Product Description",
        "Manufacturer",
    ]
)

# Scrape multiple pages
pages_to_scrape = 20
# products_per_page = 10
target_product_count = 200
scraped_product_count = 0
base_url = "https://www.amazon.in/s?k=bags&crid=2M096C61O4MLT&qid=1653308124&sprefix=ba%2Caps%2C283&ref=sr_pg_{}"

for page in range(1, pages_to_scrape + 1):
    url = base_url.format(page)
    print(f"Scraping page {page}...")
    driver.get(url)
    time.sleep(2)  # Wait for the page to load

    # Find all product listings
    products = driver.find_elements(
        By.CSS_SELECTOR, 'div[data-component-type="s-search-result"]'
    )

    # Iterate over each product listing
    for product in products:
        # Check if the target product count is reached
        if scraped_product_count >= target_product_count:
            break

        # Wrap product elements with CachedWebElement
        product_url_element = CachedWebElement((By.CSS_SELECTOR, "h2 a"))
        product_name_element = CachedWebElement((By.CSS_SELECTOR, "h2 a span"))

        # Extract product information
        try:
            product_url = product_url_element.find_element(driver).get_attribute("href")
            product_name = product_name_element.find_element(driver).text
            product_price = product.find_element(By.CSS_SELECTOR, ".a-price-whole").text
            rating = product.find_element(
                By.CSS_SELECTOR, ".a-icon-star-small span"
            ).get_attribute("aria-label")
            num_reviews = product.find_element(
                By.CSS_SELECTOR, "span.a-size-base"
            ).text.split()[0]
        except NoSuchElementException:
            continue

        # Visit product URL to fetch additional details
        print(f"Visiting product URL: {product_url}")
        driver.get(product_url)
        time.sleep(2)  # Wait for the page to load

        # Extract additional details
        try:
            description = driver.find_element(
                By.CSS_SELECTOR, "#productDescription"
            ).text
        except NoSuchElementException:
            description = ""
        try:
            asin = driver.find_element(
                By.XPATH, '//th[text()="ASIN"]/following-sibling::td'
            ).text
        except NoSuchElementException:
            asin = ""
        try:
            product_description = driver.find_element(
                By.XPATH, '//th[text()="Product Dimensions"]/following-sibling::td'
            ).text
        except NoSuchElementException:
            product_description = ""
        try:
            manufacturer = driver.find_element(
                By.XPATH, '//th[text()="Manufacturer"]/following-sibling::td'
            ).text
        except NoSuchElementException:
            manufacturer = ""

        # Write data to CSV file
        csv_writer.writerow(
            [
                product_url,
                product_name,
                product_price,
                rating,
                num_reviews,
                description,
                asin,
                product_description,
                manufacturer,
            ]
        )

        # Increment the scraped product count
        scraped_product_count += 1

        print(f"Scraped product {scraped_product_count}/{target_product_count}")

    # Check if the target product count is reached
    if scraped_product_count >= target_product_count:
        break

# Close CSV file and browser
csv_file.close()
driver.quit()
