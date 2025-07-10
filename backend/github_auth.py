"""
GitHub OAuth Authentication Backend
Handles GitHub OAuth flow and token exchange
"""

from flask import Flask, request, jsonify, redirect, session
from flask_cors import CORS
import os
import requests
import secrets
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, supports_credentials=True)

# Configuration
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))
GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET')
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')

# GitHub OAuth URLs
GITHUB_AUTH_URL = 'https://github.com/login/oauth/authorize'
GITHUB_TOKEN_URL = 'https://github.com/login/oauth/access_token'
GITHUB_API_URL = 'https://api.github.com'

@app.route('/auth/github/login', methods=['GET'])
def github_login():
    """Initiate GitHub OAuth flow"""
    
    # Generate state parameter for security
    state = secrets.token_urlsafe(32)
    session['oauth_state'] = state
    
    # Build GitHub authorization URL
    params = {
        'client_id': GITHUB_CLIENT_ID,
        'redirect_uri': f"{request.host_url}auth/github/callback",
        'scope': 'repo,user:email',
        'state': state,
        'allow_signup': 'true'
    }
    
    auth_url = GITHUB_AUTH_URL + '?' + '&'.join([f"{k}={v}" for k, v in params.items()])
    
    return redirect(auth_url)

@app.route('/auth/github/callback', methods=['GET'])
def github_callback():
    """Handle GitHub OAuth callback"""
    
    # Get parameters from callback
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')
    
    # Check for errors
    if error:
        return redirect(f"{FRONTEND_URL}/login.html?error={error}")
    
    # Verify state parameter
    if not state or state != session.get('oauth_state'):
        return redirect(f"{FRONTEND_URL}/login.html?error=invalid_state")
    
    # Clear state from session
    session.pop('oauth_state', None)
    
    if not code:
        return redirect(f"{FRONTEND_URL}/login.html?error=no_code")
    
    try:
        # Exchange code for access token
        token_data = exchange_code_for_token(code)
        
        # Get user information
        user_data = get_github_user(token_data['access_token'])
        
        # Store token and user data in session (in production, use secure storage)
        session['github_token'] = token_data['access_token']
        session['github_user'] = user_data
        
        # Redirect to main app with success
        return redirect(f"{FRONTEND_URL}/?auth=success")
        
    except Exception as e:
        print(f"OAuth error: {e}")
        return redirect(f"{FRONTEND_URL}/login.html?error=auth_failed")

