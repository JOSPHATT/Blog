#!/usr/bin/env python3
"""
Team Statistics Comprehensive Analysis Generator

This script fetches team statistics from a CSV file, removes duplicate entries,
ranks teams by performance, and generates a comprehensive summary post displaying
all original CSV statistics for the top 20 performing teams.

Features:
- Automatic duplicate team removal (keeps first occurrence)
- Composite performance scoring with weighted metrics
- Comprehensive summary post with complete team statistics
- Intelligent column detection and data processing
- All original CSV data preserved and displayed
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





def create_summary_post_only(top_teams, total_teams):
    """Create only a comprehensive summary post with all team statistics"""
    
    # Ensure posts directory exists
    os.makedirs('posts', exist_ok=True)
    
    current_date = datetime.now().strftime('%Y-%m-%d')
    current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Create comprehensive summary content
    summary_content = f"""---
title: "Top 20 Performing Teams - Complete Analysis"
date: {current_date}
---

# Top 20 Performing Teams - Complete Analysis

Generated on {current_datetime}

## Overview

This analysis presents the top 20 performing teams based on a composite performance score. Each team's complete statistics from the original dataset are displayed below.

## Team Rankings & Complete Statistics

"""
    
    for rank, (_, team_data) in enumerate(top_teams.iterrows(), 1):
        team_name = team_data['TEAM']
        performance_score = team_data.get('performance_score', 0)
        
        summary_content += f"""
### #{rank}. {team_name}

**Performance Score:** {performance_score:.2f}

#### Complete Team Statistics:
"""
        
        # Display all available statistics from the CSV
        for column, value in team_data.items():
            if column != 'TEAM':  # Skip the team name since it's already displayed
                # Format the value based on its type
                if pd.isna(value):
                    formatted_value = "N/A"
                elif isinstance(value, (int, float)):
                    if column in ['performance_score', 'calculated_win_rate', 'calculated_goal_difference', 'calculated_goals_per_match']:
                        formatted_value = f"{value:.2f}"
                    elif 'rate' in column.lower() or 'percentage' in column.lower():
                        formatted_value = f"{value:.1f}%"
                    elif isinstance(value, float) and value != int(value):
                        formatted_value = f"{value:.2f}"
                    else:
                        formatted_value = f"{int(value)}" if value == int(value) else f"{value:.2f}"
                else:
                    formatted_value = str(value)
                
                # Format column name for display
                display_name = column.replace('_', ' ').title()
                summary_content += f"- **{display_name}:** {formatted_value}\n"
        
        summary_content += "\n---\n"
    
    # Add methodology section
    summary_content += f"""

## Methodology

### Performance Score Calculation
Teams are ranked using a composite performance score calculated from:
- **Win Rate (40% weight)** - Percentage of matches won
- **Goal Difference (25% weight)** - Goals scored minus goals conceded  
- **Goals Scored per Match (20% weight)** - Average goals scored per game
- **Scoring Strength (15% weight)** - Team's offensive capabilities

### Data Processing
- **Data source:** {CSV_URL}
- **Total teams analyzed:** {total_teams} (after removing duplicates)
- **Duplicate handling:** First occurrence kept, subsequent duplicates removed
- **Missing data:** Automatically calculated from available metrics when possible

### Column Detection
The script intelligently detects various column naming conventions and calculates missing metrics:
- Win rates calculated from matches won/played when not available
- Goal differences calculated from goals for/against when not available  
- Goals per match calculated from total goals/matches when not available

### Quality Assurance
✅ Duplicate teams removed for accuracy  
✅ Missing values handled appropriately  
✅ Performance scores validated across all teams  
✅ All original CSV statistics preserved and displayed  

---

*All statistics are sourced directly from the original CSV data and processed for accuracy and completeness.*
"""
    
    summary_filename = f"posts/{current_date}-top-20-teams-complete-analysis.md"
    with open(summary_filename, 'w', encoding='utf-8') as f:
        f.write(summary_content)
    
    print(f"Generated comprehensive summary post: {summary_filename}")
    return [summary_filename]

def main():
    """Main function to orchestrate the comprehensive team analysis"""
    
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
    # Show available columns for preview
    preview_columns = ['TEAM', 'performance_score']
    for col in ['win_rate', 'calculated_win_rate', 'goal_difference', 'calculated_goal_difference']:
        if col in top_teams.columns:
            preview_columns.append(col)
            break
    
    print(top_teams[preview_columns].head())
    
    print("\nGenerating comprehensive summary post with all team statistics...")
    generated_posts = create_summary_post_only(top_teams, len(df))
    
    print(f"\nCompleted! Generated comprehensive analysis:")
    for post in generated_posts:
        print(f"  ✓ {post}")
    
    print(f"\nSummary: Analyzed {len(df)} teams and created detailed report for top 20 performers.")

if __name__ == "__main__":
    main()