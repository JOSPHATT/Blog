#!/usr/bin/env python3
"""
Team Statistics Blog Post Generator

This script fetches team statistics from a CSV file, ranks teams by performance,
and generates markdown blog posts for the top 20 performing teams.
"""

import pandas as pd
import requests
from datetime import datetime
import os
import re

# CSV data URL
CSV_URL = "https://raw.githubusercontent.com/JOSPHATT/Finished_Matches_dash_statistics/refs/heads/main/team_statistics.csv"

def fetch_team_data():
    """Fetch team statistics from the CSV URL"""
    try:
        response = requests.get(CSV_URL)
        response.raise_for_status()
        
        # Save to temporary file and read with pandas
        with open('temp_team_stats.csv', 'w') as f:
            f.write(response.text)
        
        df = pd.read_csv('temp_team_stats.csv')
        
        # Clean up temporary file
        os.remove('temp_team_stats.csv')
        
        print(f"Successfully loaded data for {len(df)} teams")
        return df
        
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def calculate_performance_score(df):
    """Calculate a composite performance score for ranking teams"""
    
    # Handle missing values by filling with 0
    df = df.fillna(0)
    
    # Convert percentage strings to float if needed
    for col in ['win_rate', 'draw_rate', 'loss_rate']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Calculate composite performance score
    # Weighted combination of key metrics
    df['performance_score'] = (
        df['win_rate'] * 0.4 +  # 40% weight on win rate
        df['goal_difference'] * 0.25 +  # 25% weight on goal difference
        df['goals_scored_per_match'] * 0.2 +  # 20% weight on scoring rate
        df['scoring_strength'] * 0.15  # 15% weight on scoring strength
    )
    
    return df

def get_top_performing_teams(df, top_n=20):
    """Get the top N performing teams based on performance score"""
    
    # Calculate performance scores
    df_with_scores = calculate_performance_score(df)
    
    # Sort by performance score and get top N
    top_teams = df_with_scores.nlargest(top_n, 'performance_score')
    
    print(f"Top {top_n} performing teams selected")
    return top_teams

def sanitize_filename(team_name):
    """Sanitize team name for use as filename"""
    # Remove or replace special characters
    sanitized = re.sub(r'[^a-zA-Z0-9\s-]', '', team_name)
    # Replace spaces with hyphens and convert to lowercase
    sanitized = re.sub(r'\s+', '-', sanitized.strip()).lower()
    return sanitized

def generate_blog_post(team_data, rank):
    """Generate a markdown blog post for a team"""
    
    team_name = team_data['TEAM']
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    # Sanitize team name for filename
    filename = sanitize_filename(team_name)
    
    # Create markdown content
    content = f"""---
title: "Team Analysis: {team_name}"
date: {current_date}
rank: {rank}
team: "{team_name}"
performance_score: {team_data['performance_score']:.2f}
---

# {team_name} - Performance Analysis

**Rank:** #{rank} of top performing teams

## Key Statistics

### Match Performance
- **Matches Played:** {team_data['matches_played']}
- **Matches Won:** {team_data['matches_won']}
- **Matches Drawn:** {team_data['matches_drawn']}
- **Matches Lost:** {team_data['matches_lost']}
- **Win Rate:** {team_data['win_rate']:.1f}%

### Goal Statistics
- **Goals For:** {team_data['goals_for']}
- **Goals Against:** {team_data['goals_against']}
- **Goal Difference:** {team_data['goal_difference']:+d}
- **Goals Scored per Match:** {team_data['goals_scored_per_match']:.2f}
- **Goals Conceded per Match:** {team_data['goals_conceded_per_match']:.2f}

### Performance Metrics
- **Performance Score:** {team_data['performance_score']:.2f}
- **Scoring Strength:** {team_data['scoring_strength']:.2f}
- **Goal Difference per Match:** {team_data['goal_difference_per_match']:.2f}

## Analysis

{team_name} ranks #{rank} among top performing teams with a performance score of {team_data['performance_score']:.2f}.

### Strengths
"""

    # Add analysis based on statistics
    if team_data['win_rate'] > 60:
        content += f"- **High Win Rate**: With a {team_data['win_rate']:.1f}% win rate, {team_name} demonstrates consistent winning performance.\n"
    
    if team_data['goal_difference'] > 0:
        content += f"- **Positive Goal Difference**: A goal difference of {team_data['goal_difference']:+d} shows strong defensive and offensive balance.\n"
    
    if team_data['goals_scored_per_match'] > 1.5:
        content += f"- **Strong Attack**: Averaging {team_data['goals_scored_per_match']:.2f} goals per match demonstrates potent offensive capabilities.\n"
    
    if team_data['goals_conceded_per_match'] < 1.0:
        content += f"- **Solid Defense**: Conceding only {team_data['goals_conceded_per_match']:.2f} goals per match shows defensive strength.\n"

    content += """
### Key Metrics Summary

This team's performance is based on a composite score considering:
- Win rate (40% weight)
- Goal difference (25% weight) 
- Goals scored per match (20% weight)
- Scoring strength (15% weight)

*Data sourced from match statistics and performance analytics.*
"""

    return filename, content

