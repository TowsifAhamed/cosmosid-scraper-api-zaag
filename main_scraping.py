from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import StaleElementReferenceException, ElementClickInterceptedException
import time
import json
import re
import logging
import os
from datetime import datetime

logging.basicConfig(
    filename='scraper.log',  # Specify the filename for the log file
    level=logging.INFO,       # Set the logging level to INFO
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080")

# Set download directory
download_dir = "/home/tlabib/Documents/github/cosmosid-scraper-api-zaag/downloads"  # Replace with your desired download directory path
prefs = {
    "download.default_directory": download_dir,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
}
chrome_options.add_experimental_option("prefs", prefs)

# Set up the Chrome driver with these options
service = Service('/usr/lib/chromium-browser/chromedriver')
driver = webdriver.Chrome(service=service, options=chrome_options)

# To store the collected links and export results
links_data = []
exported_data = []

def signin():        
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

    except Exception as e:
        print(f"An error occurred: {e}")

def get_sample_links(get_samples):
    if get_samples:
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
                                    "name": link_text.strip(),  # Removing unnecessary whitespace
                                    "url": link_href,
                                    "folder": folder_name
                                }
                                print(link_text.strip(), href_match.group(1), folder_name)
                                if link_info not in links_data:
                                    links_data.append(link_info)
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
            
            # Save collected links to a JSON file
            with open('collected_links.json', 'w') as json_file:
                json.dump(links_data, json_file, indent=4)

        except Exception as e:
            print(f"An error occurred: {e}")

def save_export_data(new_data):
    """
    Save new export data by appending to existing data in the JSON file.
    
    Parameters:
        new_data (dict): New data to append.
    """
    # Load existing data if the file exists
    if os.path.exists('exported_results.json'):
        with open('exported_results.json', 'r') as json_file:
            try:
                exported_data = json.load(json_file)
            except json.JSONDecodeError:
                exported_data = []
    else:
        exported_data = []

    # Append new data
    exported_data.append(new_data)

    # Save the updated data back to the JSON file
    with open('exported_results.json', 'w') as json_file:
        json.dump(exported_data, json_file, indent=4)

# Function to interact with the 'Level' dropdown
def interact_with_level_dropdown(driver, lurl):
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
                download_file = wait_for_download(download_dir)
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
                save_export_data(export_info)

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
                save_export_data(export_info)
                logging.error(f"Failed to click 'Export current results': {e}")

    except Exception as e:
        logging.error(f"An error occurred while interacting with the 'Level' dropdown: {e}")

