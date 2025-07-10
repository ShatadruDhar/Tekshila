"""
Vercel Serverless API for GitHub Repository Operations
File: api/github/repos.py
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.parse
import urllib.request
import jwt
import re
import secrets

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests for repositories and branches"""
        path = self.path
        
        if path == '/api/github/repos':
            self.handle_get_repositories()
        elif re.match(r'/api/github/repos/[\w.-]+/[\w.-]+/branches', path):
            self.handle_get_branches()
        else:
            self.send_error(404, "Not Found")
    
    def do_POST(self):
        """Handle POST requests for pull requests"""
        path = self.path
        
        if re.match(r'/api/github/repos/[\w.-]+/[\w.-]+/pulls', path):
            self.handle_create_pull_request()
        else:
            self.send_error(404, "Not Found")
    
    def handle_get_repositories(self):
        """Get user repositories"""
        try:
            github_token = self.get_github_token()
            if not github_token:
                self.send_json_response({'error': 'Not authenticated'}, 401)
                return
            
            # Get repositories from GitHub API
            req = urllib.request.Request(
                'https://api.github.com/user/repos?sort=updated&per_page=100',
                headers={
                    'Authorization': f'token {github_token}',
                    'Accept': 'application/vnd.github.v3+json',
                    'User-Agent': 'Tekshila-App'
                }
            )
            
            with urllib.request.urlopen(req) as response:
                if response.status != 200:
                    raise Exception(f"GitHub API error: {response.status}")
                
                repos = json.loads(response.read().decode())
                self.send_json_response(repos)
                
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)
    
    def handle_get_branches(self):
        """Get repository branches"""
        try:
            github_token = self.get_github_token()
            if not github_token:
                self.send_json_response({'error': 'Not authenticated'}, 401)
                return
            
            # Extract owner and repo from path
            path_parts = self.path.split('/')
            owner = path_parts[4]  # /api/github/repos/{owner}/{repo}/branches
            repo = path_parts[5]
            
            # Get branches from GitHub API
            req = urllib.request.Request(
                f'https://api.github.com/repos/{owner}/{repo}/branches',
                headers={
                    'Authorization': f'token {github_token}',
                    'Accept': 'application/vnd.github.v3+json',
                    'User-Agent': 'Tekshila-App'
                }
            )
            
            with urllib.request.urlopen(req) as response:
                if response.status != 200:
                    raise Exception(f"GitHub API error: {response.status}")
                
                branches = json.loads(response.read().decode())
                self.send_json_response(branches)
                
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)
    
    def handle_create_pull_request(self):
        """Create a pull request"""
        try:
            github_token = self.get_github_token()
            if not github_token:
                self.send_json_response({'error': 'Not authenticated'}, 401)
                return
            
            # Extract owner and repo from path
            path_parts = self.path.split('/')
            owner = path_parts[4]  # /api/github/repos/{owner}/{repo}/pulls
            repo = path_parts[5]
            
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)
            
            # Create a new branch for the PR
            new_branch_name = f"docs/ai-generated-{secrets.token_hex(4)}"
            
            # Get base branch SHA
            base_branch = data.get('base', 'main')
            branch_req = urllib.request.Request(
                f'https://api.github.com/repos/{owner}/{repo}/git/ref/heads/{base_branch}',
                headers={
                    'Authorization': f'token {github_token}',
                    'Accept': 'application/vnd.github.v3+json',
                    'User-Agent': 'Tekshila-App'
                }
            )
            
            with urllib.request.urlopen(branch_req) as response:
                if response.status != 200:
                    raise Exception(f"Failed to get base branch: {response.status}")
                branch_data = json.loads(response.read().decode())
                base_sha = branch_data['object']['sha']
            
            # Create new branch
            create_branch_data = {
                'ref': f'refs/heads/{new_branch_name}',
                'sha': base_sha
            }
            
            branch_create_req = urllib.request.Request(
                f'https://api.github.com/repos/{owner}/{repo}/git/refs',
                data=json.dumps(create_branch_data).encode(),
                headers={
                    'Authorization': f'token {github_token}',
                    'Accept': 'application/vnd.github.v3+json',
                    'User-Agent': 'Tekshila-App',
                    'Content-Type': 'application/json'
                }
            )
            
            with urllib.request.urlopen(branch_create_req) as response:
                if response.status not in [200, 201]:
                    raise Exception(f"Failed to create branch: {response.status}")
            
            # Create or update file
            filename = data.get('filename', 'README.md')
            content = data.get('content', '')
            commit_message = data.get('commit_message', 'Add documentation')
            
            # Encode content to base64
            import base64
            encoded_content = base64.b64encode(content.encode('utf-8')).decode('ascii')
            
            file_data = {
                'message': commit_message,
                'content': encoded_content,
                'branch': new_branch_name
            }
            
            # Try to get existing file first
            try:
                existing_file_req = urllib.request.Request(
                    f'https://api.github.com/repos/{owner}/{repo}/contents/{filename}?ref={new_branch_name}',
                    headers={
                        'Authorization': f'token {github_token}',
                        'Accept': 'application/vnd.github.v3+json',
                        'User-Agent': 'Tekshila-App'
                    }
                )
                
                with urllib.request.urlopen(existing_file_req) as response:
                    if response.status == 200:
                        existing_data = json.loads(response.read().decode())
                        file_data['sha'] = existing_data['sha']
            except:
                pass  # File doesn't exist, create new one
            
            file_req = urllib.request.Request(
                f'https://api.github.com/repos/{owner}/{repo}/contents/{filename}',
                data=json.dumps(file_data).encode(),
                headers={
                    'Authorization': f'token {github_token}',
                    'Accept': 'application/vnd.github.v3+json',
                    'User-Agent': 'Tekshila-App',
                    'Content-Type': 'application/json'
                }
            )
            file_req.get_method = lambda: 'PUT'
            
            with urllib.request.urlopen(file_req) as response:
                if response.status not in [200, 201]:
                    raise Exception(f"Failed to create file: {response.status}")
            
            # Create pull request
            pr_data = {
                'title': data.get('title', 'Add AI-generated documentation'),
                'body': data.get('body', 'This PR adds documentation generated by AI.'),
                'head': new_branch_name,
                'base': base_branch
            }
            
            pr_req = urllib.request.Request(
                f'https://api.github.com/repos/{owner}/{repo}/pulls',
                data=json.dumps(pr_data).encode(),
                headers={
                    'Authorization': f'token {github_token}',
                    'Accept': 'application/vnd.github.v3+json',
                    'User-Agent': 'Tekshila-App',
                    'Content-Type': 'application/json'
                }
            )
            
            with urllib.request.urlopen(pr_req) as response:
                if response.status not in [200, 201]:
                    raise Exception(f"Failed to create PR: {response.status}")
                
                pr_result = json.loads(response.read().decode())
                self.send_json_response({
                    'pr_url': pr_result['html_url'],
                    'pr_number': pr_result['number']
                })
                
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)
    
    def get_github_token(self):
        """Extract GitHub token from JWT cookie"""
        try:
            cookies = self.parse_cookies()
            jwt_token = cookies.get('auth_token')
            
            if not jwt_token:
                return None
            
            # Decode JWT token
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
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Allow-Credentials', 'true')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Allow-Credentials', 'true')
        self.end_headers()
