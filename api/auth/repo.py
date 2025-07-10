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
import base64
import secrets

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        if self.path.startswith('/api/github/repos'):
            self.handle_get_repos()
        else:
            self.send_error(404, "Not Found")
    
    def do_POST(self):
        """Handle POST requests"""
        if '/pulls' in self.path:
            self.handle_create_pr()
        else:
            self.send_error(404, "Not Found")
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Allow-Credentials', 'true')
        self.end_headers()
    
    def handle_get_repos(self):
        """Get repositories or branches"""
        try:
            # Get authentication
            github_token = self.get_github_token()
            if not github_token:
                self.send_json_response({'error': 'Not authenticated'}, 401)
                return
            
            # Parse path to determine what to fetch
            path_parts = self.path.split('/')
            
            if len(path_parts) == 4:  # /api/github/repos
                self.get_repositories(github_token)
            elif len(path_parts) == 7 and path_parts[6] == 'branches':  # /api/github/repos/owner/repo/branches
                owner = path_parts[4]
                repo = path_parts[5]
                self.get_branches(github_token, owner, repo)
            else:
                self.send_error(404, "Not Found")
                
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)
    
    def handle_create_pr(self):
        """Create pull request"""
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
            
            # Create pull request
            result = self.create_pull_request(github_token, owner, repo, data)
            self.send_json_response(result)
            
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)
    
    def get_repositories(self, github_token):
        """Get user repositories"""
        try:
            # Parse query parameters
            parsed_url = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed_url.query)
            sort = params.get('sort', ['updated'])[0]
            
            req = urllib.request.Request(
                f'https://api.github.com/user/repos?sort={sort}&per_page=100&type=all',
                headers={
                    'Authorization': f'token {github_token}',
                    'Accept': 'application/vnd.github.v3+json',
                    'User-Agent': 'Tekshila-App'
                }
            )
            
            with urllib.request.urlopen(req) as response:
                if response.status != 200:
                    raise Exception(f"Failed to fetch repositories: {response.status}")
                
                repos = json.loads(response.read().decode())
                self.send_json_response(repos)
                
        except Exception as e:
            raise Exception(f"Failed to get repositories: {str(e)}")
    
    def get_branches(self, github_token, owner, repo):
        """Get repository branches"""
        try:
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
                    raise Exception(f"Failed to fetch branches: {response.status}")
                
                branches = json.loads(response.read().decode())
                self.send_json_response(branches)
                
        except Exception as e:
            raise Exception(f"Failed to get branches: {str(e)}")
    
    def create_pull_request(self, github_token, owner, repo, data):
        """Create a pull request with documentation"""
        try:
            # Create new branch
            branch_name = f"docs/ai-generated-{secrets.token_hex(4)}"
            
            # Get base branch SHA
            base_branch = data.get('base', 'main')
            req = urllib.request.Request(
                f'https://api.github.com/repos/{owner}/{repo}/git/ref/heads/{base_branch}',
                headers={
                    'Authorization': f'token {github_token}',
                    'Accept': 'application/vnd.github.v3+json',
                    'User-Agent': 'Tekshila-App'
                }
            )
            
            with urllib.request.urlopen(req) as response:
                if response.status != 200:
                    raise Exception(f"Failed to get base branch: {response.status}")
                
                base_ref = json.loads(response.read().decode())
                base_sha = base_ref['object']['sha']
            
            # Create new branch
            branch_data = {
                'ref': f'refs/heads/{branch_name}',
                'sha': base_sha
            }
            
            req = urllib.request.Request(
                f'https://api.github.com/repos/{owner}/{repo}/git/refs',
                data=json.dumps(branch_data).encode(),
                headers={
                    'Authorization': f'token {github_token}',
                    'Accept': 'application/vnd.github.v3+json',
                    'User-Agent': 'Tekshila-App',
                    'Content-Type': 'application/json'
                }
            )
            
            with urllib.request.urlopen(req) as response:
                if response.status != 201:
                    raise Exception(f"Failed to create branch: {response.status}")
            
            # Create/update file
            filename = data.get('filename', 'README.md')
            file_content = data.get('content', '')
            commit_message = data.get('commit_message', 'Add AI-generated documentation')
            
            # Encode content
            encoded_content = base64.b64encode(file_content.encode('utf-8')).decode('utf-8')
            
            file_data = {
                'message': commit_message,
                'content': encoded_content,
                'branch': branch_name
            }
            
            # Try to get existing file
            try:
                req = urllib.request.Request(
                    f'https://api.github.com/repos/{owner}/{repo}/contents/{filename}?ref={branch_name}',
                    headers={
                        'Authorization': f'token {github_token}',
                        'Accept': 'application/vnd.github.v3+json',
                        'User-Agent': 'Tekshila-App'
                    }
                )
                
                with urllib.request.urlopen(req) as response:
                    if response.status == 200:
                        existing_file = json.loads(response.read().decode())
                        file_data['sha'] = existing_file['sha']
            except:
                pass  # File doesn't exist, will create new
            
            # Create/update file
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
                    raise Exception(f"Failed to create/update file: {response.status}")
            
            # Create pull request
            pr_data = {
                'title': data.get('title', 'Add AI-generated documentation'),
                'body': data.get('body', 'This PR adds comprehensive documentation generated by AI.'),
                'head': branch_name,
                'base': base_branch
            }
            
            req = urllib.request.Request(
                f'https://api.github.com/repos/{owner}/{repo}/pulls',
                data=json.dumps(pr_data).encode(),
                headers={
                    'Authorization': f'token {github_token}',
                    'Accept': 'application/vnd.github.v3+json',
                    'User-Agent': 'Tekshila-App',
                    'Content-Type': 'application/json'
                }
            )
            
            with urllib.request.urlopen(req) as response:
                if response.status != 201:
                    raise Exception(f"Failed to create pull request: {response.status}")
                
                pr_result = json.loads(response.read().decode())
                
                return {
                    'success': True,
                    'pr_number': pr_result['number'],
                    'pr_url': pr_result['html_url'],
                    'branch': branch_name
                }
                
        except Exception as e:
            raise Exception(f"Failed to create pull request: {str(e)}")
    
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
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Allow-Credentials', 'true')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())