#!/usr/bin/env python3
"""
Clean and prepare EPP_Database_1.csv for executive contact discovery.

This script:
1. Fixes column name typos
2. Adds tracking columns for scraping
3. Adds missing executive title columns
4. Extracts local union numbers
5. Cleans phone numbers and domains
"""

import pandas as pd
import re
import os
from datetime import datetime

def clean_column_names(df):
    """Fix typos and standardize column names."""
    column_mapping = {
        'Preisent & CEO': 'President & CEO',
        'web site domain': 'website_domain',
        'email domain': 'email_domain',
        'entity_type': 'entity_type',
        ' total_participants ': 'total_participants',  # Remove spaces
        'Vice President/VP ': 'Vice President/VP',  # Remove trailing space
        'phone_num': 'phone_number'
    }
    
    # Apply mapping
    df = df.rename(columns=column_mapping)
    
    # Strip whitespace from all column names
    df.columns = df.columns.str.strip()
    
    return df

def add_tracking_columns(df):
    """Add columns for scraper tracking."""
    tracking_columns = {
        'scrape_status': 'pending',  # pending, in_progress, completed, failed
        'scrape_date': None,
        'scrape_attempts': 0,
        'last_scrape_error': None,
        'data_quality_score': None,
        'executives_found': 0,
        'linkedin_profile_url': None,
        'company_website_verified': None,
        'data_source': 'Form 5500',
        'last_updated': datetime.now().strftime('%Y-%m-%d')
    }
    
    for col, default_val in tracking_columns.items():
        df[col] = default_val
    
    return df

def add_missing_executive_columns(df):
    """Add missing executive title columns."""
    new_executive_titles = [
        'General Counsel',
        'Fund Administrator',
        'Administrator',
        'Assistant Administrator',
        'Benefits Administrator',
        'Plan Administrator',
        'Trust Administrator',
        'Chief Operating Officer/COO',
        'Chief Technology Officer/CTO',
        'Chief Information Officer/CIO',
        'Chief Human Resources Officer/CHRO',
        'Chief Marketing Officer/CMO',
        'Chief Legal Officer/CLO',
        'Managing Director',
        'Executive Secretary',
        'Assistant Secretary',
        'Assistant Treasurer',
        'Controller',
        'Benefits Manager',
        'HR Director',
        'Operations Director',
        'IT Director',
        'Communications Director',
        'Board Chair',
        'Board Secretary',
        'Trustee Chair',
        'Union President',
        'Union Secretary-Treasurer',
        'Business Manager'
    ]
    
    # Add columns if they don't exist
    for title in new_executive_titles:
        if title not in df.columns:
            df[title] = None
    
    return df

def extract_local_union_info(df):
    """Extract local union numbers from organization names."""
    df['local_union_number'] = None
    df['parent_union'] = None
    
    # Common patterns for local unions
    local_patterns = [
        r'LOCAL\s+(\d+)',
        r'LOCAL\s+NO\.\s*(\d+)',
        r'LOCAL\s+UNION\s+(\d+)',
        r'LOCAL\s+#(\d+)',
        r'L\.U\.\s*(\d+)',
        r'LU\s*(\d+)'
    ]
    
    # Common union abbreviations
    union_patterns = {
        'IBEW': 'International Brotherhood of Electrical Workers',
        'IBT': 'International Brotherhood of Teamsters',
        'TEAMSTERS': 'International Brotherhood of Teamsters',
        'UAW': 'United Auto Workers',
        'SEIU': 'Service Employees International Union',
        'AFSCME': 'American Federation of State, County and Municipal Employees',
        'AFL-CIO': 'American Federation of Labor and Congress of Industrial Organizations',
        'UFCW': 'United Food and Commercial Workers',
        'UNITE HERE': 'UNITE HERE',
        'LIUNA': 'Laborers International Union of North America',
        'IUOE': 'International Union of Operating Engineers',
        'USW': 'United Steelworkers',
        'STEELWORKERS': 'United Steelworkers',
        'AFT': 'American Federation of Teachers',
        'NEA': 'National Education Association',
        'CWA': 'Communications Workers of America',
        'IUPAT': 'International Union of Painters and Allied Trades',
        'SMART': 'International Association of Sheet Metal, Air, Rail and Transportation Workers',
        'IAM': 'International Association of Machinists and Aerospace Workers'
    }
    
    for idx, row in df.iterrows():
        org_name = str(row['organization_name']).upper() if pd.notna(row['organization_name']) else ''
        
        # Extract local number
        for pattern in local_patterns:
            match = re.search(pattern, org_name)
            if match:
                df.at[idx, 'local_union_number'] = match.group(1)
                break
        
        # Identify parent union
        for abbrev, full_name in union_patterns.items():
            if abbrev in org_name:
                df.at[idx, 'parent_union'] = full_name
                break
    
    return df

