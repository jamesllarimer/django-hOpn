from django.conf import settings
from urllib.parse import urljoin
import requests

class ApiClient:
    """Client for making internal API calls"""
    
    def __init__(self, request=None):
        self.base_url = f"http://{settings.ALLOWED_HOSTS[0]}/api/" if settings.ALLOWED_HOSTS else "http://localhost:8000/api/"
        self.session = requests.Session()
        if request:
            # Copy authentication from the original request
            self.session.cookies = request.COOKIES
            if request.user.is_authenticated:
                self.session.headers.update({
                    'X-CSRFToken': request.COOKIES.get('csrftoken'),
                })

    def _make_url(self, endpoint):
        return urljoin(self.base_url, endpoint.lstrip('/'))

    def get(self, endpoint, params=None):
        """Make GET request to API endpoint"""
        response = self.session.get(self._make_url(endpoint), params=params)
        response.raise_for_status()
        return response.json()

    def post(self, endpoint, data=None):
        """Make POST request to API endpoint"""
        response = self.session.post(self._make_url(endpoint), json=data)
        response.raise_for_status()
        return response.json()

    def put(self, endpoint, data=None):
        """Make PUT request to API endpoint"""
        response = self.session.put(self._make_url(endpoint), json=data)
        response.raise_for_status()
        return response.json()

    def delete(self, endpoint):
        """Make DELETE request to API endpoint"""
        response = self.session.delete(self._make_url(endpoint))
        response.raise_for_status()
        return response.json() if response.content else None