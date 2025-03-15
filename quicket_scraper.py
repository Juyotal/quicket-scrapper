#!/usr/bin/env python3
"""
Quicket Event Scraper

This script scrapes event information from Quicket's events page and saves it to a CSV file.
"""

import time
import random
import logging
import re
import pandas as pd
import os
import shutil

from typing import List, Dict, Any

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


XPATHS = {
    'event_item': "//div[contains(@class, 'l-event-list')]//li[contains(@class, 'l-event-item')]",
    'event_title': ".//div[contains(@class, 'l-event-content')]//div[contains(@class, 'l-hit-name')]",
    'event_location': ".//div[contains(@class, 'l-event-content')]//div[contains(@class, 'l-hit-venue')]",
    'event_date_time': ".//div[contains(@class, 'l-event-content')]//div[contains(@class, 'l-date-container')]",
    'next_page': "//a[@class='ais-Pagination-link' and contains(text(), '›')]",
    'page_number': "//a[@class='ais-Pagination-link' and contains(text(), '{0}')]",
    'cookie_consent': "//button[contains(@class, 'cookie-consent-accept') or contains(text(), 'Accept') or contains(text(), 'I agree')]",
}

class QuicketScraper:
    """Scraper for Quicket events page."""
    
    def __init__(self, max_pages: int = 10, headless: bool = True):
        """
        Initialize the scraper.
        
        Args:
            base_url: The base URL to scrape
            max_pages: Maximum number of pages to scrape
            headless: Whether to run the browser in headless mode
        """
        self.base_url = "https://www.quicket.co.za/events/"
        self.max_pages = max_pages
        self.headless = headless
        self.current_page = 1
        self.events_data = []
        self.driver = None
        self.first_page_event = None

    def setup_driver(self):
        """Set up the Selenium WebDriver."""
        logger.info("Setting up Chrome WebDriver...")
        chrome_options = Options()
        
        if self.headless:
            logger.info("Running in headless mode")
            chrome_options.add_argument("--headless")
        else:
            logger.info("Running in visible mode")
            
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Add user agent to avoid detection
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.implicitly_wait(15)
        
    def close_driver(self):
        """Close the WebDriver."""
        if self.driver:
            logger.info("Closing WebDriver...")
            self.driver.quit()

    def handle_cookie_consent(self):
        """Handle cookie consent dialog if it appears."""
        try:
           
            cookie_buttons = WebDriverWait(self.driver, 5).until(
                EC.presence_of_all_elements_located((By.XPATH, XPATHS['cookie_consent']))
            )
            
            if cookie_buttons:
                logger.info("Cookie consent dialog found, accepting cookies")
                cookie_buttons[0].click()
                time.sleep(1)  # Wait for the dialog to disappear
        except (TimeoutException, NoSuchElementException):
            logger.info("No cookie consent dialog found or it has already been accepted")
        except Exception as e:
            logger.warning(f"Error handling cookie consent: {e}")

    def _element_has_changed(self, current_event_id):
        try:
            new_first_event = self.driver.find_element(By.XPATH, XPATHS['event_item'])
            new_event_id = new_first_event.get_attribute("innerHTML")
            return new_event_id != current_event_id
        except (NoSuchElementException, StaleElementReferenceException):
            # If we can't find the element or it's stale, the page is probably changing
            return True
    
    def wait_for_page_load(self):
        """
        Wait for a page to load, optionally waiting for a reference element to become stale first.

        Args:
            reference_element: Element that should become stale during page transition

        Returns:
            bool: True if the page loaded successfully
        """

        def page_has_changed(driver):
            try:
                new_first_event = driver.find_element(By.XPATH, XPATHS['event_item'])
                return new_first_event != self.first_page_event
            except (NoSuchElementException, StaleElementReferenceException):
                return True
        try:
            WebDriverWait(self.driver, 10).until(
                page_has_changed
            )
            
            return True
        except TimeoutException:
            logger.warning("Timed out waiting for page to load")
            self.driver.save_screenshot(f"error_screenshots/timeout_page_{self.current_page}.png")
            return False

    def safe_click(self, element):
        """
        Safely click an element, handling any intercepted clicks.

        Args:
            element: WebElement to click
            
        Returns:
            bool: True if click was successful
        """
        try:
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.5)
            
            # Try regular click first
            try:
                element.click()
            except ElementClickInterceptedException:
                # Fall back to JavaScript click
                logger.info("Click intercepted, trying JavaScript click")
                self.driver.execute_script("arguments[0].click();", element)
                
            return True
        except Exception as e:
            logger.exception(f"Error clicking element: {e}")
            return False

    def navigate_to_page(self, page_number: int) -> bool:
        """
        Navigate to a specific page number.

        Args:
            page_number: The page number to navigate to
            
        Returns:
            bool: True if navigation was successful, False otherwise
        """
        if self.current_page == page_number:
            return True
            
        try:
            page_xpath = XPATHS['page_number'].format(page_number)
            page_links = self.driver.find_elements(By.XPATH, page_xpath)
            
            if not page_links:
                logger.warning(f"Page {page_number} link not found")
                return False
            
            if not self.safe_click(page_links[0]):
                return False
                
            if not self.wait_for_page_load():
                return False
            
            self.current_page = page_number
            return True
            
        except Exception as e:
            logger.exception(f"Error navigating to page {page_number}: {e}")
            return False
            
    def navigate_to_next_page(self) -> bool:
        """
        Navigate to the next page using the next button.

        Returns:
            bool: True if navigation was successful, False otherwise
        """
        try:
            next_buttons = self.driver.find_elements(By.XPATH, XPATHS['next_page'])
            
            if not next_buttons:
                logger.info("No more pages available")
                return False
                
            next_button = next_buttons[0]
            if not next_button.is_enabled():
                logger.info("Next page button is disabled")
                return False
            
            if not self.safe_click(next_button):
                return False
                
            if not self.wait_for_page_load():
                return False
            
            self.current_page += 1
            return True
            
        except Exception as e:
            logger.exception(f"Error navigating to next page: {e}")
            self.driver.save_screenshot(f"error_screenshots/error_next_page_{self.current_page}.png")
            return False

    def scrape_events(self):
        """Scrape events from Quicket."""
        try:
            self.setup_driver()
            self.current_page = 1
            
            logger.info(f"Navigating to {self.base_url}")
            self.driver.get(self.base_url)

            self.handle_cookie_consent()
            
            # Wait for the initial page to load
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.XPATH, XPATHS['event_item']))
            )
            
            while self.current_page <= self.max_pages:
                logger.info(f"Scraping page {self.current_page} of {self.max_pages}")
                
                # we store the first event on the page to later check if the page has changed
                self.first_page_event = self.driver.find_element(By.XPATH, XPATHS['event_item'])

                page_events = self._extract_events_from_page_with_retry()
                self.events_data.extend(page_events)
                
                # Rate limiting - random delay between 1-3 seconds
                delay = random.uniform(1, 3)
                logger.info(f"Rate limiting: waiting for {delay:.2f} seconds")
                time.sleep(delay)
                
                if self.current_page >= self.max_pages:
                    break
                
                next_page = self.current_page + 1
                if not self.navigate_to_page(next_page):
                    logger.warning(f"Failed to navigate to page {next_page}, trying next button")
                    
                    # Try using the next page button as a fallback
                    if not self.navigate_to_next_page():
                        logger.info("Could not navigate to next page, ending scrape")
                        break
                    
            logger.info(f"Scraped a total of {len(self.events_data)} events")
            return self.events_data
            
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            if self.driver:
                self.driver.save_screenshot(f"error_screenshots/error_screenshot.png")
                logger.error(f"Page source at error: {self.driver.page_source[:1000]}...")
            raise
        finally:
            self.close_driver()
    
    def _extract_events_from_page_with_retry(self) -> List[Dict[str, Any]]:
        """
        Extract events from the current page with retry logic.
        
        Returns:
            List of dictionaries containing event information
        """
        retries = 0
        max_retries = 3
        while retries < max_retries:
            try:
                return self._extract_events_from_page()
            except Exception as e:
                retries += 1
                logger.warning(f"Error extracting events (attempt {retries}/{max_retries}): {e}")
                
                if retries >= max_retries:
                    logger.error(f"Failed to extract events after {max_retries} attempts")
                    return []
                
                # Reload the page and try again
                logger.info(f"Reloading page {self.current_page} and retrying...")
                self.driver.refresh()
                self.navigate_to_page(self.current_page)
                time.sleep(2)
        
        return []
            
    def _extract_events_from_page(self) -> List[Dict[str, Any]]:
        """
        Extract events from the current page using BeautifulSoup.
        
        Returns:
            List of dictionaries containing event information
        """
        page_events = []
        
        page_source = self.driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        event_list = soup.select('div.l-event-list li.l-event-item')
        logger.info(f"Found {len(event_list)} events on page {self.current_page}")
        
        for event in event_list:
            try:
                title_element = event.select_one('div.l-event-content div.l-hit-name')
                title = title_element.text.strip() if title_element else "Not specified"
                
                location_element = event.select_one('div.l-event-content div.l-hit-venue')
                location = location_element.text.strip() if location_element else "Not specified"
                
                date_time_element = event.select_one('div.l-event-content div.l-date-container')
                date_time_text = date_time_element.text.strip() if date_time_element else ""
                
                date, time_info = self._parse_date_time(date_time_text)
                
                event_data = {
                    'title': title,
                    'location': location,
                    'date': date,
                    'time': time_info
                }
                
                page_events.append(event_data)
                logger.debug(f"Extracted event: {event_data}")
                
            except Exception as e:
                logger.warning(f"Error extracting event data: {e}")
                continue
                
        return page_events
    
    def _parse_date_time(self, date_time_text: str) -> tuple:
        """
        Parse date and time from the combined text.
        
        Args:
            date_time_text: The combined date and time text
            
        Returns:
            Tuple of (date, time)
        """
        date = ""
        time_info = ""
        
        try:
            
            # Look for date format like "Friday, March 14, 2025"
            date_pattern = r'([A-Za-z]+,\s+[A-Za-z]+\s+\d{1,2},\s+\d{4})'
            time_pattern = r'(\d{1,2}:\d{2}(?:\s*[AP]M)?)'
            
            if not date:
                date_match = re.search(date_pattern, date_time_text)
                if date_match:
                    date = date_match.group(1).strip()
            
            if not time_info:
                time_match = re.search(time_pattern, date_time_text)
                if time_match:
                    time_info = time_match.group(1).strip()
                    
        except Exception as e:
            logger.warning(f"Error parsing date and time: {e}")
            
        return date, time_info
        
    def save_to_csv(self, filename: str = "quicket_events.csv"):
        """
        Save the scraped data to a CSV file.
        
        Args:
            filename: Name of the CSV file
        """
        if not self.events_data:
            logger.warning("No data to save")
            return
            
        try:
            df = pd.DataFrame(self.events_data)
            df.to_csv(filename, index=False)
            logger.info(f"Data saved to {filename}")
            logger.info(f"Sample data:\n{df.head()}")
        except Exception as e:
            logger.error(f"Error saving data to CSV: {e}")
            raise
