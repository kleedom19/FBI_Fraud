"""
Visualization functions for FBI Fraud data.
Returns Plotly figure objects for use in Streamlit or other applications.
Focuses on meaningful fraud metrics: financial losses, victim counts, and fraud categories.
"""

import json
import re
from collections import defaultdict
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from gemini_supabase import get_supabase_client


def normalize_age_group(age_group):
    """Normalize age group names to standard format."""
    if not age_group:
        return None
    
    age_lower = age_group.lower().strip()
    
    # Remove extra spaces and normalize dashes
    age_lower = re.sub(r'\s+', ' ', age_lower)
    age_lower = age_lower.replace(' - ', '-').replace('–', '-').replace('—', '-')
    
    # Map various formats to standard format
    if 'over' in age_lower and ('60' in age_lower or 'sixty' in age_lower or age_lower.startswith('60+')):
        return 'Over 60'
    elif ('50' in age_lower and '59' in age_lower) or age_lower == '50-59' or age_lower == '50 - 59':
        return '50-59'
    elif ('40' in age_lower and '49' in age_lower) or age_lower == '40-49' or age_lower == '40 - 49':
        return '40-49'
    elif ('30' in age_lower and '39' in age_lower) or age_lower == '30-39' or age_lower == '30 - 39':
        return '30-39'
    elif ('20' in age_lower and '29' in age_lower) or age_lower == '20-29' or age_lower == '20 - 29':
        return '20-29'
    elif 'under' in age_lower and '20' in age_lower:
        return 'Under 20'
    elif age_lower.startswith('60+') or age_lower == 'over 60':
        return 'Over 60'
    elif age_lower.startswith('< 20') or age_lower.startswith('under 20'):
        return 'Under 20'
    
    # Return original if no match
    return age_group

def get_age_group_order():
    """Return the correct order for age groups."""
    return ['Over 60', '50-59', '40-49', '30-39', '20-29', 'Under 20']


def get_all_analyses():
    """Retrieve all analysis records from Supabase."""
    try:
        supabase = get_supabase_client()
        response = supabase.table("ocr_results").select("*").execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error fetching data from Supabase: {e}")
        return []


def extract_year_from_filename(filename):
    """Extract year from filename (e.g., '2019agedata.pdf' -> 2019)."""
    match = re.search(r'(\d{4})', filename)
    return int(match.group(1)) if match else None


