# git_server.py
from flask import Flask, jsonify, request
import subprocess
import os

app = Flask(__name__)

# Configuration - Update these to match your setup
REPO_PATH = r"C:\Users\Zarni\Desktop\GitTerminalAndroid"  # No spaces now!
GIT_REMOTE = "origin"  # Your remote name
BRANCH = "main"       # Your branch name
PORT = 5000           # Port to run the server

def run_git_command(args):
    """Helper function to run git commands safely"""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=REPO_PATH,
            capture_output=True,
            text=True,
            shell=True,  # Required for Windows
            check=True
        )
        return {"success": True, "output": result.stdout.strip()}
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": e.stderr.strip()}

@app.route('/api/commits', methods=['GET'])
def get_commits():
    """Get the last 3 commits"""
    result = run_git_command(["log", "-3", "--pretty=format:%h|%an|%ad|%s", "--date=short"])
    
    if not result["success"]:
        return jsonify({"status": "error", "message": result["error"]}), 500
    
    commits = [commit.split("|") for commit in result["output"].split("\n") if commit]
    
    return jsonify({
        "status": "success",
        "commits": [
            {
                "hash": c[0],
                "author": c[1],
                "date": c[2],
                "message": c[3]
            } for c in commits
        ]
    })

@app.route('/api/push', methods=['POST'])
def push_changes():
    """Pull latest changes and push"""
    # First pull to avoid conflicts
    pull_result = run_git_command(["pull", GIT_REMOTE, BRANCH])
    if not pull_result["success"]:
        return jsonify({"status": "error", "message": pull_result["error"]}), 500
    
    # Then push changes
    push_result = run_git_command(["push", GIT_REMOTE, BRANCH])
    
    return jsonify({
        "status": "success" if push_result["success"] else "error",
        "pull_output": pull_result["output"],
        "push_output": push_result.get("output", push_result.get("error", ""))
    })

@app.route('/api/status', methods=['GET'])
def repo_status():
    """Get current git status"""
    status_result = run_git_command(["status"])
    return jsonify({
        "status": "success" if status_result["success"] else "error",
        "data": status_result["output"] if status_result["success"] else status_result["error"]
    })

if __name__ == '__main__':
    # Verify repo exists
    if not os.path.exists(os.path.join(REPO_PATH, ".git")):
        print(f"ERROR: No git repository found at {REPO_PATH}")
        print("Please clone your repo to this location first")
    else:
        print(f"Starting Git Server for repository at {REPO_PATH}")
        print(f"API endpoints available at http://localhost:{PORT}/api/")
        app.run(host='0.0.0.0', port=PORT, debug=True)