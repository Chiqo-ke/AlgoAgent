"""
View learning analytics from the SQL knowledge base.

Usage:
    python view_learning_analytics.py
    python view_learning_analytics.py --export output.json
"""

import argparse
import json
from pathlib import Path
from learning.sql_knowledge_base import get_knowledge_base


def print_analytics(analytics: dict):
    """Print analytics in a readable format."""
    print("\n" + "="*70)
    print(" 🧠 LEARNING SYSTEM ANALYTICS")
    print("="*70 + "\n")
    
    # Overall stats
    print("📊 Overall Statistics:")
    print(f"   Total Error Patterns Learned: {analytics['total_patterns']}")
    print(f"   Total Iterations Logged: {analytics['total_iterations']}")
    print(f"   Total Successful Fixes: {analytics['total_successes']}")
    print(f"   Overall Success Rate: {analytics['success_rate']}%")
    print()
    
    # Error type stats
    print("🔍 Error Type Breakdown:")
    print(f"   {'Error Type':<25} {'Occurrences':<15} {'Fixes':<12} {'Fix Rate':<10}")
    print(f"   {'-'*25} {'-'*15} {'-'*12} {'-'*10}")
    
    for stat in analytics['error_type_stats']:
        error_type = stat['error_type']
        occurrences = stat['total_occurrences']
        fixes = stat['total_fixes']
        fix_rate = stat['fix_rate']
        print(f"   {error_type:<25} {occurrences:<15} {fixes:<12} {fix_rate:>6.1f}%")
    
    if not analytics['error_type_stats']:
        print("   No error types recorded yet")
    print()
    
    # Top fixes
    print("💡 Top Fixes by Confidence:")
    print(f"   {'Error Type':<20} {'Signature':<18} {'Success':<10} {'Confidence':<12}")
    print(f"   {'-'*20} {'-'*18} {'-'*10} {'-'*12}")
    
    for fix in analytics['top_fixes'][:10]:
        error_type = fix['error_type'][:18]
        signature = fix['error_signature'][:16]
        success = fix['success_count']
        confidence = fix['confidence_score'] * 100
        print(f"   {error_type:<20} {signature:<18} {success:<10} {confidence:>6.1f}%")
    
    if not analytics['top_fixes']:
        print("   No fixes recorded yet")
    print()
    
    print("="*70 + "\n")


def main():
    parser = argparse.ArgumentParser(description='View learning analytics')
    parser.add_argument('--export', type=str, help='Export analytics to JSON file')
    parser.add_argument('--export-knowledge', type=str, help='Export full knowledge base to JSON file')
    args = parser.parse_args()
    
    try:
        # Get knowledge base
        kb = get_knowledge_base()
        
        # Get analytics
        analytics = kb.get_analytics()
        
        # Print to console
        print_analytics(analytics)
        
        # Export if requested
        if args.export:
            export_path = Path(args.export)
            export_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(analytics, f, indent=2)
            
            print(f"✅ Analytics exported to {export_path}")
        
        # Export full knowledge if requested
        if args.export_knowledge:
            export_path = Path(args.export_knowledge)
            kb.export_knowledge(export_path)
            print(f"✅ Knowledge base exported to {export_path}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
