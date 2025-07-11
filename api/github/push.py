"""
Vercel Serverless API for Direct Push to GitHub
File: api/github/push.py
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import base64
import jwt
import urllib.request
import urllib.parse

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle POST requests for direct push"""
        path = self.path
        
        if '/push' in path:
            self.handle_direct_push()
        else:
            self.send_error(404, "Not Found")
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Allow-Credentials', 'true')
        self.end_headers()
    
    def handle_direct_push(self):
        """Handle direct push to repository"""
        try:
            # Get authentication
            github_token = self.get_github_token()
            if not github_token:
                self.send_json_response({'error': 'Not authenticated'}, 401)
                return
            
            # Parse path to get owner and repo
            path_parts = self.path.split('/')
            if len(path_parts) < 7:
                self.send_error(400, "Invalid path")
                return
            
            owner = path_parts[4]
            repo = path_parts[5]
            
            # Get request body
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # Validate required fields
            branch = data.get('branch')
            content = data.get('content')
            filename = data.get('filename', 'README.md')
            commit_message = data.get('commit_message', 'Update documentation')
            
            if not all([branch, content]):
                self.send_json_response({'error': 'Missing required fields'}, 400)
                return
            
            # Get current file SHA if it exists
            file_sha = self.get_file_sha(github_token, owner, repo, filename, branch)
            
            # Prepare file data
            file_data = {
                'message': commit_message,
                'content': base64.b64encode(content.encode('utf-8')).decode('utf-8'),
                'branch': branch
            }
            
            if file_sha:
                file_data['sha'] = file_sha
            
            # Create or update file
            req = urllib.request.Request(
                f'https://api.github.com/repos/{owner}/{repo}/contents/{filename}',
                data=json.dumps(file_data).encode(),
                headers={
                    'Authorization': f'token {github_token}',
                    'Accept': 'application/vnd.github.v3+json',
                    'User-Agent': 'Tekshila-App',
                    'Content-Type': 'application/json'
                }
            )
            req.get_method = lambda: 'PUT'
            
            with urllib.request.urlopen(req) as response:
                if response.status not in [200, 201]:
                    raise Exception(f"Failed to push file: {response.status}")
                
                result = json.loads(response.read().decode())
                
                self.send_json_response({
                    'success': True,
                    'commit': result['commit'],
                    'content': result['content']
                })
                
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)
    
    def get_file_sha(self, github_token, owner, repo, filename, branch):
        """Get the SHA of an existing file"""
        try:
            req = urllib.request.Request(
                f'https://api.github.com/repos/{owner}/{repo}/contents/{filename}?ref={branch}',
                headers={
                    'Authorization': f'token {github_token}',
                    'Accept': 'application/vnd.github.v3+json',
                    'User-Agent': 'Tekshila-App'
                }
            )
            
            with urllib.request.urlopen(req) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    return data.get('sha')
        except:
            # File doesn't exist
            return None
    
    def get_github_token(self):
        """Extract GitHub token from JWT"""
        try:
            cookies = self.parse_cookies()
            jwt_token = cookies.get('auth_token')
            
            if not jwt_token:
                return None
            
            # Decode JWT
            secret_key = os.getenv('SECRET_KEY', 'default-secret-key')
            payload = jwt.decode(jwt_token, secret_key, algorithms=['HS256'])
            
            return payload.get('github_token')
            
        except:
            return None
    
    def parse_cookies(self):
        """Parse cookies from request"""
        cookies = {}
        cookie_header = self.headers.get('Cookie', '')
        
        for cookie in cookie_header.split(';'):
            if '=' in cookie:
                key, value = cookie.strip().split('=', 1)
                cookies[key] = value
        
        return cookies
    
    def send_json_response(self, data, status=200):
        """Send JSON response"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Allow-Credentials', 'true')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
