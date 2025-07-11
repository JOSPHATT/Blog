#!/usr/bin/env python3
"""
Team Statistics Blog Post Generator

This script fetches team statistics from a CSV file, removes duplicate entries,
ranks teams by performance, and generates markdown blog posts for the top 20 
performing teams.

Features:
- Automatic duplicate team removal (keeps first occurrence)
- Composite performance scoring with weighted metrics
- Automated blog post generation in markdown format
"""

import pandas as pd
import requests
from datetime import datetime
import os
import re

# CSV data URL
CSV_URL = "https://raw.githubusercontent.com/JOSPHATT/Finished_Matches_dash_statistics/refs/heads/main/team_statistics.csv"

def remove_duplicates(df):
    """Remove duplicate team entries from the dataframe"""
    if df is None or df.empty:
        return df
    
    initial_count = len(df)
    
    # Check if TEAM column exists
    if 'TEAM' not in df.columns:
        print("Warning: 'TEAM' column not found. Checking for alternative team column names...")
        # Look for potential team column names
        team_columns = [col for col in df.columns if 'team' in col.lower() or 'name' in col.lower()]
        if team_columns:
            print(f"Found potential team column: {team_columns[0]}")
            df = df.rename(columns={team_columns[0]: 'TEAM'})
        else:
            print("No team column found. Using first column as team identifier.")
            df = df.rename(columns={df.columns[0]: 'TEAM'})
    
    # Remove duplicates based on team name, keeping the first occurrence
    df_cleaned = df.drop_duplicates(subset=['TEAM'], keep='first')
    
    duplicates_removed = initial_count - len(df_cleaned)
    
    if duplicates_removed > 0:
        print(f"Removed {duplicates_removed} duplicate team entries")
        print(f"Teams after duplicate removal: {len(df_cleaned)}")
    else:
        print("No duplicate teams found")
    
    return df_cleaned

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
        
        # Remove duplicate teams
        df = remove_duplicates(df)
        
        return df
        
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def detect_column_names(df):
    """Detect and map column names to standardized names"""
    column_mapping = {}
    
    # Column name variations for different metrics
    column_patterns = {
        'win_rate': ['win_rate', 'win%', 'win_percentage', 'wins_percentage', 'win_pct'],
        'goal_difference': ['goal_difference', 'goal_diff', 'gd', 'goals_difference'],
        'goals_scored_per_match': ['goals_scored_per_match', 'goals_per_match', 'avg_goals_scored', 'goals_avg'],
        'scoring_strength': ['scoring_strength', 'attack_strength', 'offensive_strength', 'scoring_rate'],
        'matches_played': ['matches_played', 'games_played', 'matches', 'games'],
        'matches_won': ['matches_won', 'wins', 'games_won', 'matches_w'],
        'matches_drawn': ['matches_drawn', 'draws', 'games_drawn', 'matches_d'],
        'matches_lost': ['matches_lost', 'losses', 'games_lost', 'matches_l'],
        'goals_for': ['goals_for', 'goals_scored', 'gf', 'goals'],
        'goals_against': ['goals_against', 'goals_conceded', 'ga', 'goals_conceded'],
        'goals_conceded_per_match': ['goals_conceded_per_match', 'goals_against_per_match', 'avg_goals_conceded']
    }
    
    # Find matching columns
    for standard_name, variations in column_patterns.items():
        for col in df.columns:
            if col.lower() in [v.lower() for v in variations]:
                column_mapping[standard_name] = col
                break
    
    return column_mapping

