"""
Main entry point for the news analysis pipeline.
Orchestrates fetching, analysis, validation, and reporting.
"""

import os
import json
import time
from datetime import datetime
from news_fetcher import NewsFetcher
from llm_analyzer import LLMAnalyzer
from llm_validator import LLMValidator
from dotenv import load_dotenv

def ensure_output_directory():
    """Create output directory if it doesn't exist."""
    if not os.path.exists('output'):
        os.makedirs('output')
        print("✓ Created output directory")

def save_json(data, filename):
    """Save data to JSON file in output directory."""
    filepath = os.path.join('output', filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved {filename}")

def generate_markdown_report(validated_results):
    """Generate a human-readable markdown report."""
    report_lines = [
        "# News Analysis Report",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Articles Analyzed:** {len(validated_results)}",
        "**Source:** NewsAPI",
        "",
        "## Summary",
        ""
    ]
    
    # Count sentiments
    sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
    for result in validated_results:
        sentiment = result.get('analysis', {}).get('sentiment', 'neutral').lower()
        if sentiment in sentiment_counts:
            sentiment_counts[sentiment] += 1
    
    report_lines.extend([
        f"- Positive: {sentiment_counts['positive']} articles",
        f"- Negative: {sentiment_counts['negative']} articles",
        f"- Neutral: {sentiment_counts['neutral']} articles",
        "",
        "## Detailed Analysis",
        ""
    ])
    
    # Add each article
    for idx, result in enumerate(validated_results, 1):
        article = result.get('article', {})
        analysis = result.get('analysis', {})
        validation = result.get('validation', {})
        
        title = article.get('title', 'No title')
        url = article.get('url', '#')
        gist = analysis.get('gist', 'N/A')
        sentiment = analysis.get('sentiment', 'N/A')
        tone = analysis.get('tone', 'N/A')
        is_valid = validation.get('is_valid', False)
        validation_notes = validation.get('notes', 'No validation notes')
        
        validation_symbol = "✓" if is_valid else "✗"
        
        report_lines.extend([
            f"### Article {idx}: \"{title}\"",
            f"- **Source:** [{url}]({url})",
            f"- **Gist:** {gist}",
            f"- **LLM#1 Sentiment:** {sentiment}",
            f"- **LLM#2 Validation:** {validation_symbol} {validation_notes}",
            f"- **Tone:** {tone}",
            ""
        ])
    
    report_content = "\n".join(report_lines)
    
    # Save report
    filepath = os.path.join('output', 'final_report.md')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(report_content)
    print(f"✓ Generated final_report.md")
    
    return report_content

def main():
    """Main execution flow."""
    print("=" * 60)
    print("NEWS ANALYSIS PIPELINE - DUAL LLM VALIDATION")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    # Step 1: Setup
    print("\n[Step 1/5] Setting up...")
    ensure_output_directory()
    
    # Step 2: Fetch news articles
    print("\n[Step 2/5] Fetching news articles...")
    fetcher = NewsFetcher()
    articles = fetcher.fetch_india_politics_news(num_articles=12)
    
    if not articles:
        print("✗ No articles fetched. Exiting.")
        return
    
    save_json(articles, 'raw_articles.json')
    print(f"✓ Fetched {len(articles)} articles")
    
    # Step 3: Analyze with LLM#1 (Groq GPT OSS 120B)
    print("\n[Step 3/5] Analyzing with LLM#1 (Groq GPT OSS 120B)...")
    analyzer = LLMAnalyzer()
    analysis_results = []
    
    for idx, article in enumerate(articles, 1):
        print(f"  Analyzing article {idx}/{len(articles)}...", end=" ")
        analysis = analyzer.analyze_article(article)
        analysis_results.append({
            'article': article,
            'analysis': analysis
        })
        print("✓")
        time.sleep(3)  # Delay to avoid rate limits
    
    save_json(analysis_results, 'analysis_results.json')
    
    # Step 4: Validate with LLM#2 (Groq GPT OSS 20B)
    print("\n[Step 4/5] Validating with LLM#2 (Groq GPT OSS 20B)...")
    validator = LLMValidator()
    validated_results = []
    
    for idx, result in enumerate(analysis_results, 1):
        print(f"  Validating article {idx}/{len(analysis_results)}...", end=" ")
        validation = validator.validate_analysis(
            result['article'],
            result['analysis']
        )
        validated_results.append({
            'article': result['article'],
            'analysis': result['analysis'],
            'validation': validation
        })
        print("✓")
        time.sleep(3)  # Delay to avoid rate limits
    
    save_json(validated_results, 'validated_results.json')
    
    # Step 5: Generate final report
    print("\n[Step 5/5] Generating final report...")
    generate_markdown_report(validated_results)
    
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("\nCheck the 'output' folder for:")
    print("  - raw_articles.json")
    print("  - analysis_results.json")
    print("  - validated_results.json")
    print("  - final_report.md")

if __name__ == "__main__":
    main()