def extract_fraud_metrics(analysis_data):
    """Extract fraud-specific metrics from Gemini analysis."""
    metrics = {
        'year': None,
        'total_loss': None,
        'total_victims': None,
        'losses_by_category': [],
        'losses_by_age_group': [],
        'losses_by_state': [],
        'top_categories': []
    }
    
    if 'formatted_json' not in analysis_data:
        return metrics
    
    try:
        formatted = json.loads(analysis_data['formatted_json'])
        
        # Extract year
        metrics['year'] = formatted.get('year') or extract_year_from_filename(analysis_data.get('filename', ''))
        
        # Extract overall metrics
        overall_metrics = formatted.get('overall_metrics', {})
        if overall_metrics:
            metrics['total_loss'] = overall_metrics.get('total_loss')
            metrics['total_victims'] = overall_metrics.get('total_victims')
            metrics['top_categories'] = overall_metrics.get('top_fraud_categories', [])
            
            # Extract losses by category
            losses_by_cat = overall_metrics.get('losses_by_category', [])
            if losses_by_cat:
                metrics['losses_by_category'] = losses_by_cat
            
            # Extract losses by state
            losses_by_state = overall_metrics.get('losses_by_state', [])
            if losses_by_state:
                metrics['losses_by_state'] = losses_by_state
        
        # Extract page-level fraud metrics
        for page in formatted.get('pages', []):
            # Check if page has meaningful content (not just image references)
            raw_text = page.get('raw_text', '')
            content_summary = page.get('content_summary', '')
            
            # Skip pages that only have image references and no actual data
            if not raw_text or (len(raw_text.strip()) < 50 and 'image' in raw_text.lower() and 'table' not in content_summary.lower()):
                continue
            
            page_metrics = page.get('fraud_metrics', {})
            if page_metrics:
                # Extract tables with fraud data
                tables = page_metrics.get('tables', [])
                for table in tables:
                    rows = table.get('rows', [])
                    table_title = table.get('title', '').lower()
                    
                    # Check if this is a state table - look for state names or state-related headers
                    is_state_table = (
                        'state' in table_title or 
                        any('state' in str(row.get('state', '')).lower() for row in rows) or
                        any('state' in str(val).lower() for row in rows for val in row.values() if isinstance(val, str))
                    )
                    
                    # Also check headers for state indicators
                    headers = table.get('headers', [])
                    if not is_state_table and headers:
                        header_str = ' '.join(str(h).lower() for h in headers)
                        is_state_table = 'state' in header_str and ('rank' in header_str or 'count' in header_str or 'loss' in header_str)
                    
                    for row in rows:
                        # Handle state data
                        if is_state_table or row.get('state'):
                            state = row.get('state', '')
                            # Also check for state in other fields if 'state' key doesn't exist
                            if not state:
                                for key, val in row.items():
                                    if isinstance(val, str) and any(state_name in val for state_name in ['California', 'Texas', 'Florida', 'New York', 'Arizona', 'Pennsylvania']):
                                        # This might be a state name, check if it's in a state column
                                        if 'state' in key.lower() or key.lower() in ['state', 'location']:
                                            state = val
                                            break
                            
                            if state and state.strip():
                                # Clean state name (remove extra whitespace, fix common issues)
                                state = state.strip()
                                # Fix "District of" -> "District of Columbia"
                                if state == "District of":
                                    state = "District of Columbia"
                                
                                metrics['losses_by_state'].append({
                                    'state': state,
                                    'loss': row.get('loss') or row.get('amount') or row.get('total_loss') or row.get('Loss'),
                                    'victim_count': row.get('victim_count') or row.get('victims') or row.get('count') or row.get('Count'),
                                    'incidents': row.get('incidents') or row.get('Incidents') or row.get('count') or row.get('Count'),
                                    'year': metrics['year']
                                })
                            continue
                        
                        # Handle category/age group data
                        category = row.get('category', '')
                        victim_count = row.get('victim_count')
                        total_loss = row.get('total_loss')
                        
                        if total_loss and category:
                            # Check if it's an age group or fraud category
                            age_patterns = ['under', 'over', 'age', '20', '30', '40', '50', '60']
                            is_age_group = any(pattern in category.lower() for pattern in age_patterns)
                            
                            if is_age_group:
                                metrics['losses_by_age_group'].append({
                                    'age_group': category,
                                    'loss': total_loss,
                                    'victim_count': victim_count,
                                    'year': metrics['year']
                                })
                            else:
                                metrics['losses_by_category'].append({
                                    'category': category,
                                    'loss': total_loss,
                                    'victim_count': victim_count,
                                    'year': metrics['year']
                                })
                
                # Also check financial_data
                financial_data = page.get('financial_data', {})
                if financial_data:
                    losses_by_cat = financial_data.get('losses_by_category', [])
                    for item in losses_by_cat:
                        metrics['losses_by_category'].append({
                            'category': item.get('category', ''),
                            'loss': item.get('amount'),
                            'victim_count': item.get('victim_count'),
                            'year': metrics['year']
                        })
                    
                    losses_by_state = financial_data.get('losses_by_state', [])
                    for item in losses_by_state:
                        metrics['losses_by_state'].append({
                            'state': item.get('state', ''),
                            'loss': item.get('amount'),
                            'victim_count': item.get('victim_count'),
                            'incidents': item.get('incidents'),
                            'year': metrics['year']
                        })
    
    except Exception as e:
        print(f"Error extracting fraud metrics: {e}")
    
    return metrics


def get_summary_stats(all_analyses):
    """Get summary statistics from analyses."""
    total_loss = 0
    total_victims = 0
    years = set()
    
    for analysis in all_analyses:
        metrics = extract_fraud_metrics(analysis)
        if metrics['total_loss']:
            total_loss += metrics['total_loss']
        if metrics['total_victims']:
            total_victims += metrics['total_victims']
        if metrics['year']:
            years.add(metrics['year'])
    
    return {
        'total_documents': len(all_analyses),
        'total_loss': total_loss,
        'total_victims': total_victims,
        'years_covered': sorted(years)
    }


