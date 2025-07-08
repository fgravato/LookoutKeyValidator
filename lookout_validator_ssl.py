#!/usr/bin/env python3
"""
Lookout Mobile Risk API - Application Key Validator

This tool validates Lookout application keys by attempting to:
1. Obtain an OAuth2 access token using the application key
2. Make a test API call to verify the token works
3. Report the validation results

Usage:
    python lookout_validator.py <application_key>
    python lookout_validator.py --key <application_key>
    python lookout_validator.py --file keys.txt
    python lookout_validator.py --key <application_key> --skip-ssl-verify
"""

import requests
import json
import argparse
import sys
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import time
import urllib3

class LookoutAPIValidator:
    """Validates Lookout application keys and API connectivity."""
    
    def __init__(self, base_url: str = "https://api.lookout.com", skip_ssl_verify: bool = False):
        self.base_url = base_url.rstrip('/')
        self.token_endpoint = f"{self.base_url}/oauth2/token"
        self.test_endpoint = f"{self.base_url}/mra/api/v2/devices"
        self.skip_ssl_verify = skip_ssl_verify
        
        # Disable SSL warnings if skip_ssl_verify is True
        if self.skip_ssl_verify:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
    def get_access_token(self, application_key: str, scope: str = None) -> Tuple[bool, Dict[str, Any]]:
        """
        Obtain an OAuth2 access token using the application key.
        
        Args:
            application_key: The Lookout application key
            scope: Optional scope parameter
            
        Returns:
            Tuple of (success, response_data)
        """
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {application_key}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {'grant_type': 'client_credentials'}
        if scope:
            data['scope'] = scope
            
        try:
            response = requests.post(
                self.token_endpoint,
                headers=headers,
                data=data,
                timeout=30,
                verify=not self.skip_ssl_verify
            )
            
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, {
                    'error': f'HTTP {response.status_code}',
                    'message': response.text,
                    'status_code': response.status_code
                }
                
        except requests.exceptions.RequestException as e:
            return False, {'error': 'Network error', 'message': str(e)}
    
    def test_api_access(self, access_token: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Test API access using the access token.
        
        Args:
            access_token: OAuth2 access token
            
        Returns:
            Tuple of (success, response_data)
        """
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }
        
        # Test with a simple devices query with limit=1 to minimize data transfer
        params = {'limit': 1}
        
        try:
            response = requests.get(
                self.test_endpoint,
                headers=headers,
                params=params,
                timeout=30,
                verify=not self.skip_ssl_verify
            )
            
            if response.status_code == 200:
                data = response.json()
                return True, {
                    'device_count': data.get('count', 0),
                    'api_accessible': True
                }
            else:
                return False, {
                    'error': f'HTTP {response.status_code}',
                    'message': response.text,
                    'status_code': response.status_code
                }
                
        except requests.exceptions.RequestException as e:
            return False, {'error': 'Network error', 'message': str(e)}
    
    def validate_key(self, application_key: str, scope: str = None) -> Dict[str, Any]:
        """
        Validate a Lookout application key.
        
        Args:
            application_key: The application key to validate
            scope: Optional scope parameter
            
        Returns:
            Dictionary with validation results
        """
        result = {
            'application_key': application_key[:20] + '...' if len(application_key) > 20 else application_key,
            'timestamp': datetime.now().isoformat(),
            'valid': False,
            'token_obtained': False,
            'api_accessible': False,
            'ssl_verify_skipped': self.skip_ssl_verify,
            'errors': []
        }
        
        ssl_status = " (SSL verification disabled)" if self.skip_ssl_verify else ""
        print(f"🔍 Validating application key: {result['application_key']}{ssl_status}")
        
        # Step 1: Try to get access token
        print("  ➤ Requesting OAuth2 access token...")
        token_success, token_data = self.get_access_token(application_key, scope)
        
        if not token_success:
            result['errors'].append(f"Token request failed: {token_data.get('error', 'Unknown error')}")
            print(f"  ❌ Token request failed: {token_data.get('message', 'Unknown error')}")
            return result
        
        result['token_obtained'] = True
        result['token_info'] = {
            'token_type': token_data.get('token_type'),
            'expires_in': token_data.get('expires_in'),
            'expires_at': token_data.get('expires_at'),
            'scope': token_data.get('scope', '')
        }
        
        print(f"  ✅ Access token obtained (expires in {token_data.get('expires_in', 'unknown')} seconds)")
        
        # Step 2: Test API access
        print("  ➤ Testing API access...")
        access_token = token_data['access_token']
        api_success, api_data = self.test_api_access(access_token)
        
        if not api_success:
            result['errors'].append(f"API access failed: {api_data.get('error', 'Unknown error')}")
            print(f"  ❌ API access failed: {api_data.get('message', 'Unknown error')}")
            return result
        
        result['api_accessible'] = True
        result['api_info'] = api_data
        result['valid'] = True
        
        print(f"  ✅ API access successful (found {api_data.get('device_count', 0)} devices)")
        print("  🎉 Application key is valid!")
        
        return result

def load_keys_from_file(filename: str) -> list:
    """Load application keys from a text file (one per line)."""
    try:
        with open(filename, 'r') as f:
            keys = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
        return keys
    except FileNotFoundError:
        print(f"❌ File not found: {filename}")
        return []
    except Exception as e:
        print(f"❌ Error reading file {filename}: {e}")
        return []

def main():
    parser = argparse.ArgumentParser(
        description='Validate Lookout Mobile Risk API application keys',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python lookout_validator.py abc123...
  python lookout_validator.py --key abc123...
  python lookout_validator.py --file keys.txt
  python lookout_validator.py --key abc123... --scope "custom_scope"
  python lookout_validator.py --key abc123... --skip-ssl-verify
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('key', nargs='?', help='Application key to validate')
    group.add_argument('--key', dest='key_arg', help='Application key to validate')
    group.add_argument('--file', help='File containing application keys (one per line)')
    
    parser.add_argument('--scope', help='Optional OAuth2 scope parameter')
    parser.add_argument('--url', default='https://api.lookout.com', 
                       help='Lookout API base URL (default: https://api.lookout.com)')
    parser.add_argument('--output', help='Save results to JSON file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--skip-ssl-verify', action='store_true', 
                       help='Skip SSL certificate verification (use with caution)')
    
    args = parser.parse_args()
    
    # Determine the application key(s) to validate
    keys_to_validate = []
    
    if args.file:
        keys_to_validate = load_keys_from_file(args.file)
        if not keys_to_validate:
            sys.exit(1)
    else:
        key = args.key or args.key_arg
        if not key:
            print("❌ No application key provided")
            sys.exit(1)
        keys_to_validate = [key]
    
    print(f"🚀 Lookout API Key Validator")
    print(f"📡 API Base URL: {args.url}")
    print(f"🔑 Keys to validate: {len(keys_to_validate)}")
    
    if args.skip_ssl_verify:
        print("⚠️  SSL certificate verification is DISABLED")
    
    print("-" * 50)
    
    validator = LookoutAPIValidator(args.url, args.skip_ssl_verify)
    results = []
    
    for i, key in enumerate(keys_to_validate, 1):
        if len(keys_to_validate) > 1:
            print(f"\n[{i}/{len(keys_to_validate)}]")
        
        result = validator.validate_key(key, args.scope)
        results.append(result)
        
        if args.verbose:
            print(f"  📊 Full result: {json.dumps(result, indent=2)}")
        
        # Small delay between requests if validating multiple keys
        if i < len(keys_to_validate):
            time.sleep(1)
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 VALIDATION SUMMARY")
    print("=" * 50)
    
    valid_count = sum(1 for r in results if r['valid'])
    print(f"✅ Valid keys: {valid_count}/{len(results)}")
    print(f"❌ Invalid keys: {len(results) - valid_count}/{len(results)}")
    
    if args.skip_ssl_verify:
        print("⚠️  SSL verification was disabled for all requests")
    
    if not all(r['valid'] for r in results):
        print("\n❌ Failed validations:")
        for result in results:
            if not result['valid']:
                print(f"  • {result['application_key']}: {', '.join(result['errors'])}")
    
    # Save results if requested
    if args.output:
        try:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n💾 Results saved to: {args.output}")
        except Exception as e:
            print(f"\n❌ Failed to save results: {e}")
    
    # Exit with error code if any validation failed
    if not all(r['valid'] for r in results):
        sys.exit(1)

if __name__ == "__main__":
    main()