def exchange_code_for_token(code):
    """Exchange authorization code for access token"""
    
    data = {
        'client_id': GITHUB_CLIENT_ID,
        'client_secret': GITHUB_CLIENT_SECRET,
        'code': code,
        'redirect_uri': f"{request.host_url}auth/github/callback"
    }
    
    headers = {
        'Accept': 'application/json',
        'User-Agent': 'Tekshila-App'
    }
    
    response = requests.post(GITHUB_TOKEN_URL, data=data, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Token exchange failed: {response.status_code}")
    
    token_data = response.json()
    
    if 'error' in token_data:
        raise Exception(f"GitHub error: {token_data['error_description']}")
    
    return token_data

def get_github_user(access_token):
    """Get user information from GitHub API"""
    
    headers = {
        'Authorization': f'token {access_token}',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'Tekshila-App'
    }
    
    response = requests.get(f"{GITHUB_API_URL}/user", headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Failed to get user info: {response.status_code}")
    
    return response.json()

@app.route('/auth/user', methods=['GET'])
def get_current_user():
    """Get current authenticated user"""
    
    if 'github_token' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # Verify token is still valid
        user_data = get_github_user(session['github_token'])
        
        return jsonify({
            'user': user_data,
            'token': session['github_token']
        })
        
    except Exception as e:
        # Token is invalid, clear session
        session.pop('github_token', None)
        session.pop('github_user', None)
        return jsonify({'error': 'Invalid token'}), 401

@app.route('/auth/logout', methods=['POST'])
def logout():
    """Logout user and clear session"""
    
    session.pop('github_token', None)
    session.pop('github_user', None)
    
    return jsonify({'success': True})

@app.route('/api/github/repos', methods=['GET'])
def get_repositories():
    """Get user repositories"""
    
    if 'github_token' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        headers = {
            'Authorization': f'token {session["github_token"]}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Tekshila-App'
        }
        
        # Get repositories
        params = {
            'sort': request.args.get('sort', 'updated'),
            'per_page': 100,
            'type': 'all'
        }
        
        response = requests.get(f"{GITHUB_API_URL}/user/repos", 
                              headers=headers, params=params)
        
        if response.status_code != 200:
            return jsonify({'error': 'Failed to fetch repositories'}), 500
        
        return jsonify(response.json())
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/github/repos/<owner>/<repo>/branches', methods=['GET'])
def get_branches(owner, repo):
    """Get repository branches"""
    
    if 'github_token' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        headers = {
            'Authorization': f'token {session["github_token"]}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Tekshila-App'
        }
        
        response = requests.get(f"{GITHUB_API_URL}/repos/{owner}/{repo}/branches", 
                              headers=headers)
        
        if response.status_code != 200:
            return jsonify({'error': 'Failed to fetch branches'}), 500
        
        return jsonify(response.json())
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/github/repos/<owner>/<repo>/pulls', methods=['POST'])
def create_pull_request(owner, repo):
    """Create a pull request"""
    
    if 'github_token' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        
        headers = {
            'Authorization': f'token {session["github_token"]}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Tekshila-App',
            'Content-Type': 'application/json'
        }
        
        # First, create a new branch
        branch_name = f"docs/ai-generated-{secrets.token_hex(4)}"
        
        # Get base branch SHA
        base_response = requests.get(
            f"{GITHUB_API_URL}/repos/{owner}/{repo}/git/ref/heads/{data['base']}", 
            headers=headers
        )
        
        if base_response.status_code != 200:
            return jsonify({'error': 'Failed to get base branch'}), 500
        
        base_sha = base_response.json()['object']['sha']
        
        # Create new branch
        branch_data = {
            'ref': f"refs/heads/{branch_name}",
            'sha': base_sha
        }
        
        branch_response = requests.post(
            f"{GITHUB_API_URL}/repos/{owner}/{repo}/git/refs",
            headers=headers,
            json=branch_data
        )
        
        if branch_response.status_code != 201:
            return jsonify({'error': 'Failed to create branch'}), 500
        
        # Create or update file
        file_content = data.get('content', '')
        filename = data.get('filename', 'README.md')
        commit_message = data.get('commit_message', 'Add AI-generated documentation')
        
        # Encode content to base64
        import base64
        encoded_content = base64.b64encode(file_content.encode('utf-8')).decode('utf-8')
        
        file_data = {
            'message': commit_message,
            'content': encoded_content,
            'branch': branch_name
        }
        
        # Try to get existing file first
        try:
            existing_response = requests.get(
                f"{GITHUB_API_URL}/repos/{owner}/{repo}/contents/{filename}",
                headers=headers,
                params={'ref': branch_name}
            )
            
            if existing_response.status_code == 200:
                file_data['sha'] = existing_response.json()['sha']
        except:
            pass  # File doesn't exist, will create new
        
        file_response = requests.put(
            f"{GITHUB_API_URL}/repos/{owner}/{repo}/contents/{filename}",
            headers=headers,
            json=file_data
        )
        
        if file_response.status_code not in [200, 201]:
            return jsonify({'error': 'Failed to create/update file'}), 500
        
        # Create pull request
        pr_data = {
            'title': data.get('title', 'Add AI-generated documentation'),
            'body': data.get('body', 'This PR adds comprehensive documentation generated by AI.'),
            'head': branch_name,
            'base': data['base']
        }
        
        pr_response = requests.post(
            f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls",
            headers=headers,
            json=pr_data
        )
        
        if pr_response.status_code != 201:
            return jsonify({'error': 'Failed to create pull request'}), 500
        
        pr_result = pr_response.json()
        
        return jsonify({
            'success': True,
            'pr_number': pr_result['number'],
            'pr_url': pr_result['html_url'],
            'branch': branch_name
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'GitHub OAuth Backend'
    })

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Check required environment variables
    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        print("Error: GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET must be set")
        exit(1)
    
    print("Starting GitHub OAuth Backend...")
    print(f"Client ID: {GITHUB_CLIENT_ID}")
    print(f"Frontend URL: {FRONTEND_URL}")
    print("\nAvailable endpoints:")
    print("  GET  /health - Health check")
    print("  GET  /auth/github/login - Initiate OAuth")
    print("  GET  /auth/github/callback - OAuth callback")
    print("  GET  /auth/user - Get current user")
    print("  POST /auth/logout - Logout")
    print("  GET  /api/github/repos - Get repositories")
    print("  GET  /api/github/repos/<owner>/<repo>/branches - Get branches")
    print("  POST /api/github/repos/<owner>/<repo>/pulls - Create PR")
    print("\nServer running on http://localhost:5000")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
