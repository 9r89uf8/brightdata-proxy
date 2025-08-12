"""
Detect your real IP address from multiple sources to understand IP variations
"""
import requests
import socket
import json
import sys
from datetime import datetime

def get_ip_from_multiple_sources():
    """Get IP address from multiple sources to see variations"""
    
    sources = [
        ("httpbin.org", "http://httpbin.org/ip"),
        ("ipify.org", "https://api.ipify.org?format=json"),
        ("ip-api.com", "http://ip-api.com/json/"),
        ("ipinfo.io", "https://ipinfo.io/json"),
        ("whatismyip.akamai.com", "http://whatismyip.akamai.com/"),
        ("icanhazip.com", "https://icanhazip.com/"),
    ]
    
    results = {}
    print("=== CHECKING YOUR IP FROM MULTIPLE SOURCES ===")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    for name, url in sources:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                content = response.text.strip()
                
                # Try to parse as JSON
                try:
                    data = json.loads(content)
                    if 'origin' in data:
                        ip = data['origin']
                    elif 'ip' in data:
                        ip = data['ip']
                    elif 'query' in data:
                        ip = data['query']
                    else:
                        ip = content
                except:
                    ip = content
                
                results[name] = ip
                print(f"[OK] {name:20}: {ip}")
            else:
                print(f"[FAIL] {name:20}: HTTP {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"[FAIL] {name:20}: {str(e)[:50]}...")
        except Exception as e:
            print(f"[FAIL] {name:20}: {str(e)[:50]}...")
    
    return results

def analyze_ip_variations(results):
    """Analyze IP variations and provide recommendations"""
    
    if not results:
        print("\n[ERROR] Could not get IP from any source!")
        return None
    
    print(f"\n=== ANALYSIS ===")
    
    # Get unique IPs
    unique_ips = set(results.values())
    
    if len(unique_ips) == 1:
        ip = list(unique_ips)[0]
        print(f"[GOOD] All sources show the same IP: {ip}")
        print(f"[ACTION] Use this IP for Oxylabs whitelisting: {ip}")
        return ip
    else:
        print(f"[WARNING] Multiple different IPs detected:")
        for ip in unique_ips:
            sources = [name for name, result_ip in results.items() if result_ip == ip]
            print(f"  {ip} - seen by: {', '.join(sources)}")
        
        print(f"\n[ISSUE] Your IP is not consistent across services!")
        print(f"This is common with:")
        print(f"  • Dynamic IP from ISP")
        print(f"  • Complex network routing")
        print(f"  • IPv4/IPv6 dual stack")
        print(f"  • Load balancer or CDN interference")
        
        # Recommend the most common IP
        ip_counts = {}
        for ip in results.values():
            ip_counts[ip] = ip_counts.get(ip, 0) + 1
        
        most_common_ip = max(ip_counts, key=ip_counts.get)
        print(f"\n[RECOMMENDATION] Most common IP: {most_common_ip}")
        print(f"[ACTION] Try whitelisting this IP first: {most_common_ip}")
        
        return most_common_ip

def test_oxylabs_specific():
    """Test what IP Oxylabs specifically sees"""
    print(f"\n=== TESTING WHAT OXYLABS SEES ===")
    
    # Test direct connection to see what IP Oxylabs infrastructure sees
    oxylabs_test_urls = [
        "https://httpbin.org/ip",  # This goes through various networks
        "http://httpbin.org/ip",   # Non-SSL version
    ]
    
    for url in oxylabs_test_urls:
        try:
            print(f"Testing {url}...")
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = json.loads(response.text)
                ip = data.get('origin', 'unknown')
                print(f"  Oxylabs-route IP: {ip}")
            else:
                print(f"  Failed: HTTP {response.status_code}")
        except Exception as e:
            print(f"  Error: {e}")

def get_network_info():
    """Get additional network information"""
    print(f"\n=== NETWORK INFO ===")
    
    try:
        # Get local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        print(f"Local IP: {local_ip}")
    except:
        print("Could not determine local IP")
    
    try:
        hostname = socket.gethostname()
        print(f"Hostname: {hostname}")
    except:
        pass

def main():
    print("IP ADDRESS DETECTIVE")
    print("=" * 50)
    print("This tool will help you understand why you see different IPs")
    print("and determine the correct IP to whitelist with Oxylabs.")
    print()
    
    # Get network info
    get_network_info()
    
    # Check IPs from multiple sources
    results = get_ip_from_multiple_sources()
    
    # Analyze variations
    recommended_ip = analyze_ip_variations(results)
    
    # Test Oxylabs-specific routing
    test_oxylabs_specific()
    
    print(f"\n=== RECOMMENDATIONS ===")
    
    if recommended_ip:
        print(f"1. WHITELIST THIS IP: {recommended_ip}")
        print(f"2. If whitelisting fails, your IP might be dynamic")
        print(f"3. Consider switching to credential-based authentication")
    
    print(f"\n=== SOLUTIONS FOR DYNAMIC IP ===")
    print(f"1. CREDENTIAL AUTH (Easiest):")
    print(f"   - Use OXYLABS_USERNAME/PASSWORD instead of IP whitelisting")
    print(f"   - No need to track IP changes")
    print(f"   - Run: python fix_proxy_config.py and choose option 2")
    
    print(f"\n2. DYNAMIC IP WHITELISTING:")
    print(f"   - Some ISPs provide static IP for business plans")
    print(f"   - Use a VPN with static IP")
    print(f"   - Set up automatic IP update script")
    
    print(f"\n3. MIXED APPROACH:")
    print(f"   - Keep credential auth as backup")
    print(f"   - Use IP whitelisting when your IP is stable")
    
    print(f"\nNext step: Run 'python fix_proxy_config.py' to switch to credential auth")

if __name__ == "__main__":
    main()