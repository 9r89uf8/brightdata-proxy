"""
DOM Extractor Module - Simplifies web pages for Claude AI analysis
Extracts interactive elements and important content while minimizing tokens
"""

from typing import Dict, List, Any, Optional
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
import json
import re


class DOMExtractor:
    """Extracts and simplifies DOM for AI analysis"""
    
    def __init__(self, driver):
        self.driver = driver
        self.element_counter = 0
        self.element_map = {}  # Maps element IDs to actual WebElements
    
    def extract_page_info(self) -> Dict[str, Any]:
        """Extract simplified page information for Claude"""
        
        # Reset counters
        self.element_counter = 0
        self.element_map = {}
        
        page_info = {
            "url": self.driver.current_url,
            "title": self.driver.title,
            "viewport": self._get_viewport_info(),
            "elements": self._extract_interactive_elements(),
            "text_content": self._extract_important_text(),
            "scroll_position": self._get_scroll_position()
        }
        
        return page_info
    
    def _get_viewport_info(self) -> Dict[str, int]:
        """Get viewport dimensions and scroll info"""
        return self.driver.execute_script("""
            return {
                width: window.innerWidth,
                height: window.innerHeight,
                scrollHeight: document.documentElement.scrollHeight,
                scrollWidth: document.documentElement.scrollWidth
            };
        """)
    
    def _get_scroll_position(self) -> Dict[str, int]:
        """Get current scroll position"""
        return self.driver.execute_script("""
            return {
                x: window.pageXOffset || document.documentElement.scrollLeft,
                y: window.pageYOffset || document.documentElement.scrollTop
            };
        """)
    
    def _extract_interactive_elements(self) -> List[Dict[str, Any]]:
        """Extract clickable and interactive elements"""
        elements = []
        
        # Extract search boxes and input fields
        inputs = self._extract_inputs()
        elements.extend(inputs)
        
        # Extract clickable links
        links = self._extract_links()
        elements.extend(links)
        
        # Extract buttons
        buttons = self._extract_buttons()
        elements.extend(buttons)
        
        # Extract select dropdowns
        selects = self._extract_selects()
        elements.extend(selects)
        
        return elements
    
    def _extract_inputs(self) -> List[Dict[str, Any]]:
        """Extract input fields"""
        inputs = []
        
        # Use JavaScript to get all visible input fields
        input_data = self.driver.execute_script("""
            const inputs = [];
            const elements = document.querySelectorAll('input, textarea');
            
            elements.forEach(el => {
                const rect = el.getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0 && 
                    el.offsetParent !== null &&
                    el.type !== 'hidden') {
                    inputs.push({
                        tag: el.tagName.toLowerCase(),
                        type: el.type || 'text',
                        name: el.name || '',
                        id: el.id || '',
                        placeholder: el.placeholder || '',
                        value: el.value || '',
                        ariaLabel: el.getAttribute('aria-label') || '',
                        className: el.className || '',
                        rect: {
                            x: rect.x,
                            y: rect.y,
                            width: rect.width,
                            height: rect.height
                        }
                    });
                }
            });
            
            return inputs;
        """)
        
        for input_info in input_data:
            element_id = f"input_{self.element_counter}"
            self.element_counter += 1
            
            # Find the actual element for mapping
            if input_info['id']:
                element = self.driver.find_element(By.ID, input_info['id'])
            elif input_info['name']:
                element = self.driver.find_element(By.NAME, input_info['name'])
            else:
                # Use XPath with multiple attributes
                xpath = f"//{input_info['tag']}"
                if input_info['type']:
                    xpath += f"[@type='{input_info['type']}']"
                if input_info['placeholder']:
                    xpath += f"[@placeholder='{input_info['placeholder']}']"
                try:
                    element = self.driver.find_element(By.XPATH, xpath)
                except:
                    continue
            
            self.element_map[element_id] = element
            
            # Determine input purpose
            purpose = self._determine_input_purpose(input_info)
            
            inputs.append({
                "element_id": element_id,
                "type": "input",
                "input_type": input_info['type'],
                "purpose": purpose,
                "placeholder": input_info['placeholder'],
                "current_value": input_info['value'],
                "label": input_info['ariaLabel'] or input_info['placeholder'],
                "position": input_info['rect']
            })
        
        return inputs
    
    def _determine_input_purpose(self, input_info: Dict) -> str:
        """Determine the likely purpose of an input field"""
        combined = f"{input_info['name']} {input_info['id']} {input_info['placeholder']} {input_info['ariaLabel']}".lower()
        
        if 'search' in combined or 'query' in combined or 'q' == input_info['name']:
            return "search"
        elif 'email' in combined:
            return "email"
        elif 'password' in combined or input_info['type'] == 'password':
            return "password"
        elif 'user' in combined or 'login' in combined:
            return "username"
        elif 'phone' in combined or 'tel' in combined:
            return "phone"
        else:
            return "text"
    
    def _extract_links(self) -> List[Dict[str, Any]]:
        """Extract visible links"""
        links = []
        
        link_data = self.driver.execute_script("""
            const links = [];
            const elements = document.querySelectorAll('a[href]');
            
            elements.forEach(el => {
                const rect = el.getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0 && 
                    el.offsetParent !== null) {
                    const text = el.innerText || el.textContent || '';
                    if (text.trim()) {
                        links.push({
                            href: el.href,
                            text: text.trim().substring(0, 100),
                            title: el.title || '',
                            rect: {
                                x: rect.x,
                                y: rect.y,
                                width: rect.width,
                                height: rect.height
                            }
                        });
                    }
                }
            });
            
            return links;
        """)
        
        for link_info in link_data[:50]:  # Limit to 50 most relevant links
            element_id = f"link_{self.element_counter}"
            self.element_counter += 1
            
            # Find the actual element
            try:
                element = self.driver.find_element(By.XPATH, f"//a[@href='{link_info['href']}']")
                self.element_map[element_id] = element
                
                links.append({
                    "element_id": element_id,
                    "type": "link",
                    "text": link_info['text'],
                    "href": link_info['href'],
                    "position": link_info['rect']
                })
            except:
                continue
        
        return links
    
    def _extract_buttons(self) -> List[Dict[str, Any]]:
        """Extract visible buttons"""
        buttons = []
        
        button_data = self.driver.execute_script("""
            const buttons = [];
            const elements = document.querySelectorAll('button, input[type="submit"], input[type="button"], [role="button"]');
            
            elements.forEach(el => {
                const rect = el.getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0 && 
                    el.offsetParent !== null) {
                    const text = el.innerText || el.textContent || el.value || '';
                    if (text.trim() || el.type === 'submit') {
                        buttons.push({
                            tag: el.tagName.toLowerCase(),
                            type: el.type || 'button',
                            text: text.trim().substring(0, 50),
                            ariaLabel: el.getAttribute('aria-label') || '',
                            className: el.className || '',
                            rect: {
                                x: rect.x,
                                y: rect.y,
                                width: rect.width,
                                height: rect.height
                            }
                        });
                    }
                }
            });
            
            return buttons;
        """)
        
        for button_info in button_data[:30]:  # Limit buttons
            element_id = f"button_{self.element_counter}"
            self.element_counter += 1
            
            # Build XPath to find the element
            xpath = f"//{button_info['tag']}"
            text = button_info['text']
            if text:
                # Escape quotes in text
                text = text.replace('"', '\\"')
                xpath = f"//{button_info['tag']}[contains(., '{text}')]"
            
            try:
                element = self.driver.find_element(By.XPATH, xpath)
                self.element_map[element_id] = element
                
                buttons.append({
                    "element_id": element_id,
                    "type": "button",
                    "text": button_info['text'] or button_info['ariaLabel'] or "Submit",
                    "button_type": button_info['type'],
                    "position": button_info['rect']
                })
            except:
                continue
        
        return buttons
    
    def _extract_selects(self) -> List[Dict[str, Any]]:
        """Extract select dropdowns"""
        selects = []
        
        select_data = self.driver.execute_script("""
            const selects = [];
            const elements = document.querySelectorAll('select');
            
            elements.forEach(el => {
                const rect = el.getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0 && 
                    el.offsetParent !== null) {
                    const options = Array.from(el.options).map(opt => ({
                        value: opt.value,
                        text: opt.text
                    }));
                    
                    selects.push({
                        name: el.name || '',
                        id: el.id || '',
                        selectedIndex: el.selectedIndex,
                        options: options.slice(0, 20), // Limit options
                        rect: {
                            x: rect.x,
                            y: rect.y,
                            width: rect.width,
                            height: rect.height
                        }
                    });
                }
            });
            
            return selects;
        """)
        
        for select_info in select_data:
            element_id = f"select_{self.element_counter}"
            self.element_counter += 1
            
            # Find the actual element
            if select_info['id']:
                element = self.driver.find_element(By.ID, select_info['id'])
            elif select_info['name']:
                element = self.driver.find_element(By.NAME, select_info['name'])
            else:
                continue
            
            self.element_map[element_id] = element
            
            selects.append({
                "element_id": element_id,
                "type": "select",
                "current_value": select_info['options'][select_info['selectedIndex']]['text'] if select_info['selectedIndex'] >= 0 else "",
                "options": [opt['text'] for opt in select_info['options'][:10]],  # Limit to 10 options
                "position": select_info['rect']
            })
        
        return selects
    
    def _extract_important_text(self) -> List[str]:
        """Extract important visible text content"""
        
        # Get main text content
        text_content = self.driver.execute_script("""
            const texts = [];
            
            // Get search results or main content
            const selectors = [
                '.g',  // Google search results
                'h1', 'h2', 'h3',  // Headers
                'article',  // Article content
                'main',  // Main content
                '.result',  // Generic results
                'p'  // Paragraphs
            ];
            
            selectors.forEach(selector => {
                const elements = document.querySelectorAll(selector);
                elements.forEach(el => {
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0) {
                        const text = el.innerText || el.textContent || '';
                        const trimmed = text.trim();
                        if (trimmed && trimmed.length > 20 && trimmed.length < 500) {
                            texts.push(trimmed);
                        }
                    }
                });
            });
            
            return [...new Set(texts)].slice(0, 20);  // Unique texts, max 20
        """)
        
        return text_content
    
    def get_element_by_id(self, element_id: str) -> Optional[WebElement]:
        """Get the actual WebElement by its extracted ID"""
        return self.element_map.get(element_id)
    
    def format_for_claude(self, page_info: Dict[str, Any]) -> str:
        """Format extracted page info for Claude in a concise way"""
        
        formatted = f"=== Page: {page_info['title']} ===\n"
        formatted += f"URL: {page_info['url']}\n"
        formatted += f"Viewport: {page_info['viewport']['width']}x{page_info['viewport']['height']}\n"
        formatted += f"Scroll: {page_info['scroll_position']['y']}/{page_info['viewport']['scrollHeight']}\n\n"
        
        # Interactive elements
        formatted += "=== Interactive Elements ===\n"
        
        # Group by type
        inputs = [e for e in page_info['elements'] if e['type'] == 'input']
        buttons = [e for e in page_info['elements'] if e['type'] == 'button']
        links = [e for e in page_info['elements'] if e['type'] == 'link']
        selects = [e for e in page_info['elements'] if e['type'] == 'select']
        
        if inputs:
            formatted += "\nInput Fields:\n"
            for inp in inputs:
                formatted += f"  [{inp['element_id']}] {inp['purpose']} input"
                if inp['placeholder']:
                    formatted += f" (placeholder: '{inp['placeholder']}')"
                if inp['current_value']:
                    formatted += f" [value: '{inp['current_value'][:30]}']"
                formatted += "\n"
        
        if buttons:
            formatted += "\nButtons:\n"
            for btn in buttons[:10]:  # Limit buttons shown
                formatted += f"  [{btn['element_id']}] '{btn['text']}'\n"
        
        if links:
            formatted += "\nLinks:\n"
            for link in links[:15]:  # Limit links shown
                text = link['text'][:50] + "..." if len(link['text']) > 50 else link['text']
                formatted += f"  [{link['element_id']}] {text}\n"
        
        if selects:
            formatted += "\nDropdowns:\n"
            for sel in selects:
                formatted += f"  [{sel['element_id']}] Select: {sel['current_value']} (options: {', '.join(sel['options'][:5])}...)\n"
        
        # Important text
        if page_info['text_content']:
            formatted += "\n=== Page Content ===\n"
            for text in page_info['text_content'][:10]:
                if len(text) > 100:
                    text = text[:100] + "..."
                formatted += f"• {text}\n"
        
        return formatted