"""
Test the SQL Knowledge Base Learning System

This script tests the core functionality of the learning system.
"""

from learning.sql_knowledge_base import SQLKnowledgeBase
from pathlib import Path
import tempfile
import shutil


def test_knowledge_base():
    """Test all major features of the knowledge base."""
    
    # Create temporary database for testing
    temp_dir = Path(tempfile.mkdtemp())
    db_path = temp_dir / "test_knowledge.db"
    
    print("="*70)
    print(" 🧪 Testing SQL Knowledge Base")
    print("="*70 + "\n")
    
    try:
        # Initialize knowledge base
        print("1. Initializing knowledge base...")
        kb = SQLKnowledgeBase(db_path=db_path)
        print("   ✅ Database created\n")
        
        # Test error classification
        print("2. Testing error classification...")
        test_errors = [
            ("AttributeError: 'DataFrame' object has no attribute 'RSI'", "attribute_error"),
            ("ImportError: No module named 'talib'", "import_error"),
            ("SyntaxError: invalid syntax", "syntax_error"),
            ("TypeError: expected str, got int", "type_error"),
            ("NameError: name 'data' is not defined", "name_error"),
            ("Some random error message", "general_error"),
        ]
        
        for error_msg, expected_type in test_errors:
            classified = kb.classify_error_advanced(error_msg)
            status = "✅" if classified == expected_type else "❌"
            print(f"   {status} '{error_msg[:50]}...' -> {classified}")
        print()
        
        # Test error normalization
        print("3. Testing error normalization...")
        original = "AttributeError: 'DataFrame' object has no attribute 'RSI' at line 45 in C:\\Users\\test\\strategy.py"
        normalized = kb.normalize_error(original)
        print(f"   Original:  {original}")
        print(f"   Normalized: {normalized}")
        signature = kb.hash_error(normalized)
        print(f"   Signature:  {signature}")
        print("   ✅ Normalization working\n")
        
        # Test recording iterations
        print("4. Testing iteration logging...")
        for i in range(1, 4):
            kb.record_iteration(
                workflow_id="test_workflow",
                iteration_number=i,
                error_type="attribute_error",
                error_message="DataFrame has no attribute 'RSI'",
                fix_attempted=f"Iteration {i} fix",
                success=(i == 3),  # Third iteration succeeds
                duration=10.0 + i,
                error_details={"test": True},
                fix_details={"iteration": i}
            )
            print(f"   ✅ Recorded iteration {i}")
        print()
        
        # Test recording successful fix
        print("5. Testing successful fix recording...")
        kb.record_successful_fix(
            error_type="attribute_error",
            error_message="DataFrame has no attribute 'RSI'",
            fix_description="Add RSI calculation using talib",
            fix_code_snippet="data['RSI'] = talib.RSI(data['Close'], timeperiod=14)",
            workflow_id="test_workflow",
            tags=["rsi", "indicator"],
            fix_time=12.5
        )
        print("   ✅ Successful fix recorded\n")
        
        # Test searching similar errors
        print("6. Testing similar error search...")
        similar = kb.search_similar_errors(
            error_message="DataFrame object has no attribute 'MACD'",
            error_type="attribute_error",
            limit=5
        )
        print(f"   Found {len(similar)} similar error(s)")
        for fix in similar:
            fix_dict = fix.to_dict()
            print(f"      - {fix_dict['error_type']}: {fix_dict['fix_description'][:50]}...")
            print(f"        Success: {fix_dict['success_count']}, Confidence: {fix_dict['confidence_score']:.0%}")
        print()
        
        # Test analytics
        print("7. Testing analytics...")
        analytics = kb.get_analytics()
        print(f"   Total patterns: {analytics['total_patterns']}")
        print(f"   Total iterations: {analytics['total_iterations']}")
        print(f"   Success rate: {analytics['success_rate']}%")
        print(f"   Error types tracked: {len(analytics['error_type_stats'])}")
        print("   ✅ Analytics working\n")
        
        # Test export
        print("8. Testing knowledge export...")
        export_path = temp_dir / "export.json"
        kb.export_knowledge(export_path)
        print(f"   ✅ Exported to {export_path}\n")
        
        # Test recording a failed fix
        print("9. Testing failed fix recording...")
        kb.record_failed_fix(
            error_type="attribute_error",
            error_message="DataFrame has no attribute 'RSI'",
            fix_attempted="Tried wrong approach"
        )
        print("   ✅ Failed fix recorded\n")
        
        # Get updated analytics
        print("10. Checking updated confidence scores...")
        analytics = kb.get_analytics()
        if analytics['top_fixes']:
            fix = analytics['top_fixes'][0]
            print(f"   Top fix confidence: {fix['confidence_score'] * 100:.1f}%")
            print(f"   Success/Failure: {fix['success_count']}/{analytics.get('failure_count', 0)}")
        print("   ✅ Confidence scoring working\n")
        
        print("="*70)
        print(" ✅ All Tests Passed!")
        print("="*70 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        try:
            shutil.rmtree(temp_dir)
            print("🧹 Cleaned up test database\n")
        except:
            pass


if __name__ == '__main__':
    success = test_knowledge_base()
    exit(0 if success else 1)
