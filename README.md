# LookoutKeyValidator
Features:

1. OAuth2 Token Validation: Tests if the application key can obtain an access token
2. API Access Testing: Verifies the token works by making a test API call
3. Multiple Key Support: Can validate single keys or batch process from a file
4. Detailed Reporting: Provides clear success/failure feedback with error details
5. JSON Export: Option to save results to a file for further analysis


Usage Examples:
# Validate a single key
```python lookout_validator.py "your_application_key_here" ```

# Validate with explicit --key flag
```python lookout_validator.py --key "your_application_key_here"```

# Validate multiple keys from a file
```python lookout_validator.py --file keys.txt```

# Save results to JSON file
```python lookout_validator.py --key "your_key" --output results.json```

# Use custom scope
```python lookout_validator.py --key "your_key" --scope "custom_scope"```


Required Dependencies:
Python3 and Requests
You'll need to install the requests library:
```pip install requests```

Key Validation Process:

 Step 1: Attempts to get an OAuth2 access token using the application key
 
 Step 2: Tests API access by making a simple call to /mra/api/v2/devices
 
 Reports: Success/failure with detailed error messages


# Lookout API Key Validation Process

## Key Validation Process

The validation process consists of two main steps:

**Step 1**: Attempts to get an OAuth2 access token using the application key

**Step 2**: Tests API access by making a simple call to `/mra/api/v2/devices`

**Reports**: Success/failure with detailed error messages

## File Format for Batch Validation

Create a text file with one application key per line:

```
application_key_1
application_key_2
# Comments start with #
application_key_3
```

## Authentication Flow

The tool follows the exact authentication flow described in your Lookout API documentation:

- Uses the `/oauth2/token` endpoint with `client_credentials` grant type
- Includes proper headers and authentication
- Tests the token with a real API call to ensure it's working

This should help you quickly validate whether your Lookout application keys are properly configured and can successfully connect to the API.
