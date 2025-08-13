"""
Actions Module - Human-like browser interactions
Provides safe wrappers for element interactions with anti-detection measures
"""

import time
import random
from typing import Optional, Union, Tuple
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException
import base64
from io import BytesIO
from PIL import Image


class BrowserActions:
    """Handles all browser interactions with human-like behavior"""
    
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
        
    def type_text(self, element: Union[str, WebElement], text: str, clear_first: bool = True) -> bool:
        """Type text with enhanced human-like behavior"""
        try:
            # Get element if string ID provided
            if isinstance(element, str):
                element = self._get_element(element)
            
            if not element:
                print(f"[ERROR] Element not found for typing")
                return False
            
            # Human-like approach to the element
            self._human_mouse_movement(element)
            
            # Scroll element into view
            self.scroll_to_element(element)
            time.sleep(random.uniform(0.5, 1.2))  # Longer pause like human reading
            
            # Click to focus with slight delay
            element.click()
            time.sleep(random.uniform(0.3, 0.7))
            
            # Clear if requested
            if clear_first and element.get_attribute('value'):
                if self._is_mobile():
                    # Mobile clear method
                    element.clear()
                else:
                    # Desktop clear with keyboard
                    element.send_keys(Keys.CONTROL + "a")
                    time.sleep(random.uniform(0.1, 0.3))
                    element.send_keys(Keys.DELETE)
                time.sleep(random.uniform(0.3, 0.6))
            
            # Enhanced human-like typing with mistakes and corrections
            self._type_like_human(element, text)
            
            print(f"[ACTION] Typed text: '{text[:30]}...'")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to type text: {e}")
            return False
    
    def click_element(self, element: Union[str, WebElement], use_js: bool = False) -> bool:
        """Click element with random offset"""
        try:
            # Get element if string ID provided
            if isinstance(element, str):
                element = self._get_element(element)
            
            if not element:
                print(f"[ERROR] Element not found for clicking")
                return False
            
            # Scroll element into view
            self.scroll_to_element(element)
            time.sleep(random.uniform(0.3, 0.6))
            
            if use_js or self._is_mobile():
                # Use JavaScript click for mobile or when requested
                self.driver.execute_script("arguments[0].click();", element)
            else:
                # Try regular click with offset
                try:
                    # Get element size
                    size = element.size
                    # Click with random offset from center
                    offset_x = random.randint(-size['width']//4, size['width']//4)
                    offset_y = random.randint(-size['height']//4, size['height']//4)
                    
                    from selenium.webdriver.common.action_chains import ActionChains
                    actions = ActionChains(self.driver)
                    actions.move_to_element_with_offset(element, offset_x, offset_y)
                    actions.click()
                    actions.perform()
                except:
                    # Fallback to simple click
                    element.click()
            
            print(f"[ACTION] Clicked element")
            time.sleep(random.uniform(0.5, 1.0))  # Wait after click
            return True
            
        except ElementNotInteractableException:
            # Try JavaScript click as fallback
            if not use_js:
                print("[WARN] Element not interactable, trying JS click")
                return self.click_element(element, use_js=True)
            print(f"[ERROR] Element not clickable")
            return False
        except Exception as e:
            print(f"[ERROR] Failed to click element: {e}")
            return False
    
    def scroll_page(self, direction: str = "down", amount: int = None) -> bool:
        """Scroll the page with human-like patterns"""
        try:
            # Add random micro-scrolls like humans do while reading
            if random.random() < 0.3:  # 30% chance of micro-scroll first
                micro_amount = random.randint(10, 50)
                self.driver.execute_script(f"window.scrollBy(0, {micro_amount});")
                time.sleep(random.uniform(0.1, 0.3))
            
            if direction == "down":
                if amount:
                    # Scroll specific amount with variation
                    actual_amount = amount + random.randint(-20, 20)
                    self.driver.execute_script(f"""
                        window.scrollBy({{
                            top: {actual_amount},
                            behavior: 'smooth'
                        }});
                    """)
                else:
                    # Variable scroll distance (like humans)
                    viewport_height = self.driver.execute_script("return window.innerHeight;")
                    scroll_factor = random.uniform(0.5, 0.9)  # Random amount
                    self.driver.execute_script(f"""
                        window.scrollBy({{
                            top: {viewport_height * scroll_factor},
                            behavior: 'smooth'
                        }});
                    """)
            elif direction == "up":
                if amount:
                    actual_amount = amount + random.randint(-20, 20)
                    self.driver.execute_script(f"""
                        window.scrollBy({{
                            top: -{actual_amount},
                            behavior: 'smooth'
                        }});
                    """)
                else:
                    viewport_height = self.driver.execute_script("return window.innerHeight;")
                    scroll_factor = random.uniform(0.3, 0.7)
                    self.driver.execute_script(f"""
                        window.scrollBy({{
                            top: -{viewport_height * scroll_factor},
                            behavior: 'smooth'
                        }});
                    """)
            elif direction == "top":
                self.driver.execute_script("window.scrollTo({top: 0, behavior: 'smooth'});")
            elif direction == "bottom":
                self.driver.execute_script("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'});")
            
            # Variable wait time after scroll
            time.sleep(random.uniform(0.3, 1.5))
            
            # Sometimes do a small correction scroll (human behavior)
            if random.random() < 0.2:  # 20% chance
                correction = random.randint(-30, 30)
                self.driver.execute_script(f"window.scrollBy(0, {correction});")
                time.sleep(random.uniform(0.2, 0.4))
            
            print(f"[ACTION] Scrolled {direction}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to scroll: {e}")
            return False
    
    def reading_scroll_pattern(self):
        """Simulate human reading pattern with scrolling"""
        try:
            # Small scrolls like reading line by line
            for _ in range(random.randint(2, 5)):
                scroll_amount = random.randint(50, 150)
                self.scroll_page("down", scroll_amount)
                time.sleep(random.uniform(1.0, 3.0))  # Reading time
                
                # Sometimes scroll back up a bit to re-read
                if random.random() < 0.15:
                    self.scroll_page("up", random.randint(20, 60))
                    time.sleep(random.uniform(0.5, 1.0))
            
            return True
        except:
            return False
    
    def scroll_to_element(self, element: Union[str, WebElement]) -> bool:
        """Scroll element into view"""
        try:
            # Get element if string ID provided
            if isinstance(element, str):
                element = self._get_element(element)
            
            if not element:
                return False
            
            # Scroll element to center of viewport
            self.driver.execute_script("""
                arguments[0].scrollIntoView({
                    behavior: 'smooth',
                    block: 'center',
                    inline: 'center'
                });
            """, element)
            
            time.sleep(random.uniform(0.3, 0.5))
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to scroll to element: {e}")
            return False
    
    def submit_form(self, element: Union[str, WebElement] = None) -> bool:
        """Submit a form (finds form if element provided)"""
        try:
            if element:
                # Get element if string ID provided
                if isinstance(element, str):
                    element = self._get_element(element)
                
                if element:
                    # Try to submit the form containing this element
                    element.submit()
            else:
                # Try to find and submit the first form
                form = self.driver.find_element(By.TAG_NAME, "form")
                form.submit()
            
            print("[ACTION] Submitted form")
            time.sleep(random.uniform(1.0, 2.0))  # Wait for submission
            return True
            
        except Exception as e:
            # Try pressing Enter as fallback
            try:
                if element:
                    element.send_keys(Keys.RETURN)
                    print("[ACTION] Submitted with Enter key")
                    time.sleep(random.uniform(1.0, 2.0))
                    return True
            except:
                pass
            
            print(f"[ERROR] Failed to submit form: {e}")
            return False
    
    def select_option(self, element: Union[str, WebElement], option: str, by: str = "text") -> bool:
        """Select option from dropdown"""
        try:
            # Get element if string ID provided
            if isinstance(element, str):
                element = self._get_element(element)
            
            if not element:
                print(f"[ERROR] Select element not found")
                return False
            
            # Scroll element into view
            self.scroll_to_element(element)
            time.sleep(random.uniform(0.3, 0.5))
            
            select = Select(element)
            
            if by == "text":
                select.select_by_visible_text(option)
            elif by == "value":
                select.select_by_value(option)
            elif by == "index":
                select.select_by_index(int(option))
            
            print(f"[ACTION] Selected option: {option}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to select option: {e}")
            return False
    
    def wait_for_element(self, selector: str, by: By = By.CSS_SELECTOR, timeout: int = 10) -> Optional[WebElement]:
        """Wait for element to be present and visible"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
            # Also wait for it to be visible
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of(element)
            )
            return element
        except TimeoutException:
            print(f"[WARN] Element not found: {selector}")
            return None
    
    def wait_for_page_load(self, timeout: int = 10) -> bool:
        """Wait for page to finish loading"""
        try:
            # Wait for document ready state
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # Additional wait for dynamic content
            time.sleep(random.uniform(0.5, 1.0))
            
            print("[ACTION] Page loaded")
            return True
        except TimeoutException:
            print("[WARN] Page load timeout")
            return False
    
    def go_back(self) -> bool:
        """Navigate back in browser history"""
        try:
            self.driver.back()
            time.sleep(random.uniform(1.0, 2.0))
            print("[ACTION] Navigated back")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to go back: {e}")
            return False
    
    def go_forward(self) -> bool:
        """Navigate forward in browser history"""
        try:
            self.driver.forward()
            time.sleep(random.uniform(1.0, 2.0))
            print("[ACTION] Navigated forward")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to go forward: {e}")
            return False
    
    def refresh_page(self) -> bool:
        """Refresh the current page"""
        try:
            self.driver.refresh()
            self.wait_for_page_load()
            print("[ACTION] Page refreshed")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to refresh: {e}")
            return False
    
    def take_screenshot(self, filename: str = None) -> str:
        """Take a screenshot and return base64 encoded image"""
        try:
            if filename:
                self.driver.save_screenshot(filename)
                print(f"[ACTION] Screenshot saved to {filename}")
                with open(filename, "rb") as f:
                    return base64.b64encode(f.read()).decode()
            else:
                # Return base64 encoded screenshot
                png = self.driver.get_screenshot_as_png()
                print("[ACTION] Screenshot captured")
                return base64.b64encode(png).decode()
        except Exception as e:
            print(f"[ERROR] Failed to take screenshot: {e}")
            return ""
    
    def get_current_url(self) -> str:
        """Get current page URL"""
        return self.driver.current_url
    
    def get_page_title(self) -> str:
        """Get current page title"""
        return self.driver.title
    
    def _get_element(self, identifier: str) -> Optional[WebElement]:
        """Get element by various methods"""
        try:
            # Try ID first
            if identifier.startswith("#"):
                return self.driver.find_element(By.ID, identifier[1:])
            # Try class
            elif identifier.startswith("."):
                return self.driver.find_element(By.CLASS_NAME, identifier[1:])
            # Try CSS selector
            elif " " in identifier or ">" in identifier or "[" in identifier:
                return self.driver.find_element(By.CSS_SELECTOR, identifier)
            # Default to ID
            else:
                return self.driver.find_element(By.ID, identifier)
        except:
            return None
    
    def _human_mouse_movement(self, element):
        """Simulate human-like mouse movement to element"""
        if not self._is_mobile():
            try:
                from selenium.webdriver.common.action_chains import ActionChains
                actions = ActionChains(self.driver)
                
                # Get element location
                location = element.location
                size = element.size
                
                # Random approach path (not direct)
                intermediate_x = location['x'] + random.randint(-50, 50)
                intermediate_y = location['y'] + random.randint(-50, 50)
                
                # Move to intermediate point first
                actions.move_by_offset(intermediate_x, intermediate_y)
                actions.pause(random.uniform(0.1, 0.3))
                
                # Then to the element
                target_x = location['x'] + size['width']//2 + random.randint(-5, 5)
                target_y = location['y'] + size['height']//2 + random.randint(-5, 5)
                actions.move_by_offset(target_x - intermediate_x, target_y - intermediate_y)
                actions.perform()
                
                time.sleep(random.uniform(0.1, 0.3))
            except:
                pass  # Fallback silently
    
    def _type_like_human(self, element, text):
        """Type text with human-like patterns including occasional mistakes"""
        words = text.split(' ')
        
        for i, word in enumerate(words):
            # Occasionally make a typo and correct it
            if len(word) > 3 and random.random() < 0.05:  # 5% chance of typo
                # Type wrong character
                wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz')
                element.send_keys(word + wrong_char)
                time.sleep(random.uniform(0.2, 0.4))
                
                # Realize mistake, backspace
                element.send_keys(Keys.BACKSPACE)
                time.sleep(random.uniform(0.1, 0.2))
                element.send_keys(Keys.BACKSPACE)  # Remove the wrong char and last char
                time.sleep(random.uniform(0.1, 0.2))
                
                # Type correct ending
                element.send_keys(word[-1])
                time.sleep(random.uniform(0.1, 0.2))
            else:
                # Type normally with variable speed
                for char in word:
                    element.send_keys(char)
                    # Realistic typing rhythm
                    if char in 'aeiou':  # Vowels typed slightly faster
                        time.sleep(random.uniform(0.08, 0.12))
                    else:
                        time.sleep(random.uniform(0.12, 0.18))
                    
                    # Occasional longer pause (thinking)
                    if random.random() < 0.03:
                        time.sleep(random.uniform(0.3, 0.8))
            
            # Add space between words
            if i < len(words) - 1:
                element.send_keys(' ')
                time.sleep(random.uniform(0.15, 0.25))
                
                # Occasional pause between words (reading/thinking)
                if random.random() < 0.1:
                    time.sleep(random.uniform(0.5, 1.2))

    def _is_mobile(self) -> bool:
        """Check if running in mobile mode"""
        user_agent = self.driver.execute_script("return navigator.userAgent;")
        return "Mobile" in user_agent or "Android" in user_agent or "iPhone" in user_agent
    
    def hover_element(self, element: Union[str, WebElement]) -> bool:
        """Hover over an element"""
        try:
            # Get element if string ID provided
            if isinstance(element, str):
                element = self._get_element(element)
            
            if not element:
                return False
            
            # Scroll element into view
            self.scroll_to_element(element)
            
            if self._is_mobile():
                # Mobile doesn't have hover, just highlight it
                self.driver.execute_script("""
                    arguments[0].style.backgroundColor = 'yellow';
                    setTimeout(() => {
                        arguments[0].style.backgroundColor = '';
                    }, 1000);
                """, element)
            else:
                from selenium.webdriver.common.action_chains import ActionChains
                actions = ActionChains(self.driver)
                actions.move_to_element(element)
                actions.perform()
            
            time.sleep(random.uniform(0.3, 0.5))
            print("[ACTION] Hovered over element")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to hover: {e}")
            return False