def create_losses_by_category_chart(all_analyses):
    """Create bar chart showing financial losses by fraud category."""
    category_data = defaultdict(lambda: {'loss': 0, 'victim_count': 0, 'years': set()})
    
    for analysis in all_analyses:
        metrics = extract_fraud_metrics(analysis)
        for item in metrics['losses_by_category']:
            cat = item.get('category', 'Unknown')
            if cat and cat != 'Unknown':
                category_data[cat]['loss'] += item.get('loss', 0)
                category_data[cat]['victim_count'] += item.get('victim_count', 0)
                if item.get('year'):
                    category_data[cat]['years'].add(item['year'])
    
    if not category_data:
        return None
    
    # Sort by loss amount
    sorted_categories = sorted(category_data.items(), key=lambda x: x[1]['loss'], reverse=True)
    top_categories = sorted_categories[:15]  # Top 15 categories
    
    categories = [cat for cat, _ in top_categories]
    losses = [data['loss'] for _, data in top_categories]
    
    fig = px.bar(
        x=losses,
        y=categories,
        orientation='h',
        title='Top Fraud Categories by Financial Loss',
        labels={'x': 'Total Loss ($)', 'y': 'Fraud Category'},
        color=losses,
        color_continuous_scale='Reds'
    )
    fig.update_layout(
        yaxis={'categoryorder': 'total ascending'},
        height=600,
        showlegend=False,
        xaxis_tickformat='$,.0f'
    )
    return fig


def create_losses_by_age_group_chart(all_analyses):
    """Create bar chart showing financial losses by age group."""
    age_data = defaultdict(lambda: {'loss': 0, 'victim_count': 0, 'years': set()})
    
    for analysis in all_analyses:
        metrics = extract_fraud_metrics(analysis)
        for item in metrics['losses_by_age_group']:
            age_group = normalize_age_group(item.get('age_group', ''))
            if age_group:
                age_data[age_group]['loss'] += item.get('loss', 0) or 0
                age_data[age_group]['victim_count'] += item.get('victim_count', 0) or 0
                if item.get('year'):
                    age_data[age_group]['years'].add(item['year'])
    
    if not age_data:
        return None
    
    # Convert to list and sort by custom order
    age_order = get_age_group_order()
    plot_data = []
    for age_group in age_order:
        if age_group in age_data:
            plot_data.append({
                'age_group': age_group,
                'loss': age_data[age_group]['loss'],
                'victim_count': age_data[age_group]['victim_count']
            })
    
    # Also include any age groups not in standard order
    for age_group, data in age_data.items():
        if age_group not in age_order:
            plot_data.append({
                'age_group': age_group,
                'loss': data['loss'],
                'victim_count': data['victim_count']
            })
    
    if not plot_data:
        return None
    
    df = pd.DataFrame(plot_data)
    
    # Create categorical type with custom order
    age_order_extended = age_order + [ag for ag in df['age_group'].unique() if ag not in age_order]
    df['age_group'] = pd.Categorical(df['age_group'], categories=age_order_extended, ordered=True)
    df = df.sort_values('age_group')
    
    fig = px.bar(
        df,
        x='age_group',
        y='loss',
        title='Total Financial Loss by Age Group',
        labels={'age_group': 'Age Group', 'loss': 'Total Loss ($)'},
        color='loss',
        color_continuous_scale='Blues'
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        height=500,
        showlegend=False,
        yaxis_tickformat='$,.0f'
    )
    return fig