def clean_phone_numbers(df):
    """Standardize phone number formats."""
    def format_phone(phone):
        if pd.isna(phone):
            return None
        
        # Convert to string and remove all non-digits
        phone_str = re.sub(r'\D', '', str(phone))
        
        # Handle different lengths
        if len(phone_str) == 10:
            return f"({phone_str[:3]}) {phone_str[3:6]}-{phone_str[6:]}"
        elif len(phone_str) == 11 and phone_str[0] == '1':
            return f"({phone_str[1:4]}) {phone_str[4:7]}-{phone_str[7:]}"
        else:
            return phone_str  # Return as-is if format is unexpected
    
    df['phone_number_cleaned'] = df['phone_number'].apply(format_phone)
    
    return df

def clean_domains(df):
    """Clean and standardize domain names."""
    def clean_domain(domain):
        if pd.isna(domain) or domain == '':
            return None
        
        domain = str(domain).lower().strip()
        
        # Remove common prefixes
        domain = re.sub(r'^(https?://|www\.)', '', domain)
        
        # Remove trailing slashes and paths
        domain = domain.split('/')[0]
        
        # Basic validation
        if '.' in domain and len(domain) > 3:
            return domain
        else:
            return None
    
    df['website_domain_cleaned'] = df['website_domain'].apply(clean_domain)
    df['email_domain_cleaned'] = df['email_domain'].apply(clean_domain)
    
    return df

def add_data_quality_metrics(df):
    """Add data quality scoring based on completeness."""
    def calculate_quality_score(row):
        score = 0
        max_score = 0
        
        # Essential fields (weighted higher)
        essential_fields = [
            ('ein', 10),
            ('organization_name', 10),
            ('mail_us_city', 5),
            ('mail_us_state', 5),
            ('phone_number_cleaned', 8),
            ('website_domain_cleaned', 7)
        ]
        
        for field, weight in essential_fields:
            max_score += weight
            if pd.notna(row.get(field)) and str(row.get(field)).strip() != '':
                score += weight
        
        # Calculate percentage
        return round((score / max_score) * 100, 2) if max_score > 0 else 0
    
    df['data_completeness_score'] = df.apply(calculate_quality_score, axis=1)
    
    return df

def create_summary_report(df):
    """Generate a summary report of the cleaning process."""
    report = {
        'total_records': len(df),
        'records_with_phone': df['phone_number_cleaned'].notna().sum(),
        'records_with_website': df['website_domain_cleaned'].notna().sum(),
        'records_with_email_domain': df['email_domain_cleaned'].notna().sum(),
        'local_unions_identified': df['local_union_number'].notna().sum(),
        'parent_unions_identified': df['parent_union'].notna().sum(),
        'avg_data_completeness': df['data_completeness_score'].mean(),
        'high_quality_records': (df['data_completeness_score'] >= 70).sum()
    }
    
    return report

def main():
    """Main cleaning pipeline."""
    # Paths
    input_path = '../data/EPP_Database_1.csv'
    output_path = '../data/EPP_Database_1_cleaned.csv'
    report_path = '../data/cleaning_report.txt'
    
    print("Loading data...")
    df = pd.read_csv(input_path)
    print(f"Loaded {len(df)} records")
    
    print("\nCleaning column names...")
    df = clean_column_names(df)
    
    print("Adding tracking columns...")
    df = add_tracking_columns(df)
    
    print("Adding missing executive columns...")
    df = add_missing_executive_columns(df)
    
    print("Extracting local union information...")
    df = extract_local_union_info(df)
    
    print("Cleaning phone numbers...")
    df = clean_phone_numbers(df)
    
    print("Cleaning domains...")
    df = clean_domains(df)
    
    print("Calculating data quality metrics...")
    df = add_data_quality_metrics(df)
    
    # Save cleaned data
    print(f"\nSaving cleaned data to {output_path}...")
    df.to_csv(output_path, index=False)
    
    # Generate report
    print("Generating summary report...")
    report = create_summary_report(df)
    
    with open(report_path, 'w') as f:
        f.write("EPP Database Cleaning Report\n")
        f.write("=" * 50 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        for key, value in report.items():
            f.write(f"{key.replace('_', ' ').title()}: {value:,}\n")
        
        f.write("\n\nColumn Summary:\n")
        f.write("-" * 30 + "\n")
        f.write(f"Total columns: {len(df.columns)}\n")
        f.write(f"Executive title columns: {len([col for col in df.columns if any(title in col.lower() for title in ['chief', 'officer', 'president', 'director', 'secretary', 'treasurer', 'counsel', 'administrator', 'manager'])])}\n")
        
        # Sample of cleaned data
        f.write("\n\nSample Records (Top 5 by data quality):\n")
        f.write("-" * 50 + "\n")
        top_records = df.nlargest(5, 'data_completeness_score')[['organization_name', 'mail_us_city', 'mail_us_state', 'phone_number_cleaned', 'website_domain_cleaned', 'data_completeness_score']]
        f.write(top_records.to_string(index=False))
    
    print(f"\nCleaning complete! Report saved to {report_path}")
    
    # Print summary to console
    print("\n" + "=" * 50)
    print("CLEANING SUMMARY")
    print("=" * 50)
    for key, value in report.items():
        print(f"{key.replace('_', ' ').title()}: {value:,}")

if __name__ == "__main__":
    main()