"""
Search Agent Module - Claude-powered Google Search Agent
Intelligent web navigation and information extraction
"""

import os
import json
import time
import random
from typing import Dict, Any, Optional, List
from anthropic import Anthropic
from selenium.webdriver.common.keys import Keys
from dom_extractor import DOMExtractor
from actions import BrowserActions


class GoogleSearchAgent:
    """Claude-powered agent for Google Search automation"""
    
    def __init__(self, driver, api_key: str = None):
        self.driver = driver
        self.dom_extractor = DOMExtractor(driver)
        self.actions = BrowserActions(driver)
        
        # Initialize Claude
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        
        self.claude = Anthropic(api_key=self.api_key)
        self.conversation_history = []
        self.task = None
        self.max_steps = 20
        self.current_step = 0
    
    def set_task(self, task: str):
        """Set the current task for the agent"""
        self.task = task
        self.current_step = 0
        self.conversation_history = []
        print(f"\n[AGENT] Task set: {task}")
    
    def navigate_to_google(self) -> bool:
        """Navigate to Google search page with human-like behavior"""
        try:
            print("[AGENT] Navigating to Google...")
            
            # Human-like session warmup - visit a few pages first
            self._session_warmup()
            
            self.driver.get("https://www.google.com")
            
            # Wait for page to fully load
            self.actions.wait_for_page_load()
            
            # Simulate human reading time - IMPORTANT for Google
            time.sleep(random.uniform(4.0, 7.0))  # Longer initial wait
            
            # Handle cookie consent if present
            self._handle_cookie_consent()
            
            # Human-like page exploration before searching
            self._explore_google_homepage()
            
            # Additional human-like pause
            time.sleep(random.uniform(2.0, 4.0))
            
            return True
        except Exception as e:
            print(f"[ERROR] Failed to navigate to Google: {e}")
            return False
    
    def _handle_cookie_consent(self):
        """Handle Google's cookie consent dialog if present"""
        try:
            # Look for common consent buttons
            consent_selectors = [
                "button[id*='accept']",
                "button[id*='Accept']",
                "button[id*='agree']",
                "button[aria-label*='Accept']",
                "button[aria-label*='Agree']"
            ]
            
            for selector in consent_selectors:
                button = self.actions.wait_for_element(selector, timeout=2)
                if button:
                    self.actions.click_element(button)
                    time.sleep(1)
                    break
        except:
            # No consent dialog or already handled
            pass
    
    def _session_warmup(self):
        """Warm up the session by visiting some pages first"""
        warmup_sites = [
            "https://example.com",
            "https://httpbin.org/headers",
        ]
        
        # Randomly visit 1-2 warmup sites
        sites_to_visit = random.sample(warmup_sites, random.randint(1, min(2, len(warmup_sites))))
        
        for site in sites_to_visit:
            try:
                print(f"[AGENT] Warming up session: {site}")
                self.driver.get(site)
                time.sleep(random.uniform(2.0, 5.0))  # Stay on page briefly
                
                # Some random interaction
                if random.random() < 0.3:  # 30% chance to scroll
                    self.actions.scroll_page("down")
                    time.sleep(random.uniform(1.0, 2.0))
                    
            except Exception as e:
                print(f"[WARN] Warmup failed for {site}: {e}")
                continue
    
    def _explore_google_homepage(self):
        """Explore Google homepage like a human before searching"""
        try:
            exploration_actions = random.randint(1, 3)
            
            for _ in range(exploration_actions):
                action = random.choice([
                    "scroll_down_up",
                    "hover_elements", 
                    "click_and_back",
                    "micro_scrolls"
                ])
                
                if action == "scroll_down_up":
                    # Scroll down and back up
                    self.actions.scroll_page("down", amount=random.randint(100, 300))
                    time.sleep(random.uniform(0.5, 1.5))
                    self.actions.scroll_page("up", amount=random.randint(50, 200))
                    
                elif action == "hover_elements":
                    # Try to hover over common elements
                    try:
                        elements = ["Images", "Gmail", "Search"]
                        for elem_text in random.sample(elements, min(2, len(elements))):
                            elem = self.actions.wait_for_element(f"*[text()='{elem_text}']", timeout=1)
                            if elem:
                                self.actions.hover_element(elem)
                                time.sleep(random.uniform(0.3, 0.8))
                    except:
                        pass
                        
                elif action == "click_and_back":
                    # Sometimes click Images/News then come back
                    if random.random() < 0.2:  # 20% chance
                        try:
                            links = self.driver.find_elements("css selector", "a")
                            if links and len(links) > 2:
                                random_link = random.choice(links[:5])  # Top links only
                                if "Images" in random_link.text or "News" in random_link.text:
                                    random_link.click()
                                    time.sleep(random.uniform(2.0, 4.0))
                                    self.driver.back()
                                    time.sleep(random.uniform(1.0, 2.0))
                        except:
                            pass
                            
                elif action == "micro_scrolls":
                    # Small scrolls like reading
                    for _ in range(random.randint(2, 4)):
                        self.actions.scroll_page("down", amount=random.randint(20, 80))
                        time.sleep(random.uniform(0.3, 1.0))
                
                time.sleep(random.uniform(0.5, 1.5))
                
        except Exception as e:
            print(f"[WARN] Homepage exploration failed: {e}")
    
    def _explore_search_results(self):
        """Explore search results page like a human"""
        try:
            # Reading pattern - scroll down slowly
            print("[AGENT] Reading search results...")
            
            # Initial pause to "read" top results
            time.sleep(random.uniform(2.0, 4.0))
            
            # Scroll pattern while reading results
            scroll_actions = random.randint(2, 4)
            for i in range(scroll_actions):
                # Scroll down to read more results
                scroll_amount = random.randint(200, 400)
                self.actions.scroll_page("down", amount=scroll_amount)
                
                # Reading pause
                time.sleep(random.uniform(1.5, 3.5))
                
                # Sometimes hover over a result
                if random.random() < 0.3:
                    try:
                        results = self.driver.find_elements("css selector", ".g")
                        if results and len(results) > i:
                            self.actions.hover_element(results[i])
                            time.sleep(random.uniform(0.5, 1.0))
                    except:
                        pass
                
                # Sometimes scroll back up a bit to re-read
                if random.random() < 0.2:
                    self.actions.scroll_page("up", amount=random.randint(50, 150))
                    time.sleep(random.uniform(0.5, 1.5))
            
            # Sometimes click on "People also ask" or other elements
            if random.random() < 0.2:
                try:
                    paa = self.driver.find_elements("css selector", "[jsname='N760b']")
                    if paa:
                        random.choice(paa[:2]).click()
                        time.sleep(random.uniform(1.0, 2.0))
                except:
                    pass
                    
        except Exception as e:
            print(f"[WARN] Search results exploration failed: {e}")
    
    
    def analyze_page(self) -> Dict[str, Any]:
        """Extract and analyze current page with Claude"""
        print("[AGENT] Analyzing page...")
        
        # Extract page information
        page_info = self.dom_extractor.extract_page_info()
        
        # Format for Claude
        formatted_page = self.dom_extractor.format_for_claude(page_info)
        
        # Store element map for action execution
        self.current_element_map = self.dom_extractor.element_map
        
        return {
            "page_info": page_info,
            "formatted": formatted_page,
            "element_map": self.current_element_map
        }
    
    def decide_action(self, page_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Ask Claude to decide the next action"""
        
        # Build the prompt
        system_prompt = """You are a web automation agent controlling a browser.
Your goal is to complete the given task by interacting with web pages.

You can perform these actions:
- type: Type text into an input field (specify element_id and text)
- click: Click on an element (specify element_id)
- submit: Submit a form (specify element_id of an input field)
- scroll: Scroll the page (specify direction: up/down/top/bottom)
- select: Select from dropdown (specify element_id and option)
- done: Task is complete (provide the result)
- error: Cannot proceed (explain why)

Respond with a JSON object containing:
{
    "action": "action_name",
    "parameters": {...},
    "reasoning": "why you chose this action",
    "progress": "what you've accomplished so far"
}"""
        
        user_prompt = f"""Current Task: {self.task}

Current Step: {self.current_step + 1}/{self.max_steps}

Page Analysis:
{page_analysis['formatted']}

Previous Actions:
{self._format_history()}

What should be the next action to complete the task?"""
        
        try:
            # Get Claude's decision
            response = self.claude.messages.create(
                model="claude-sonnet-4-20250514",  # Fast model for quick decisions
                max_tokens=500,
                temperature=0.3,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            # Parse the response
            response_text = response.content[0].text
            
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                decision = json.loads(json_match.group())
            else:
                # Fallback parsing
                decision = {
                    "action": "error",
                    "parameters": {},
                    "reasoning": "Could not parse response",
                    "progress": response_text
                }
            
            print(f"[CLAUDE] Action: {decision['action']}")
            print(f"[CLAUDE] Reasoning: {decision.get('reasoning', 'N/A')}")
            
            # Add to history
            self.conversation_history.append({
                "step": self.current_step,
                "action": decision['action'],
                "parameters": decision.get('parameters', {}),
                "url": self.driver.current_url
            })
            
            return decision
            
        except Exception as e:
            print(f"[ERROR] Failed to get Claude decision: {e}")
            return {
                "action": "error",
                "parameters": {},
                "reasoning": f"Error communicating with Claude: {e}",
                "progress": ""
            }
    
    def execute_action(self, decision: Dict[str, Any]) -> bool:
        """Execute the action decided by Claude"""
        
        action = decision['action']
        params = decision.get('parameters', {})
        
        try:
            if action == "type":
                element_id = params.get('element_id')
                text = params.get('text')
                if element_id and text:
                    element = self.current_element_map.get(element_id)
                    if element:
                        return self.actions.type_text(element, text)
            
            elif action == "click":
                element_id = params.get('element_id')
                if element_id:
                    element = self.current_element_map.get(element_id)
                    if element:
                        result = self.actions.click_element(element)
                        if result:
                            self.actions.wait_for_page_load()
                        return result
            
            elif action == "submit":
                element_id = params.get('element_id')
                if element_id:
                    element = self.current_element_map.get(element_id)
                    if element:
                        result = self.actions.submit_form(element)
                        if result:
                            self.actions.wait_for_page_load()
                        return result
            
            elif action == "scroll":
                direction = params.get('direction', 'down')
                return self.actions.scroll_page(direction)
            
            elif action == "select":
                element_id = params.get('element_id')
                option = params.get('option')
                if element_id and option:
                    element = self.current_element_map.get(element_id)
                    if element:
                        return self.actions.select_option(element, option)
            
            elif action == "done":
                print(f"[AGENT] Task completed!")
                result = params.get('result', decision.get('progress', 'Task completed'))
                print(f"[RESULT] {result}")
                return True
            
            elif action == "error":
                print(f"[AGENT] Error encountered: {decision.get('reasoning', 'Unknown error')}")
                return False
            
            else:
                print(f"[WARN] Unknown action: {action}")
                return False
                
        except Exception as e:
            print(f"[ERROR] Failed to execute action {action}: {e}")
            return False
    
    def run(self, task: str, start_url: str = None) -> Dict[str, Any]:
        """Run the agent to complete a task"""
        
        self.set_task(task)
        
        # Navigate to starting point
        if start_url:
            self.driver.get(start_url)
        else:
            self.navigate_to_google()
        
        # Main agent loop
        while self.current_step < self.max_steps:
            self.current_step += 1
            print(f"\n[STEP {self.current_step}/{self.max_steps}]")
            
            # Analyze current page
            page_analysis = self.analyze_page()
            
            # Decide next action
            decision = self.decide_action(page_analysis)
            
            # Check if task is complete
            if decision['action'] == 'done':
                return {
                    "success": True,
                    "result": decision.get('parameters', {}).get('result', decision.get('progress')),
                    "steps": self.current_step,
                    "history": self.conversation_history
                }
            
            # Check for errors
            if decision['action'] == 'error':
                return {
                    "success": False,
                    "error": decision.get('reasoning', 'Unknown error'),
                    "steps": self.current_step,
                    "history": self.conversation_history
                }
            
            # Execute the action
            success = self.execute_action(decision)
            
            if not success:
                print(f"[WARN] Action failed, retrying...")
                # Continue to next iteration to retry
            
            # Small delay between actions
            time.sleep(1)
        
        # Max steps reached
        return {
            "success": False,
            "error": "Maximum steps reached",
            "steps": self.current_step,
            "history": self.conversation_history
        }
    
    def search(self, query: str) -> Dict[str, Any]:
        """Perform a Google search with enhanced anti-detection"""
        print(f"[AGENT] Searching for: {query}")
        
        # Navigate to Google first
        if not self.navigate_to_google():
            return {"success": False, "error": "Failed to navigate to Google"}
        
        # Find the search box
        search_box = None
        try:
            # Try different selectors for the search box
            selectors = [
                'input[name="q"]',
                'textarea[name="q"]',
                'input[type="search"]',
                '#APjFqb'  # Google's current search box ID
            ]
            
            for selector in selectors:
                search_box = self.actions.wait_for_element(selector, timeout=3)
                if search_box:
                    break
            
            if not search_box:
                return {"success": False, "error": "Could not find search box"}
            
            # Human-like interaction with search box
            print("[AGENT] Found search box, preparing to search...")
            
            # Wait before interacting (longer, more human)
            time.sleep(random.uniform(2.0, 4.0))
            
            # Sometimes click elsewhere first then search box (human behavior)
            if random.random() < 0.3:
                try:
                    # Click on page background first
                    self.driver.execute_script("document.body.click();")
                    time.sleep(random.uniform(0.5, 1.0))
                except:
                    pass
            
            # Click on search box (important - triggers Google's JS)
            self.actions.click_element(search_box)
            time.sleep(random.uniform(0.8, 1.5))
            
            # Sometimes start typing then delete (human behavior)
            if random.random() < 0.15:  # 15% chance
                fake_text = random.choice(["weather", "news", "how to"])
                self.actions.type_text(search_box, fake_text[:random.randint(2, len(fake_text))], clear_first=False)
                time.sleep(random.uniform(1.0, 2.0))
                # Clear it
                search_box.clear()
                time.sleep(random.uniform(0.5, 1.0))
            
            # Type the query slowly with more variation
            self.actions.type_text(search_box, query, clear_first=True)
            
            # CRITICAL: Wait for suggestions to appear (longer)
            time.sleep(random.uniform(3.0, 5.0))
            
            # Sometimes interact with suggestions
            if random.random() < 0.4:  # 40% chance to use suggestions
                try:
                    suggestions = self.driver.find_elements("css selector", "[role='option']")
                    if suggestions and len(suggestions) > 1:
                        # Hover over a few suggestions
                        for suggestion in random.sample(suggestions, min(2, len(suggestions))):
                            self.actions.hover_element(suggestion)
                            time.sleep(random.uniform(0.3, 0.7))
                        
                        # Sometimes click a suggestion
                        if random.random() < 0.5 and suggestions:
                            random.choice(suggestions).click()
                            print("[AGENT] Clicked on suggestion")
                            suggestion_clicked = True
                        else:
                            suggestion_clicked = False
                    else:
                        suggestion_clicked = False
                except:
                    suggestion_clicked = False
            else:
                suggestion_clicked = False
            
            # Only look for search button if we didn't click a suggestion
            if not suggestion_clicked:
                # Find and click the search button (NOT Enter key)
                search_button = None
                button_selectors = [
                    'input[name="btnK"]',
                    'button[aria-label*="Search"]',
                    'input[type="submit"]'
                ]
                
                for selector in button_selectors:
                    try:
                        search_button = self.driver.find_element("css selector", selector)
                        if search_button and search_button.is_displayed():
                            break
                    except:
                        continue
                
                # Decide whether to click button or press Enter (mix it up)
                use_enter = random.random() < 0.3  # 30% chance to use Enter
                
                if search_button and not use_enter:
                    print("[AGENT] Clicking search button...")
                    # Move to button and click with more delay
                    time.sleep(random.uniform(1.0, 2.0))
                    self.actions.scroll_to_element(search_button)
                    time.sleep(random.uniform(0.8, 1.5))
                    self.actions.click_element(search_button)
                else:
                    # Use Enter key
                    print("[AGENT] Using Enter key...")
                    time.sleep(random.uniform(1.5, 3.0))
                    search_box.send_keys(Keys.RETURN)
            
            # Wait for results to load (longer, more human)
            time.sleep(random.uniform(4.0, 7.0))
            self.actions.wait_for_page_load()
            
            # Check if we got results or bot page
            if "sorry" in self.driver.page_source.lower() and "unusual traffic" in self.driver.page_source.lower():
                return {"success": False, "error": "Detected by Google bot protection"}
            
            # Human-like behavior after getting results
            self._explore_search_results()
            
            # Extract results
            results = self.extract_search_results()
            
            return {
                "success": True,
                "query": query,
                "results": results,
                "url": self.driver.current_url
            }
            
        except Exception as e:
            print(f"[ERROR] Search failed: {e}")
            return {"success": False, "error": str(e)}
    
    def search_and_visit(self, query: str, link_text: str) -> Dict[str, Any]:
        """Search and visit a specific result"""
        task = f"Search Google for '{query}', find a result containing '{link_text}', click on it, and summarize the main content of the page"
        return self.run(task)
    
    def _format_history(self) -> str:
        """Format action history for Claude"""
        if not self.conversation_history:
            return "None"
        
        formatted = []
        for entry in self.conversation_history[-5:]:  # Last 5 actions
            action = entry['action']
            params = entry.get('parameters', {})
            formatted.append(f"Step {entry['step']}: {action} {params}")
        
        return "\n".join(formatted)
    
    def extract_search_results(self) -> List[Dict[str, str]]:
        """Extract search results from current Google search page"""
        
        results = []
        
        # Use JavaScript to extract Google search results
        extracted = self.driver.execute_script("""
            const results = [];
            const searchResults = document.querySelectorAll('.g');
            
            searchResults.forEach((result, index) => {
                if (index < 10) {  // Limit to 10 results
                    const link = result.querySelector('a');
                    const title = result.querySelector('h3');
                    const description = result.querySelector('.VwiC3b, .st, .IsZvec');
                    
                    if (link && title) {
                        results.push({
                            title: title.innerText || '',
                            url: link.href || '',
                            description: description ? description.innerText : ''
                        });
                    }
                }
            });
            
            return results;
        """)
        
        return extracted
    
    def take_screenshot(self, filename: str = None) -> str:
        """Take a screenshot of current page"""
        return self.actions.take_screenshot(filename)