# Function to get sample data using the collected links and interact with the dropdown
def get_sample_data(update_prev_links):
    base_url = "https://app.cosmosid.com"

    # Load the collected links data from the JSON file
    with open('collected_links.json', 'r') as json_file:
        collected_links = json.load(json_file)

    print("collected links length : ", len(collected_links))

    if update_prev_links == False:
        # Load the already scraped links from the exported_results.json file
        if os.path.exists('exported_results.json'):
            with open('exported_results.json', 'r') as json_file:
                try:
                    scraped_data = json.load(json_file)
                except json.JSONDecodeError:
                    scraped_data = []
        else:
            scraped_data = []

        # Create a set of already scraped URLs to easily check if a link has been processed
        scraped_urls = set()
        for data in scraped_data:
            scraped_urls.add(data['link_url'])

        # Remove already scraped links from collected_links
        collected_links = [link for link in collected_links if link['url'] not in scraped_urls]

    print("collected links length : ", len(collected_links))

    try:
        for link in collected_links:
            full_url = base_url + link['url']
            logging.info(f"Opening URL: {full_url}")
            driver.get(full_url)

            # Wait for the page to load completely
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
                        logging.info(f"Selecting option: {option_text}")

                        # Click the option using JavaScript to avoid StaleElement issues
                        driver.execute_script("arguments[0].click();", option)
                        time.sleep(1)  # Allow the page to update
                        print(link['url'], option_text)

                        # Click the "Export current results" button
                        export_button_xpath_variants = [
                            "//button[contains(., 'Export current results')]",  # General text match for button
                            # "//button[contains(@class, 'MuiButton-root') and contains(text(), 'Export current results')]",  # Match using button class
                            # "//button[.//span[contains(text(),'Export current results')]]",  # Match span with text inside the button
                        ]

                        export_button = None

                        # Iterate through different possible XPaths to locate the export button
                        for xpath in export_button_xpath_variants:
                            try:
                                export_button = WebDriverWait(driver, 5).until(
                                    EC.element_to_be_clickable((By.XPATH, xpath))
                                )
                                # If we find the export button using any XPath, break out of the loop
                                if export_button:
                                    # print(xpath)
                                    logging.info(f"Export button found using XPath: {xpath}")
                                    break
                            except Exception as e:
                                logging.warning(f"Couldn't locate export button with XPath: {xpath} - {e}")

                        # Proceed if the export button was found
                        if export_button:
                            try:
                                # Scroll the button into view to ensure it is visible
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", export_button)
                                time.sleep(1)  # Allow some time for the scroll to complete

                                # Use JavaScript to click the button
                                driver.execute_script("arguments[0].click();", export_button)
                                logging.info(f"Clicked 'Export current results' for option: {option_text}")

                                # Wait for the download to complete
                                download_file = wait_for_download(download_dir)
                                logging.info(f"Downloaded file: {download_file}")

                                # Save the export data
                                export_info = {
                                    "link_url": link['url'],
                                    "result": option_text,
                                    "downloaded_file": download_file
                                }
                                print(link['url'], option_text, download_file)

                                # Save the data immediately after each download, appending to existing data
                                save_export_data(export_info)

                            except Exception as e:
                                logging.error(f"Failed to click 'Export current results': {e}")

                        else:
                            # Save the export data
                            export_info = {
                                "link_url": link['url'],
                                "result": option_text,
                                "downloaded_file": None
                            }
                            print(link['url'], option_text, None)

                            # Save the data immediately after each download, appending to existing data
                            save_export_data(export_info)
                            logging.error("Failed to locate the 'Export current results' button with any of the provided XPaths.")

                        if (option_text=="Bacteria"):
                            print("expanding bacteria")
                            # Click the "Taxonomy switcher" button after finding "Bacteria"
                            taxonomy_switcher_button_xpath = "//button[@id='artifact-select-button-kepler-biom' and @data-name='kepler-biom']"

                            try:
                                taxonomy_button = WebDriverWait(driver, 10).until(
                                    EC.element_to_be_clickable((By.XPATH, taxonomy_switcher_button_xpath))
                                )
                                taxonomy_button.click()
                                logging.info("Clicked 'Taxonomy switcher' for Bacteria.")
                                time.sleep(2)  # Allow time for UI updates
                                interact_with_level_dropdown(driver, link["url"])
                            except Exception as e:
                                logging.error(f"Failed to click 'Taxonomy switcher' button: {e}")
                                
                except Exception as e:
                    logging.error(f"Failed to load or interact with dropdown options: {e}")
                    continue

            except Exception as e:
                logging.critical(f"An error occurred while interacting with the dropdown: {e}")

    except Exception as e:
        logging.critical(f"An error occurred during get_sample_data(): {e}")

    # # Save the exported data to a JSON file
    # with open('exported_results.json', 'w') as json_file:
    #     json.dump(exported_data, json_file, indent=4)

def wait_for_download(download_dir, timeout=30):
    """
    Waits for a new file to be downloaded in the specified directory.
    
    Parameters:
        download_dir (str): The directory to watch for new downloads.
        timeout (int): Time in seconds to wait for the file to appear.

    Returns:
        str: The path to the downloaded file.
    """
    seconds = 0
    while seconds < timeout:
        time.sleep(1)
        files = os.listdir(download_dir)
        if files:
            # Sort files by modified time in descending order
            sorted_files = sorted(files, key=lambda x: os.path.getmtime(os.path.join(download_dir, x)), reverse=True)
            newest_file = sorted_files[0]
            if newest_file.endswith(('.tsv', '.csv')):  # Modify file extensions if needed
                return os.path.join(download_dir, newest_file)
        seconds += 1
    raise FileNotFoundError("No file was downloaded within the given time.")

# Execution sequence
config = {}
config["get_samples"] = False
config["update_prev_links"] = False
signin()
get_sample_links(config["get_samples"])
get_sample_data(config["update_prev_links"])
# Close the browser
input("Press Enter to close the browser...")
driver.quit()