def create_losses_trend_chart(all_analyses):
    """Create line chart showing total losses over time."""
    year_data = defaultdict(lambda: {'total_loss': 0, 'total_victims': 0})
    
    for analysis in all_analyses:
        metrics = extract_fraud_metrics(analysis)
        year = metrics['year']
        if year:
            if metrics['total_loss']:
                year_data[year]['total_loss'] += metrics['total_loss']
            if metrics['total_victims']:
                year_data[year]['total_victims'] += metrics['total_victims']
    
    if len(year_data) < 2:
        return None
    
    years = sorted(year_data.keys())
    losses = [year_data[y]['total_loss'] for y in years]
    victims = [year_data[y]['total_victims'] for y in years]
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Total Financial Losses by Year', 'Total Victims by Year'),
        vertical_spacing=0.15
    )
    
    # Losses trend
    fig.add_trace(
        go.Scatter(
            x=years,
            y=losses,
            mode='lines+markers',
            name='Total Loss',
            line=dict(width=3, color='#DC143C'),
            marker=dict(size=12)
        ),
        row=1, col=1
    )
    
    # Victims trend
    fig.add_trace(
        go.Scatter(
            x=years,
            y=victims,
            mode='lines+markers',
            name='Total Victims',
            line=dict(width=3, color='#4169E1'),
            marker=dict(size=12)
        ),
        row=2, col=1
    )
    
    fig.update_xaxes(title_text="Year", row=1, col=1)
    fig.update_xaxes(title_text="Year", row=2, col=1)
    fig.update_yaxes(title_text="Loss ($)", row=1, col=1, tickformat='$,.0f')
    fig.update_yaxes(title_text="Victim Count", row=2, col=1)
    fig.update_layout(
        height=700,
        title_text="Fraud Trends Over Time (2019-2021)",
        showlegend=False
    )
    
    return fig


def create_victims_by_age_group_chart(all_analyses):
    """Create bar chart showing victim counts by age group."""
    age_data = defaultdict(lambda: {'victim_count': 0, 'years': set()})
    
    for analysis in all_analyses:
        metrics = extract_fraud_metrics(analysis)
        for item in metrics['losses_by_age_group']:
            age_group = normalize_age_group(item.get('age_group', ''))
            if age_group:
                age_data[age_group]['victim_count'] += item.get('victim_count', 0) or 0
                if item.get('year'):
                    age_data[age_group]['years'].add(item['year'])
    
    if not age_data:
        return None
    
    # Convert to list and sort by custom order
    age_order = get_age_group_order()
    plot_data = []
    for age_group in age_order:
        if age_group in age_data:
            plot_data.append({
                'age_group': age_group,
                'victim_count': age_data[age_group]['victim_count']
            })
    
    # Also include any age groups not in standard order
    for age_group, data in age_data.items():
        if age_group not in age_order:
            plot_data.append({
                'age_group': age_group,
                'victim_count': data['victim_count']
            })
    
    if not plot_data:
        return None
    
    df = pd.DataFrame(plot_data)
    
    # Create categorical type with custom order
    age_order_extended = age_order + [ag for ag in df['age_group'].unique() if ag not in age_order]
    df['age_group'] = pd.Categorical(df['age_group'], categories=age_order_extended, ordered=True)
    df = df.sort_values('age_group')
    
    fig = px.bar(
        df,
        x='age_group',
        y='victim_count',
        title='Victim Counts by Age Group',
        labels={'age_group': 'Age Group', 'victim_count': 'Number of Victims'},
        color='victim_count',
        color_continuous_scale='Oranges'
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        height=500,
        showlegend=False,
        yaxis_tickformat=','
    )
    return fig


def create_category_comparison_chart(all_analyses):
    """Create comparison chart of top categories across years."""
    category_year_data = defaultdict(lambda: defaultdict(float))
    
    for analysis in all_analyses:
        metrics = extract_fraud_metrics(analysis)
        year = metrics['year']
        if not year:
            continue
        
        for item in metrics['losses_by_category']:
            cat = item.get('category', '')
            if cat:
                category_year_data[cat][year] += item.get('loss', 0)
    
    if not category_year_data:
        return None
    
    # Get top categories by total loss
    category_totals = {cat: sum(losses.values()) for cat, losses in category_year_data.items()}
    top_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Prepare data for plotting
    plot_data = []
    for cat, _ in top_categories:
        for year, loss in category_year_data[cat].items():
            plot_data.append({
                'category': cat,
                'year': year,
                'loss': loss
            })
    
    if not plot_data:
        return None
    
    df = pd.DataFrame(plot_data)
    fig = px.bar(
        df,
        x='category',
        y='loss',
        color='year',
        title='Top Fraud Categories: Loss Comparison Across Years',
        labels={'category': 'Fraud Category', 'loss': 'Total Loss ($)', 'year': 'Year'},
        barmode='group'
    )
    fig.update_layout(
        xaxis_tickangle=-45,
        height=600,
        yaxis_tickformat='$,.0f'
    )
    return fig