def create_blog_posts(top_teams):
    """Create markdown blog posts for all top teams"""
    
    # Ensure posts directory exists
    os.makedirs('posts', exist_ok=True)
    
    generated_posts = []
    
    for rank, (_, team_data) in enumerate(top_teams.iterrows(), 1):
        filename, content = generate_blog_post(team_data, rank)
        
        # Create full filepath
        post_filename = f"posts/{datetime.now().strftime('%Y-%m-%d')}-{filename}-analysis.md"
        
        # Write blog post
        with open(post_filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        generated_posts.append(post_filename)
        print(f"Generated post for #{rank}: {team_data['TEAM']} -> {post_filename}")
    
    return generated_posts

def main():
    """Main function to orchestrate the blog post generation"""
    
    print("Fetching team statistics data...")
    df = fetch_team_data()
    
    if df is None:
        print("Failed to fetch data. Exiting.")
        return
    
    print(f"Data columns: {list(df.columns)}")
    print(f"Total teams in dataset: {len(df)}")
    
    print("\nCalculating performance scores and selecting top 20 teams...")
    top_teams = get_top_performing_teams(df, top_n=20)
    
    print("\nTop 5 teams preview:")
    print(top_teams[['TEAM', 'win_rate', 'goal_difference', 'performance_score']].head())
    
    print("\nGenerating blog posts...")
    generated_posts = create_blog_posts(top_teams)
    
    print(f"\nCompleted! Generated {len(generated_posts)} blog posts:")
    for post in generated_posts:
        print(f"  - {post}")
    
    # Generate summary post
    summary_content = f"""---
title: "Top 20 Performing Teams - Summary"
date: {datetime.now().strftime('%Y-%m-%d')}
---

# Top 20 Performing Teams Analysis

Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Rankings

"""
    
    for rank, (_, team_data) in enumerate(top_teams.iterrows(), 1):
        summary_content += f"{rank}. **{team_data['TEAM']}** - Performance Score: {team_data['performance_score']:.2f}\n"
    
    summary_content += f"""
## Methodology

Teams are ranked using a composite performance score calculated from:
- Win Rate (40% weight)
- Goal Difference (25% weight)
- Goals Scored per Match (20% weight)
- Scoring Strength (15% weight)

Total teams analyzed: {len(df)}
Data source: {CSV_URL}
"""
    
    summary_filename = f"posts/{datetime.now().strftime('%Y-%m-%d')}-top-20-teams-summary.md"
    with open(summary_filename, 'w', encoding='utf-8') as f:
        f.write(summary_content)
    
    print(f"\nSummary post created: {summary_filename}")

if __name__ == "__main__":
    main()