def calculate_performance_score(df):
    """Calculate a composite performance score for ranking teams"""
    
    print("Calculating performance scores...")
    
    # Handle missing values by filling with 0
    df = df.fillna(0)
    
    # Detect column names
    column_mapping = detect_column_names(df)
    print(f"Detected columns: {column_mapping}")
    
    # Check if we have enough columns to calculate performance score
    required_for_basic_score = ['matches_played', 'matches_won', 'goals_for', 'goals_against']
    available_basic = [col for col in required_for_basic_score if col in column_mapping]
    
    if len(available_basic) < 3:
        print(f"Warning: Missing basic columns. Available: {available_basic}")
        print("Available columns in dataset:", list(df.columns))
        # Fallback to simpler calculation using available columns
        return calculate_fallback_score(df, column_mapping)
    
    # Create working dataframe with standardized column names
    df_work = df.copy()
    
    # Calculate missing metrics if we have basic data
    if 'matches_played' in column_mapping and 'matches_won' in column_mapping:
        if 'win_rate' not in column_mapping:
            matches_played = pd.to_numeric(df_work[column_mapping['matches_played']], errors='coerce').fillna(1)
            matches_won = pd.to_numeric(df_work[column_mapping['matches_won']], errors='coerce').fillna(0)
            df_work['calculated_win_rate'] = (matches_won / matches_played * 100).fillna(0)
            column_mapping['win_rate'] = 'calculated_win_rate'
    
    if 'goals_for' in column_mapping and 'goals_against' in column_mapping:
        if 'goal_difference' not in column_mapping:
            goals_for = pd.to_numeric(df_work[column_mapping['goals_for']], errors='coerce').fillna(0)
            goals_against = pd.to_numeric(df_work[column_mapping['goals_against']], errors='coerce').fillna(0)
            df_work['calculated_goal_difference'] = goals_for - goals_against
            column_mapping['goal_difference'] = 'calculated_goal_difference'
    
    if 'goals_for' in column_mapping and 'matches_played' in column_mapping:
        if 'goals_scored_per_match' not in column_mapping:
            goals_for = pd.to_numeric(df_work[column_mapping['goals_for']], errors='coerce').fillna(0)
            matches_played = pd.to_numeric(df_work[column_mapping['matches_played']], errors='coerce').fillna(1)
            df_work['calculated_goals_per_match'] = (goals_for / matches_played).fillna(0)
            column_mapping['goals_scored_per_match'] = 'calculated_goals_per_match'
    
    # Convert columns to numeric
    for standard_name, actual_col in column_mapping.items():
        if actual_col in df_work.columns:
            df_work[actual_col] = pd.to_numeric(df_work[actual_col], errors='coerce').fillna(0)
    
    # Calculate performance score using available metrics
    score_components = []
    
    # Win rate (40% weight)
    if 'win_rate' in column_mapping:
        win_rate_component = df_work[column_mapping['win_rate']] * 0.4
        score_components.append(win_rate_component)
        print(f"Using win rate from: {column_mapping['win_rate']}")
    
    # Goal difference (25% weight)
    if 'goal_difference' in column_mapping:
        goal_diff_component = df_work[column_mapping['goal_difference']] * 0.25
        score_components.append(goal_diff_component)
        print(f"Using goal difference from: {column_mapping['goal_difference']}")
    
    # Goals scored per match (20% weight)
    if 'goals_scored_per_match' in column_mapping:
        goals_component = df_work[column_mapping['goals_scored_per_match']] * 0.2
        score_components.append(goals_component)
        print(f"Using goals per match from: {column_mapping['goals_scored_per_match']}")
    
    # Scoring strength fallback to goals per match if not available
    if 'scoring_strength' in column_mapping:
        scoring_component = df_work[column_mapping['scoring_strength']] * 0.15
        score_components.append(scoring_component)
        print(f"Using scoring strength from: {column_mapping['scoring_strength']}")
    elif 'goals_scored_per_match' in column_mapping:
        # Use goals per match as scoring strength proxy
        scoring_component = df_work[column_mapping['goals_scored_per_match']] * 0.15
        score_components.append(scoring_component)
        print(f"Using goals per match as scoring strength proxy")
    
    if score_components:
        df_work['performance_score'] = sum(score_components)
    else:
        print("Warning: No valid components for performance score calculation")
        df_work['performance_score'] = 0
    
    # Update original dataframe with calculated columns
    for col in ['performance_score', 'calculated_win_rate', 'calculated_goal_difference', 'calculated_goals_per_match']:
        if col in df_work.columns:
            df[col] = df_work[col]
    
    # Show score distribution
    print(f"Performance score range: {df['performance_score'].min():.2f} to {df['performance_score'].max():.2f}")
    print(f"Teams with non-zero scores: {(df['performance_score'] > 0).sum()}")
    
    return df

def calculate_fallback_score(df, column_mapping):
    """Fallback performance calculation when standard columns are missing"""
    print("Using fallback performance calculation...")
    
    df_work = df.copy()
    
    # Try to use any available numeric columns for scoring
    numeric_cols = df_work.select_dtypes(include=[float, int]).columns.tolist()
    
    if len(numeric_cols) > 0:
        print(f"Using numeric columns for scoring: {numeric_cols[:5]}")  # Use first 5 numeric columns
        
        # Normalize and sum the first few numeric columns
        score = 0
        for i, col in enumerate(numeric_cols[:5]):
            col_data = pd.to_numeric(df_work[col], errors='coerce').fillna(0)
            if col_data.std() > 0:  # Only use columns with variation
                normalized = (col_data - col_data.min()) / (col_data.max() - col_data.min())
                score += normalized * (0.5 ** i)  # Decreasing weights
        
        df_work['performance_score'] = score
    else:
        print("No numeric columns found. Using random scores for demonstration.")
        df_work['performance_score'] = range(len(df_work))  # Simple ranking
    
    df['performance_score'] = df_work['performance_score']
    
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
    
    print(f"\nData columns: {list(df.columns)}")
    print(f"Final teams in cleaned dataset: {len(df)}")
    
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

## Data Processing

- **Data source:** {CSV_URL}
- **Total teams analyzed:** {len(df)} (after removing duplicates)
- **Duplicate handling:** First occurrence kept, subsequent duplicates removed

*All statistics are based on deduplicated team data to ensure accurate analysis.*
"""
    
    summary_filename = f"posts/{datetime.now().strftime('%Y-%m-%d')}-top-20-teams-summary.md"
    with open(summary_filename, 'w', encoding='utf-8') as f:
        f.write(summary_content)
    
    print(f"\nSummary post created: {summary_filename}")

if __name__ == "__main__":
    main()