def create_state_visualization(all_analyses):
    """Create visualization showing fraud incidents/losses by state."""
    state_data = []
    
    for analysis in all_analyses:
        metrics = extract_fraud_metrics(analysis)
        for item in metrics['losses_by_state']:
            # Handle both 'loss' and 'amount' fields
            loss = item.get('loss') or item.get('amount') or 0
            victim_count = item.get('victim_count') or item.get('count') or 0
            incidents = item.get('incidents') or item.get('count') or victim_count
            
            if loss or victim_count or incidents:
                state_data.append({
                    'state': item.get('state', ''),
                    'loss': loss,
                    'victim_count': victim_count,
                    'incidents': incidents,
                    'year': item.get('year') or metrics['year']
                })
    
    if not state_data:
        return None
    
    df = pd.DataFrame(state_data)
    
    # Filter out rows with no data
    df = df[(df['loss'] > 0) | (df['victim_count'] > 0) | (df['incidents'] > 0)]
    
    if len(df) == 0:
        return None
    
    # Aggregate by state if multiple years or duplicate states
    # First, aggregate to handle duplicates - replace None/NaN with 0 for aggregation
    df = df.fillna({'loss': 0, 'victim_count': 0, 'incidents': 0})
    df_agg = df.groupby('state').agg({
        'loss': 'sum',
        'victim_count': 'sum',
        'incidents': 'sum'
    }).reset_index()
    
    # Filter out states with no data
    df_agg = df_agg[(df_agg['loss'] > 0) | (df_agg['victim_count'] > 0) | (df_agg['incidents'] > 0)]
    
    if len(df_agg) == 0:
        return None
    
    # Sort by loss (or incidents if no loss data)
    sort_col = 'loss' if df_agg['loss'].sum() > 0 else 'incidents'
    df_agg = df_agg.sort_values(sort_col, ascending=False).head(20)  # Top 20 states
    
    if df['year'].nunique() > 1:
        
        # Create subplot with losses and incidents
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Financial Losses by State', 'Incidents by State'),
            horizontal_spacing=0.15
        )
        
        # Losses chart
        fig.add_trace(
            go.Bar(
                x=df_agg['state'],
                y=df_agg['loss'],
                name='Loss',
                marker_color='#DC143C'
            ),
            row=1, col=1
        )
        
        # Incidents chart
        fig.add_trace(
            go.Bar(
                x=df_agg['state'],
                y=df_agg['incidents'],
                name='Incidents',
                marker_color='#4169E1'
            ),
            row=1, col=2
        )
        
        fig.update_xaxes(title_text="State", row=1, col=1, tickangle=-45)
        fig.update_xaxes(title_text="State", row=1, col=2, tickangle=-45)
        fig.update_yaxes(title_text="Loss ($)", row=1, col=1, tickformat='$,.0f')
        fig.update_yaxes(title_text="Incidents", row=1, col=2, tickformat=',')
        fig.update_layout(
            height=600,
            title_text="Top 20 States by Fraud Impact (All Years)",
            showlegend=False
        )
    else:
        # Single year - simpler visualization
        # Use aggregated data
        sort_col = 'loss' if df_agg['loss'].sum() > 0 else 'incidents'
        df_agg = df_agg.sort_values(sort_col, ascending=False).head(20)
        
        # Use loss if available, otherwise incidents
        y_col = 'loss' if df_agg['loss'].sum() > 0 else 'incidents'
        y_label = 'Total Loss ($)' if y_col == 'loss' else 'Incidents'
        
        fig = px.bar(
            df_agg,
            x='state',
            y=y_col,
            title=f'Top 20 States by {"Financial Loss" if y_col == "loss" else "Incidents"}',
            labels={'state': 'State', y_col: y_label},
            color=y_col,
            color_continuous_scale='Reds'
        )
        fig.update_layout(
            xaxis_tickangle=-45,
            height=600,
            showlegend=False,
            yaxis_tickformat='$,.0f' if y_col == 'loss' else ','
        )
    
    return fig
