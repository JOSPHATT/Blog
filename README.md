# Team Analysis Blog - Flask Application

A Flask web application that displays football team analysis blog posts from markdown files with YAML frontmatter.

## Features

- **Homepage**: Browse all blog posts with team analysis
- **Team Rankings**: View teams ranked by performance score
- **Search**: Find posts by team name or content
- **Individual Posts**: Detailed view of each team analysis
- **JSON API**: RESTful API endpoint for programmatic access

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt --break-system-packages
```

### 2. Run the Application

```bash
python3 app.py
```

The application will start on `http://localhost:5000`

### 3. Access the Web Interface

- **Homepage**: http://localhost:5000/
- **Teams**: http://localhost:5000/teams
- **Search**: http://localhost:5000/search
- **API**: http://localhost:5000/api/posts

## Application Structure

```
├── app.py                 # Main Flask application
├── posts/                 # Markdown blog posts directory
│   ├── *.md              # Individual team analysis posts
├── templates/             # HTML templates
│   ├── base.html         # Base template with navigation
│   ├── index.html        # Homepage template
│   ├── post.html         # Individual post template
│   ├── teams.html        # Teams ranking template
│   └── search.html       # Search results template
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Blog Post Format

Each blog post is a markdown file with YAML frontmatter:

```markdown
---
title: "Team Analysis: Team Name"
date: 2025-07-11
rank: 1
team: "Team Name"
performance_score: 46.07
---

# Team Name - Performance Analysis

Content goes here...
```

## API Usage

### Get All Posts
```bash
curl http://localhost:5000/api/posts
```

### Search Posts
```bash
curl "http://localhost:5000/search?q=Christchurch"
```

## Development

The Flask app automatically reads all `.md` files from the `posts/` directory and parses their YAML frontmatter to display structured team analysis data.

### Key Components

- **BlogPost Parsing**: Automatic YAML frontmatter extraction
- **Performance Metrics**: Team ranking by performance score
- **Search Functionality**: Full-text search across posts
- **Responsive Design**: Clean, modern web interface

## Data Source

Blog posts are generated from team statistics and contain:
- Team performance scores
- Rankings and match statistics  
- Goals for/against ratios
- Win rates and performance analytics
