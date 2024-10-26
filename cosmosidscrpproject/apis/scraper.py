import asyncio
import aiohttp
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import StaleElementReferenceException, ElementClickInterceptedException, NoSuchElementException, TimeoutException
import time
import logging
import re
import os
from datetime import datetime
from django.db.utils import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from asgiref.sync import sync_to_async
from .models import CollectedLinks, ExportedResults, ScrapingJob
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(
    filename='scraper.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Selenium setup for scraping
chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080")

# Set download directory
DOWNLOAD_DIR = "/home/tlabib/Documents/github/cosmosid-scraper-api-zaag/downloads"
prefs = {
    "download.default_directory": DOWNLOAD_DIR,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
}
chrome_options.add_experimental_option("prefs", prefs)
service = Service('/usr/lib/chromium-browser/chromedriver')

# Asynchronous scraping function
async def start_scraping(get_sample_links, update_prev_links, job_id):
    scraper = Scraper(get_sample_links, update_prev_links, job_id)
    await scraper.run()

class Scraper:
    def __init__(self, get_sample_links, update_prev_links, job_id):
        self.session = None
        self.get_sample_links = get_sample_links
        self.update_prev_links = update_prev_links
        self.job_id = job_id
        self.max_workers = 2

    # async def update_job_status(self, status):
    #     """Update the scraping job status in the database."""
    #     try:
    #         await sync_to_async(ScrapingJob.objects.filter(job_id=self.job_id).update)(status=status)
    #     except Exception as e:
    #         logging.error(f"Error updating job status for job_id {self.job_id}: {e}")

    async def signin(self, driver):
        try:
            # Step 1: Open the website and log in
            driver.get("https://app.cosmosid.com/search")

            # Step 2: Close the new features dialog (first close button)
            close_button_1_xpath = "//button[@id='new-features-dialog--close']"
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, close_button_1_xpath)))
            driver.find_element(By.XPATH, close_button_1_xpath).click()

            # Step 3: Enter email and password
            email = "demo_estee2@cosmosid.com"
            password = "xyzfg321"

            # Wait for email field and fill in credentials
            email_field_xpath = "//input[@id='sign-in-form--email']"
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, email_field_xpath)))
            driver.find_element(By.XPATH, email_field_xpath).send_keys(email)

            password_field_xpath = "//input[@id='sign-in-form--password']"
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, password_field_xpath)))
            driver.find_element(By.XPATH, password_field_xpath).send_keys(password)

            # Step 4: Click the Sign In button
            sign_in_button_xpath = "//button[@id='sign-in-form--submit']"
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, sign_in_button_xpath)))
            driver.find_element(By.XPATH, sign_in_button_xpath).click()

            # Step 5: Close the second introduction pop-up (second close button)
            close_button_2_xpath = "//button[@id='intro-tour--functional-2-tour--close-button']"
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, close_button_2_xpath)))
            driver.find_element(By.XPATH, close_button_2_xpath).click()

            # Update job status after successful login
            await self.update_job_status("Signed In")
        except Exception as e:
            logging.error(f"Error during sign-in: {e}")
            await self.update_job_status("Sign In Failed")
        return driver

    async def get_sample_links(self, driver):
        try:
            # Step 6: Get all the links from the table
            table_links_xpath = "//table[@class='MuiTable-root MuiTable-stickyHeader css-1ia64a4']//a"
            WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, table_links_xpath)))
            links = driver.find_elements(By.XPATH, table_links_xpath)

            # Loop through each link, click on it, then return to the main page
            for i in range(len(links)):
                # Get the list of links again because the page refreshes after clicking
                links = driver.find_elements(By.XPATH, table_links_xpath)

                # Click the current link
                link = links[i]
                folder_name = link.text
                print("visiting", folder_name)
                link.click()

                # Wait for some time to allow the page to load
                time.sleep(1)

                # Step 7: Scroll and dynamically get all the sample links from the table
                sample_links_xpath = "//table[@class='MuiTable-root MuiTable-stickyHeader css-1ia64a4']//a"
                sample_links = []
                scroll_count = 0
                max_scroll_attempts = 5

                # Loop to scroll until all links are loaded
                while scroll_count < max_scroll_attempts:
                    current_links = driver.find_elements(By.XPATH, sample_links_xpath)

                    # Collecting the links with names and URLs as they're loaded
                    for link_element in current_links[len(sample_links):]:
                        try:
                            # Use innerHTML and outerHTML as intended
                            link_text = link_element.get_attribute("innerHTML")
                            link_outer_html = link_element.get_attribute("outerHTML")
                            # Use regex to find the href value in outerHTML
                            href_match = re.search(r'href="([^"]+)"', link_outer_html)
                            if href_match:
                                link_href = href_match.group(1)
                                link_info = {
                                    "name": link_text.strip(),
                                    "url": link_href,
                                    "folder": folder_name,
                                    "job_id": self.job_id
                                }
                                if not await sync_to_async(CollectedLinks.objects.filter(url=link_href).exists)():
                                    await self.upsert_collected_links(link_info)
                            else:
                                print(f"Could not find href in element: {link_outer_html}")

                        except Exception as e:
                            print("error")

                    # If no new links are found, increment scroll count
                    if len(current_links) == len(sample_links):
                        scroll_count += 1
                    else:
                        scroll_count = 0  # Reset scroll count if new links are found

                    # Update sample_links to the new list
                    sample_links = current_links

                    # Scroll the last element into view to load more links
                    if current_links:
                        ActionChains(driver).move_to_element(current_links[-1]).perform()
                        time.sleep(2)

                # # Print the collected links for debugging purposes
                # print([link["name"] for link in links_data])

                # Specific interaction after gathering sample links
                my_sample_xpath = "//a[@class='MuiTypography-root MuiTypography-inherit MuiLink-root MuiLink-underlineHover css-1u0d02q']"
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, my_sample_xpath)))
                driver.find_element(By.XPATH, my_sample_xpath).click()

                # Wait for the next page to load
                time.sleep(1)

        except Exception as e:
            logging.error(f"Error during sample link collection: {e}")
        return driver

    async def get_sample_data(self, driver):
        try:
            if not self.update_prev_links:
                collected_links = await sync_to_async(list)(CollectedLinks.objects.exclude(url__in=ExportedResults.objects.values_list('collected_link__url', flat=True)))
            else:
                collected_links = await sync_to_async(list)(CollectedLinks.objects.all())

            logging.info(f"collected links length : {len(collected_links)}")
            base_url = "https://app.cosmosid.com"

            for link in collected_links:
                full_url = base_url + link.url
                driver.get(full_url)
                time.sleep(4)

                try:
                    retry_attempts = 3
                    dropdown_loaded = False

                    # Retry to open the dropdown if necessary
                    for attempt in range(retry_attempts):
                        try:
                            # Locate the dropdown parent element
                            dropdown_parent_xpath = "//div[@id='analysis-select']"
                            dropdown_parent = WebDriverWait(driver, 15).until(
                                EC.element_to_be_clickable((By.XPATH, dropdown_parent_xpath))
                            )

                            # Click the dropdown using ActionChains
                            ActionChains(driver).move_to_element(dropdown_parent).click().perform()
                            time.sleep(2)  # Allow time for the dropdown to open

                            # Confirm that dropdown is now expanded
                            aria_expanded = dropdown_parent.get_attribute('aria-expanded')
                            if aria_expanded == "true":
                                logging.info("Dropdown opened successfully.")
                                dropdown_loaded = True
                                break
                            else:
                                raise Exception("Dropdown did not expand as expected.")

                        except (StaleElementReferenceException, ElementClickInterceptedException) as e:
                            logging.warning(f"Exception occurred on attempt {attempt + 1}. Retrying... Exception: {e}")
                            time.sleep(2)  # Wait before retrying

                    if not dropdown_loaded:
                        logging.error("Failed to load the dropdown after multiple attempts.")
                        continue

                    # Wait for the dropdown options to appear
                    try:
                        options_xpath = "//ul[@role='listbox']//li"
                        options = WebDriverWait(driver, 15).until(
                            EC.presence_of_all_elements_located((By.XPATH, options_xpath))
                        )
                        logging.info("Dropdown options loaded successfully.")

                        # Collect and log the option names
                        option_names = [option.get_attribute("data-value") if option else "Unknown Option" for option in options]
                        logging.info(f"Dropdown options collected: {option_names}")

                        # Iterate through each option in the dropdown
                        for i in range(len(options)):
                            if i != 0:
                                # Open the dropdown again
                                ActionChains(driver).move_to_element(dropdown_parent).click().perform()
                                time.sleep(2)  # Allow time for the dropdown to open

                            # Get the list of options again to avoid stale references
                            options = WebDriverWait(driver, 15).until(
                                EC.presence_of_all_elements_located((By.XPATH, options_xpath))
                            )

                            # Click on the option at index 'i'
                            option = options[i]
                            option_text = option.get_attribute("data-value") if option else "Unknown Option"
                            logging.info(f"{link.url} - Selecting option: {option_text}")

                            # Click the option using JavaScript to avoid StaleElement issues
                            driver.execute_script("arguments[0].click();", option)
                            time.sleep(1)  # Allow the page to update

                            # Click the "Export current results" button
                            export_button_xpath = "//button[contains(., 'Export current results')]"
                            try:
                                export_button = WebDriverWait(driver, 10).until(
                                    EC.element_to_be_clickable((By.XPATH, export_button_xpath))
                                )
                                # Scroll the button into view to ensure it is visible
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", export_button)
                                time.sleep(1)  # Allow some time for the scroll to complete

                                # Use JavaScript to click the button
                                driver.execute_script("arguments[0].click();", export_button)
                                logging.info(f"Clicked 'Export current results' for option: {option_text}")

                                # Wait for the download to complete
                                download_file = self.wait_for_download()
                                logging.info(f"Downloaded file: {download_file}")

                                # Save the export data
                                export_info = {
                                    "link_url": link.url,
                                    "result": option_text,
                                    "downloaded_file": download_file
                                }
                                logging.info(f"Exported Data: {export_info}")

                                # Save the data immediately after each download, appending to existing data
                                await self.export_results(link.url, option_text, "N/A", download_file)

                            except Exception as e:
                                logging.error(f"Failed to click 'Export current results': {e}")
                                await self.export_results(link.url, option_text, "N/A", None)

                            if option_text == "Bacteria":
                                logging.info("Expanding Bacteria")
                                # Click the "Taxonomy switcher" button after finding "Bacteria"
                                taxonomy_switcher_button_xpath = "//button[@id='artifact-select-button-kepler-biom' and @data-name='kepler-biom']"

                                try:
                                    taxonomy_button = WebDriverWait(driver, 10).until(
                                        EC.element_to_be_clickable((By.XPATH, taxonomy_switcher_button_xpath))
                                    )
                                    taxonomy_button.click()
                                    logging.info("Clicked 'Taxonomy switcher' for Bacteria.")
                                    time.sleep(2)  # Allow time for UI updates
                                    driver = await self.interact_with_level_dropdown(driver, link.url)
                                except Exception as e:
                                    logging.error(f"Failed to click 'Taxonomy switcher' button: {e}")

                    except Exception as e:
                        logging.error(f"Failed to load or interact with dropdown options: {e}")
                        continue

                except Exception as e:
                    logging.critical(f"An error occurred while interacting with the dropdown: {e}")

        except Exception as e:
            logging.critical(f"An error occurred during get_sample_data(): {e}")
        return driver

    async def handle_bacteria(self, driver, url):
        try:
            taxonomy_switcher_button_xpath = "//button[@id='artifact-select-button-kepler-biom' and @data-name='kepler-biom']"
            self.click_element(driver, taxonomy_switcher_button_xpath)
            time.sleep(2)

            driver = await self.interact_with_level_dropdown(driver, url)
        except Exception as e:
            logging.error(f"Failed to click 'Taxonomy switcher' button: {e}")
        return driver

    async def interact_with_level_dropdown(self, driver, lurl):
        try:
            # Locate the 'Level' dropdown parent element
            level_dropdown_xpath = "//div[@id='artifact-options-select' and text()='Species']"
            retry_attempts = 3
            dropdown_loaded = False

            # Retry mechanism for dropdown interaction
            for attempt in range(retry_attempts):
                try:
                    # Click to open the 'Level' dropdown
                    level_dropdown = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, level_dropdown_xpath))
                    )
                    ActionChains(driver).move_to_element(level_dropdown).click().perform()
                    time.sleep(2)  # Allow time for the dropdown to open

                    # Confirm the dropdown is now expanded
                    aria_expanded = level_dropdown.get_attribute('aria-expanded')
                    if aria_expanded == "true":
                        logging.info("Level dropdown opened successfully.")
                        dropdown_loaded = True
                        break
                    else:
                        raise Exception("Level dropdown did not expand as expected.")

                except (StaleElementReferenceException, ElementClickInterceptedException) as e:
                    logging.warning(f"Exception occurred on attempt {attempt + 1} while interacting with the 'Level' dropdown. Retrying... Exception: {e}")
                    time.sleep(2)

            if not dropdown_loaded:
                logging.error("Failed to load 'Level' dropdown after multiple attempts.")
                return

            # Wait for the dropdown options to appear
            level_options_xpath = "//ul[@role='listbox']//li"
            options = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, level_options_xpath))
            )
            logging.info("Level dropdown options loaded successfully.")

            # Collect and iterate through all available options
            level_names = [option.get_attribute("data-value") if option else "Unknown Option" for option in options]
            logging.info(f"Level dropdown options collected: {level_names}")

            # Loop through each level option and interact accordingly
            for i in range(len(options)):
                if i != 0:
                    # Open the dropdown again to ensure it's visible
                    ActionChains(driver).move_to_element(level_dropdown).click().perform()
                    time.sleep(2)  # Allow dropdown to open

                # Get list of options again to avoid stale references
                options = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, level_options_xpath))
                )

                # Select the current level option
                level_option = options[i]
                level_text = level_option.get_attribute("data-value") if level_option else "Unknown Option"
                logging.info(f"Selecting Level: {level_text}")

                # Click the option using JavaScript to avoid issues
                driver.execute_script("arguments[0].click();", level_option)
                time.sleep(1)  # Allow the page to update

                print(level_option, " selected")

                # Now, perform export for each level
                export_button_xpath = "//button[contains(., 'Export current results')]"
                try:
                    export_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, export_button_xpath))
                    )
                    # Scroll the button into view to ensure it is visible
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", export_button)
                    time.sleep(1)  # Allow some time for the scroll to complete

                    # Click the button to export current results
                    driver.execute_script("arguments[0].click();", export_button)
                    logging.info(f"Clicked 'Export current results' for Level: {level_text}")

                    # Wait for the download to complete
                    download_file = self.wait_for_download()
                    logging.info(f"Downloaded file: {download_file}")

                    # Save export information
                    export_info = {
                        "link_url": lurl,
                        "result": "Bacteria",
                        "taxonomy_level": level_text,
                        "downloaded_file": download_file
                    }
                    print(lurl, "Bacteria", level_text, download_file)

                    # Save the data immediately after each download, appending to existing data
                    await self.export_results(lurl, "Bacteria", level_text, download_file)

                except Exception as e:
                    # Save export information
                    export_info = {
                        "link_url": lurl,
                        "result": "Bacteria",
                        "taxonomy_level": level_text,
                        "downloaded_file": None
                    }
                    print(lurl, "Bacteria", level_text, None)

                    # Save the data immediately after each download, appending to existing data
                    await self.export_results(lurl, "Bacteria", level_text, None)
                    logging.error(f"Failed to click 'Export current results': {e}")

        except Exception as e:
            logging.error(f"An error occurred while interacting with the 'Level' dropdown: {e}")
        return driver

    async def export_results(self, url, result, taxonomy_level="N/A", downloaded_file=None):
        try:
            export_info = {
                "link_url": url,  # Keep it as the relative URL
                "result": result,
                "taxonomy_level": taxonomy_level,
                "downloaded_file": downloaded_file,
                "job_id": self.job_id
            }
            await self.upsert_exported_results(export_info)
        except Exception as e:
            logging.error(f"Failed to click 'Export current results': {e}")

    def wait_for_download(self, timeout=30):
        seconds = 0
        while seconds < timeout:
            time.sleep(1)
            files = os.listdir(DOWNLOAD_DIR)
            if files:
                sorted_files = sorted(files, key=lambda x: os.path.getmtime(os.path.join(DOWNLOAD_DIR, x)), reverse=True)
                newest_file = sorted_files[0]
                if newest_file.endswith(('.tsv', '.csv')):
                    return os.path.join(DOWNLOAD_DIR, newest_file)
            seconds += 1
        raise FileNotFoundError("No file was downloaded within the given time.")

    async def upsert_collected_links(self, link_info):
        try:
            await sync_to_async(CollectedLinks.objects.update_or_create)(url=link_info['url'], defaults={
                "name": link_info['name'],
                "folder": link_info['folder'],
                "job_id": link_info['job_id']
            })
        except IntegrityError as e:
            logging.error(f"Error upserting collected link: {e}")

    async def upsert_exported_results(self, export_info):
        try:
            logging.info(f"Upsert: Exported Data for Upsert: {export_info}")
            
            # Get the CollectedLinks instance using the relative URL
            collected_link_instance = await sync_to_async(CollectedLinks.objects.filter(url=export_info['link_url']).first)()
            
            # Check if there are any objects in CollectedLinks
            collected_links_count = await sync_to_async(CollectedLinks.objects.filter(url=export_info['link_url']).count)()
            if collected_links_count == 0:
                logging.error(f"No CollectedLinks objects found for URL: {export_info['link_url']}. Cannot proceed with export result.")
                return
            else:
                logging.info(f"CollectedLinks count for URL {export_info['link_url']}: {collected_links_count}")

            # Check if the collected_link_instance exists
            if not collected_link_instance:
                logging.error(f"No CollectedLinks found for URL: {export_info['link_url']}. Cannot proceed with export result.")
                return
            else:
                # Log all the attributes of the collected_link_instance
                collected_link_details = {
                    "name": collected_link_instance.name,
                    "url": collected_link_instance.url,
                    "folder": collected_link_instance.folder,
                    "job_id": collected_link_instance.job_id,
                }
                logging.info(f"CollectedLinks instance details: {collected_link_details}")

            # Get the ScrapingJob instance using the provided job_id
            scraping_job_instance = await sync_to_async(ScrapingJob.objects.get)(job_id=export_info['job_id'])
            
            # Use the correct instances in the upsert call
            await sync_to_async(ExportedResults.objects.update_or_create)(
                collected_link=collected_link_instance,
                url=export_info['link_url'],
                result=export_info['result'],
                taxonomy_level=export_info.get('taxonomy_level', 'N/A'),
                defaults={
                    "downloaded_file": export_info['downloaded_file'],
                    "job_id": scraping_job_instance  # Assign the actual ScrapingJob instance
                }
            )
        except ObjectDoesNotExist as e:
            logging.error(f"Error upserting exported result: {e}")
        except Exception as e:
            logging.error(f"Unexpected error during upsert: {e}")

    async def run(self):
        """
        Create a ThreadPoolExecutor to run multiple instances of Selenium WebDriver concurrently.
        """
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            loop = asyncio.get_event_loop()
            futures = [
                loop.run_in_executor(executor, self._run_scraper_instance)
                for _ in range(self.max_workers)
            ]
            await asyncio.gather(*futures)

    def _run_scraper_instance(self):
        """
        Run a single instance of the Selenium WebDriver to perform scraping tasks.
        This function runs inside its own thread.
        """
        driver = webdriver.Chrome(service=service, options=chrome_options)
        try:
            asyncio.run(self._perform_scraping(driver))
        except Exception as e:
            logging.error(f"Error during threaded scraping run: {e}")
        finally:
            driver.quit()

    async def _perform_scraping(self, driver):
        """
        Perform scraping tasks using the given driver instance.
        This includes login, link collection, and data scraping.
        """
        try:
            await self.update_job_status("Running")

            # Step 1: Sign in
            driver = await self.signin(driver)

            # Step 2: Collect sample links if applicable
            if self.get_sample_links:
                driver = await self.get_sample_links(driver)

            # Step 3: Scrape sample data
            driver = await self.get_sample_data(driver)

            # Update status to completed
            await self.update_job_status("Completed")
        except Exception as e:
            logging.error(f"Error during scraping tasks: {e}")
            await self.update_job_status("Failed")

    async def update_job_status(self, status):
        """Update the scraping job status in the database."""
        try:
            await sync_to_async(ScrapingJob.objects.filter(job_id=self.job_id).update)(status=status)
        except Exception as e:
            logging.error(f"Error updating job status for job_id {self.job_id}: {e}")
