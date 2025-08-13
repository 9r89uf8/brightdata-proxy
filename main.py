"""
Main Entry Point - Google Search Agent with Claude AI
Orchestrates browser setup, agent initialization, and task execution
"""

import os
import sys
import argparse
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our modules
from browser_setup import create_browser
from search_agent import GoogleSearchAgent


def interactive_mode(agent: GoogleSearchAgent):
    """Run the agent in interactive mode"""
    print("\n" + "="*60)
    print("GOOGLE SEARCH AGENT - Interactive Mode")
    print("="*60)
    print("Type 'help' for available commands")
    print("Type 'quit' to exit")
    print("="*60 + "\n")
    
    while True:
        try:
            command = input("\n> ").strip()
            
            if not command:
                continue
            
            if command.lower() == 'quit':
                print("Goodbye!")
                break
            
            elif command.lower() == 'help':
                print_help()
            
            elif command.lower().startswith('search '):
                query = command[7:].strip()
                if query:
                    print(f"\n[AGENT] Searching for: {query}")
                    result = agent.search(query)
                    print_result(result)
                else:
                    print("[ERROR] Please provide a search query")
            
            elif command.lower().startswith('visit '):
                parts = command[6:].strip().split(' -> ')
                if len(parts) == 2:
                    query, link_text = parts[0].strip(), parts[1].strip()
                    print(f"\n[AGENT] Searching for '{query}' and visiting '{link_text}'")
                    result = agent.search_and_visit(query, link_text)
                    print_result(result)
                else:
                    print("[ERROR] Format: visit <query> -> <link text>")
            
            elif command.lower().startswith('task '):
                task = command[5:].strip()
                if task:
                    print(f"\n[AGENT] Executing task: {task}")
                    result = agent.run(task)
                    print_result(result)
                else:
                    print("[ERROR] Please provide a task description")
            
            elif command.lower() == 'screenshot':
                filename = f"screenshot_{Path.cwd().name}_{os.getpid()}.png"
                agent.take_screenshot(filename)
                print(f"[INFO] Screenshot saved to {filename}")
            
            elif command.lower() == 'results':
                try:
                    results = agent.extract_search_results()
                    if results:
                        print("\n=== Search Results ===")
                        for i, result in enumerate(results, 1):
                            print(f"\n{i}. {result['title']}")
                            print(f"   URL: {result['url']}")
                            if result['description']:
                                print(f"   {result['description'][:100]}...")
                    else:
                        print("[INFO] No search results found on current page")
                except:
                    print("[ERROR] Not on a search results page")
            
            elif command.lower() == 'url':
                print(f"Current URL: {agent.driver.current_url}")
            
            elif command.lower() == 'back':
                agent.actions.go_back()
                print("[INFO] Navigated back")
            
            elif command.lower() == 'forward':
                agent.actions.go_forward()
                print("[INFO] Navigated forward")
            
            elif command.lower() == 'refresh':
                agent.actions.refresh_page()
                print("[INFO] Page refreshed")
            
            else:
                print(f"[ERROR] Unknown command: {command}")
                print("Type 'help' for available commands")
                
        except KeyboardInterrupt:
            print("\n[INFO] Use 'quit' to exit properly")
        except Exception as e:
            print(f"[ERROR] {e}")


def print_help():
    """Print available commands"""
    print("\n=== Available Commands ===")
    print("search <query>           - Search Google for a query")
    print("visit <query> -> <text>  - Search and click on specific result")
    print("task <description>       - Execute a custom task")
    print("screenshot              - Take a screenshot of current page")
    print("results                 - Show search results from current page")
    print("url                     - Show current URL")
    print("back                    - Go back in browser history")
    print("forward                 - Go forward in browser history")
    print("refresh                 - Refresh current page")
    print("help                    - Show this help message")
    print("quit                    - Exit the program")
    print("="*30)


def print_result(result: dict):
    """Pretty print agent result"""
    print("\n" + "="*60)
    if result['success']:
        print("[SUCCESS] Task completed!")
        print(f"Steps taken: {result['steps']}")
        print(f"\nResult:\n{result.get('result', 'No specific result')}")
    else:
        print("[FAILED] Task could not be completed")
        print(f"Error: {result.get('error', 'Unknown error')}")
        print(f"Steps taken: {result['steps']}")
    
    if result.get('history'):
        print("\n=== Action History ===")
        for entry in result['history'][-5:]:  # Show last 5 actions
            print(f"Step {entry['step']}: {entry['action']} {entry.get('parameters', {})}")
    print("="*60)


def run_single_task(agent: GoogleSearchAgent, task: str):
    """Run a single task and exit"""
    print(f"\n[AGENT] Executing task: {task}")
    result = agent.run(task)
    print_result(result)
    return result['success']


def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(description='Google Search Agent powered by Claude AI')
    parser.add_argument('--task', type=str, help='Task to execute (non-interactive mode)')
    parser.add_argument('--search', type=str, help='Search query (non-interactive mode)')
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode')
    parser.add_argument('--desktop', action='store_true', help='Use desktop mode instead of mobile')
    parser.add_argument('--max-steps', type=int, default=5, help='Maximum steps for agent (default: 5)')
    parser.add_argument('--api-key', type=str, help='Anthropic API key (overrides env var)')
    
    args = parser.parse_args()
    
    # Check for API key
    api_key = args.api_key or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("[ERROR] ANTHROPIC_API_KEY not found!")
        print("Set it in .env file or pass with --api-key")
        sys.exit(1)
    
    # Check for proxy
    if not os.getenv("BRIGHTDATA_PROXY"):
        print("[WARNING] BRIGHTDATA_PROXY not set - running without proxy")
        print("Set it in .env file for proxy support")
    
    print("\n" + "="*60)
    print("GOOGLE SEARCH AGENT")
    print("Powered by Claude AI")
    print("="*60)
    
    # Create browser
    print("\n[INFO] Initializing browser...")
    print(f"[INFO] Mode: {'Desktop' if args.desktop else 'Mobile'}")
    print(f"[INFO] Headless: {args.headless}")
    
    try:
        driver = create_browser(
            headless=args.headless,
            mobile=not args.desktop
        )
    except Exception as e:
        print(f"[ERROR] Failed to create browser: {e}")
        sys.exit(1)
    
    try:
        # Create agent
        print("[INFO] Initializing Claude agent...")
        agent = GoogleSearchAgent(driver, api_key=api_key)
        agent.max_steps = args.max_steps
        
        # Run based on mode
        if args.task:
            # Single task mode
            success = run_single_task(agent, args.task)
            sys.exit(0 if success else 1)
        
        elif args.search:
            # Single search mode
            print(f"\n[AGENT] Searching for: {args.search}")
            result = agent.search(args.search)
            print_result(result)
            
            # Show extracted results
            try:
                results = agent.extract_search_results()
                if results:
                    print("\n=== Search Results ===")
                    for i, res in enumerate(results[:5], 1):
                        print(f"\n{i}. {res['title']}")
                        print(f"   {res['url']}")
            except:
                pass
            
            sys.exit(0 if result['success'] else 1)
        
        else:
            # Interactive mode
            interactive_mode(agent)
    
    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user")
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up
        print("\n[INFO] Closing browser...")
        driver.quit()
        print("[INFO] Goodbye!")


if __name__ == "__main__":
    main()