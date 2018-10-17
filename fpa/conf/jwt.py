"""
JSON Web Token (JWT) settings

The jwt authentication is currently setup to verify tokens signed by 
google firebase. The settings here should match your firebase settings.
"""

# JSON Wen Token key server
JWT_URI = 'https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com';

# Token issuer details
JWT_AUDIENCE = 'unset-jwt-audience';
JWT_ISSUER = 'https://securetoken.google.com/<unset>';
