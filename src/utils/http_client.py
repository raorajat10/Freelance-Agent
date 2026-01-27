import requests
from typing import Optional, Tuple
from config.settings import REQUEST_TIMEOUT, USER_AGENT


class HTTPClient:
    """Safe HTTP client with timeout and error handling"""
    
    def __init__(self, timeout: int = REQUEST_TIMEOUT):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': USER_AGENT
        })
    
    def get(self, url: str) -> Tuple[bool, Optional[requests.Response], Optional[str]]:
        """
        Make HTTP GET request
        
        Returns:
            (success: bool, response: Response, error: str)
        """
        try:
            response = self.session.get(
                url, 
                timeout=self.timeout,
                allow_redirects=True,
                verify=True
            )
            
            # Consider 2xx and 3xx as success
            if 200 <= response.status_code < 400:
                return True, response, None
            else:
                return False, response, f"HTTP {response.status_code}"
                
        except requests.exceptions.Timeout:
            return False, None, "Timeout"
        except requests.exceptions.SSLError:
            return False, None, "SSL Error"
        except requests.exceptions.ConnectionError:
            return False, None, "Connection Failed"
        except requests.exceptions.TooManyRedirects:
            return False, None, "Too Many Redirects"
        except Exception as e:
            return False, None, f"Error: {str(e)}"
    
    def close(self):
        """Close session"""
        self.session.close()