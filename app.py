#!/usr/bin/env python3
"""
Flask Blog Application

This Flask app fetches and displays blog posts from the posts directory.
It parses markdown files with YAML frontmatter and provides a web interface
to browse team analysis posts.
"""

from flask import Flask, render_template, abort, request
import frontmatter
import markdown
import os
from datetime import datetime
import glob

app = Flask(__name__)

class BlogPost:
    """Class to represent a blog post with metadata and content"""
    
    def __init__(self, filepath):
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        
        # Load and parse the markdown file
        with open(filepath, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)
            
        # Extract metadata from frontmatter
        self.metadata = post.metadata
        self.title = self.metadata.get('title', 'Untitled')
        self.date = self.metadata.get('date', datetime.now())
        self.rank = self.metadata.get('rank', None)
        self.team = self.metadata.get('team', 'Unknown Team')
        self.performance_score = self.metadata.get('performance_score', None)
        
        # Convert content to HTML
        self.content = post.content
        self.html_content = markdown.markdown(self.content)
        
        # Generate slug from filename
        self.slug = self.filename.replace('.md', '')

def load_all_posts():
    """Load all blog posts from the posts directory"""
    posts = []
    posts_dir = 'posts'
    
    if not os.path.exists(posts_dir):
        return posts
        
    # Find all markdown files
    markdown_files = glob.glob(os.path.join(posts_dir, '*.md'))
    
    for filepath in markdown_files:
        try:
            post = BlogPost(filepath)
            posts.append(post)
        except Exception as e:
            print(f"Error loading post {filepath}: {e}")
            continue
    
    return posts

def get_post_by_slug(slug):
    """Get a specific post by its slug"""
    posts = load_all_posts()
    for post in posts:
        if post.slug == slug:
            return post
    return None

@app.route('/')
def index():
    """Homepage showing all blog posts"""
    posts = load_all_posts()
    
    # Sort posts by date (newest first) and then by rank
    posts.sort(key=lambda x: (x.date if isinstance(x.date, datetime) else datetime.strptime(str(x.date), '%Y-%m-%d'), x.rank or 999), reverse=True)
    
    return render_template('index.html', posts=posts)

@app.route('/post/<slug>')
def post_detail(slug):
    """Display a specific blog post"""
    post = get_post_by_slug(slug)
    if not post:
        abort(404)
    
    return render_template('post.html', post=post)

@app.route('/teams')
def teams():
    """List all teams with their performance scores"""
    posts = load_all_posts()
    
    # Filter for team analysis posts (not summary posts)
    team_posts = [p for p in posts if p.team and p.team != 'Unknown Team' and 'summary' not in p.title.lower()]
    
    # Sort by performance score (highest first)
    team_posts.sort(key=lambda x: x.performance_score or 0, reverse=True)
    
    return render_template('teams.html', posts=team_posts)

@app.route('/api/posts')
def api_posts():
    """JSON API endpoint for posts data"""
    posts = load_all_posts()
    
    posts_data = []
    for post in posts:
        posts_data.append({
            'slug': post.slug,
            'title': post.title,
            'date': str(post.date),
            'team': post.team,
            'rank': post.rank,
            'performance_score': post.performance_score,
            'metadata': post.metadata
        })
    
    return {'posts': posts_data}

@app.route('/search')
def search():
    """Search posts by team name or content"""
    query = request.args.get('q', '').lower()
    if not query:
        return render_template('search.html', posts=[], query='')
    
    posts = load_all_posts()
    
    # Search in title, team name, and content
    matching_posts = []
    for post in posts:
        if (query in post.title.lower() or 
            query in post.team.lower() or 
            query in post.content.lower()):
            matching_posts.append(post)
    
    return render_template('search.html', posts=matching_posts, query=query)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)