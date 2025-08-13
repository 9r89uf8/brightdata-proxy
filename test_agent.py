"""
Test Script - Verify Google Search Agent components
Run this to test that all modules are working correctly
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_imports():
    """Test that all modules can be imported"""
    print("Testing module imports...")
    
    try:
        import browser_setup
        print("✓ browser_setup imported")
    except ImportError as e:
        print(f"✗ Failed to import browser_setup: {e}")
        return False
    
    try:
        import dom_extractor
        print("✓ dom_extractor imported")
    except ImportError as e:
        print(f"✗ Failed to import dom_extractor: {e}")
        return False
    
    try:
        import actions
        print("✓ actions imported")
    except ImportError as e:
        print(f"✗ Failed to import actions: {e}")
        return False
    
    try:
        import search_agent
        print("✓ search_agent imported")
    except ImportError as e:
        print(f"✗ Failed to import search_agent: {e}")
        return False
    
    try:
        import main
        print("✓ main imported")
    except ImportError as e:
        print(f"✗ Failed to import main: {e}")
        return False
    
    return True


def test_environment():
    """Test environment variables"""
    print("\nTesting environment variables...")
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        print(f"✓ ANTHROPIC_API_KEY found (length: {len(api_key)})")
    else:
        print("✗ ANTHROPIC_API_KEY not found - agent will not work without this")
        print("  Set it in .env file or as environment variable")
    
    proxy = os.getenv("BRIGHTDATA_PROXY")
    if proxy:
        print(f"✓ BRIGHTDATA_PROXY found: {proxy[:30]}...")
    else:
        print("⚠ BRIGHTDATA_PROXY not found - will run without proxy")
    
    bd_ca = os.getenv("BRIGHTDATA_CA_B64") or os.getenv("BRIGHTDATA_CA_PEM")
    if bd_ca:
        print("✓ Bright Data CA certificate found in environment")
    else:
        from pathlib import Path
        if (Path(__file__).parent / "brightdata_ca.crt").exists():
            print("✓ Bright Data CA certificate found as file")
        else:
            print("⚠ Bright Data CA certificate not found - may have issues with proxy")
    
    return api_key is not None


def test_browser_creation():
    """Test browser creation"""
    print("\nTesting browser creation...")
    
    try:
        from browser_setup import create_browser
        
        print("Creating headless mobile browser...")
        driver = create_browser(headless=True, mobile=True)
        
        print("✓ Browser created successfully")
        print(f"  User Agent: {driver.execute_script('return navigator.userAgent')[:50]}...")
        
        # Test navigation
        print("Testing navigation to Google...")
        driver.get("https://www.google.com")
        
        if "google" in driver.current_url.lower():
            print("✓ Successfully navigated to Google")
        else:
            print(f"⚠ Unexpected URL: {driver.current_url}")
        
        driver.quit()
        print("✓ Browser closed successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Browser test failed: {e}")
        return False


def test_dom_extraction():
    """Test DOM extraction"""
    print("\nTesting DOM extraction...")
    
    try:
        from browser_setup import create_browser
        from dom_extractor import DOMExtractor
        
        driver = create_browser(headless=True, mobile=True)
        driver.get("https://www.google.com")
        
        extractor = DOMExtractor(driver)
        page_info = extractor.extract_page_info()
        
        print("✓ DOM extracted successfully")
        print(f"  Title: {page_info['title']}")
        print(f"  URL: {page_info['url']}")
        print(f"  Interactive elements found: {len(page_info['elements'])}")
        
        # Check for search box
        search_inputs = [e for e in page_info['elements'] if e['type'] == 'input' and e['purpose'] == 'search']
        if search_inputs:
            print(f"✓ Found search input field")
        else:
            print("⚠ No search input found")
        
        driver.quit()
        return True
        
    except Exception as e:
        print(f"✗ DOM extraction test failed: {e}")
        return False


def test_agent_initialization():
    """Test agent initialization"""
    print("\nTesting agent initialization...")
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠ Skipping agent test - no API key")
        return False
    
    try:
        from browser_setup import create_browser
        from search_agent import GoogleSearchAgent
        
        driver = create_browser(headless=True, mobile=True)
        agent = GoogleSearchAgent(driver, api_key=api_key)
        
        print("✓ Agent initialized successfully")
        print(f"  Max steps: {agent.max_steps}")
        
        # Test navigation
        success = agent.navigate_to_google()
        if success:
            print("✓ Agent navigated to Google")
        else:
            print("✗ Agent failed to navigate to Google")
        
        driver.quit()
        return success
        
    except Exception as e:
        print(f"✗ Agent initialization failed: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("="*60)
    print("GOOGLE SEARCH AGENT - Component Test Suite")
    print("="*60)
    
    results = []
    
    # Test imports
    results.append(("Module Imports", test_imports()))
    
    # Test environment
    results.append(("Environment Setup", test_environment()))
    
    # Test browser
    if results[0][1]:  # Only if imports passed
        results.append(("Browser Creation", test_browser_creation()))
        
        # Test DOM extraction
        if results[2][1]:  # Only if browser works
            results.append(("DOM Extraction", test_dom_extraction()))
        
        # Test agent
        if results[1][1]:  # Only if environment is set up
            results.append(("Agent Initialization", test_agent_initialization()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name:25} {status}")
    
    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)
    
    print("="*60)
    print(f"Results: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("\n✓ All tests passed! The agent is ready to use.")
        print("\nRun the agent with:")
        print("  python main.py                    # Interactive mode")
        print("  python main.py --search 'query'   # Search mode")
        print("  python main.py --task 'task'      # Task mode")
    else:
        print("\n⚠ Some tests failed. Please check the errors above.")
        if not results[1][1]:
            print("\nMost importantly, set your ANTHROPIC_API_KEY in the .env file:")
            print("  ANTHROPIC_API_KEY=your_api_key_here")
    
    return total_passed == total_tests


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)