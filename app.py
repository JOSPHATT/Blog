#!/usr/bin/env python3
"""
Flask Blog Application

This Flask app displays blog posts from the posts directory.
"""

from flask import Flask, render_template, abort, request, jsonify
import os
import glob
import re
from datetime import datetime

app = Flask(__name__)

def parse_frontmatter(content):
    """Parse YAML frontmatter from markdown content"""
    if not content.startswith('---'):
        return {}, content
    
    parts = content.split('---', 2)
    if len(parts) < 3:
        return {}, content
    
    frontmatter_text = parts[1].strip()
    content = parts[2].strip()
    
    # Simple YAML parsing for our specific format
    metadata = {}
    for line in frontmatter_text.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip().strip('"')
            
            # Convert numeric values
            if value.replace('.', '').isdigit():
                value = float(value) if '.' in value else int(value)
            
            metadata[key] = value
    
    return metadata, content

def load_posts():
    """Load all blog posts from the posts directory"""
    posts = []
    posts_dir = 'posts'
    
    if not os.path.exists(posts_dir):
        return posts
    
    # Find all markdown files
    markdown_files = glob.glob(os.path.join(posts_dir, '*.md'))
    
    for filepath in markdown_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            metadata, post_content = parse_frontmatter(content)
            
            post = {
                'filename': os.path.basename(filepath),
                'slug': os.path.basename(filepath).replace('.md', ''),
                'title': metadata.get('title', 'Untitled'),
                'date': metadata.get('date', '2025-07-11'),
                'team': metadata.get('team', 'Unknown'),
                'rank': metadata.get('rank', None),
                'performance_score': metadata.get('performance_score', None),
                'content': post_content,
                'metadata': metadata
            }
            posts.append(post)
            
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
    
    return posts

@app.route('/')
def index():
    """Homepage showing all blog posts"""
    posts = load_posts()
    
    # Sort by date and rank
    posts.sort(key=lambda x: (x['date'], x['rank'] or 999), reverse=True)
    
    return render_template('index.html', posts=posts)

@app.route('/post/<slug>')
def post_detail(slug):
    """Display a specific blog post"""
    posts = load_posts()
    
    post = None
    for p in posts:
        if p['slug'] == slug:
            post = p
            break
    
    if not post:
        abort(404)
    
    return render_template('post.html', post=post)

@app.route('/teams')
def teams():
    """List all teams with their performance scores"""
    posts = load_posts()
    
    # Filter for team analysis posts
    team_posts = [p for p in posts if p['team'] and p['team'] != 'Unknown' and 'summary' not in p['title'].lower()]
    
    # Sort by performance score
    team_posts.sort(key=lambda x: x['performance_score'] or 0, reverse=True)
    
    return render_template('teams.html', posts=team_posts)

@app.route('/api/posts')
def api_posts():
    """JSON API endpoint for posts data"""
    posts = load_posts()
    return jsonify({'posts': posts})

@app.route('/search')
def search():
    """Search posts by team name or content"""
    query = request.args.get('q', '').lower()
    posts = load_posts()
    
    if not query:
        return render_template('search.html', posts=[], query='')
    
    # Search in title, team name, and content
    matching_posts = []
    for post in posts:
        if (query in post['title'].lower() or 
            query in post['team'].lower() or 
            query in post['content'].lower()):
            matching_posts.append(post)
    
    return render_template('search.html', posts=matching_posts, query=query)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)