"""
Test script for AI Topic Validation Service
Tests the topic extraction and validation features
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.topic_validation_service import topic_validation_service


async def test_topic_extraction():
    """Test extracting topic from content"""
    print("\n" + "="*60)
    print("TEST 1: Topic Extraction")
    print("="*60)
    
    # Test with Art and Culture content
    art_content = """
    The Ajanta Caves are 30 rock-cut Buddhist cave monuments dating from 
    the 2nd century BCE to about 480 CE. The caves include paintings and 
    rock-cut sculptures that are among the finest surviving examples of 
    ancient Indian art. The caves were built in two phases, the first 
    starting around the 2nd century BCE and the second occurring from 
    400–650 CE according to older scholarship.
    """
    
    print("\nTesting Art & Culture content...")
    result = await topic_validation_service.extract_topic_from_content(art_content)
    print(f"Detected Topic: {result.get('detected_topic')}")
    print(f"Confidence: {result.get('confidence')}")
    print(f"Keywords: {result.get('keywords', [])[:5]}")
    
    # Test with Quality/Management content
    quality_content = """
    Total Quality Management (TQM) is a management approach that focuses on 
    continuous improvement of products, services, and processes. The key 
    principles include customer focus, total employee involvement, process 
    approach, integrated system, and fact-based decision making.
    """
    
    print("\nTesting Quality Management content...")
    result2 = await topic_validation_service.extract_topic_from_content(quality_content)
    print(f"Detected Topic: {result2.get('detected_topic')}")
    print(f"Confidence: {result2.get('confidence')}")
    print(f"Keywords: {result2.get('keywords', [])[:5]}")
    
    return True


async def test_topic_validation():
    """Test validating topic relevance"""
    print("\n" + "="*60)
    print("TEST 2: Topic Validation (Matching)")
    print("="*60)
    
    # Test 1: Matching topics
    video_topic = "Indian Art and Culture"
    video_keywords = ["Ajanta", "Ellora", "caves", "paintings", "sculptures", "Buddhist", "Hindu"]
    
    matching_content = """
    The Ellora Caves, located in Maharashtra, India, are a World Heritage Site. 
    They contain Hindu, Buddhist, and Jain rock-cut temples and monasteries 
    dating from 600-1000 CE. The Kailasa Temple is the most remarkable structure.
    """
    
    print(f"\nVideo Topic: {video_topic}")
    print(f"Student Content: About Ellora Caves (related to Art & Culture)")
    
    result = await topic_validation_service.validate_topic_relevance(
        video_topic=video_topic,
        video_keywords=video_keywords,
        student_content=matching_content,
        threshold=0.5
    )
    
    print(f"\nResult:")
    print(f"  Is Relevant: {result.get('is_relevant')}")
    print(f"  Relevance Score: {result.get('relevance_score')}")
    print(f"  Detected Topic: {result.get('detected_topic')}")
    print(f"  Match Type: {result.get('match_type')}")
    print(f"  Reasoning: {result.get('reasoning', '')[:200]}...")
    
    return True


async def test_topic_mismatch():
    """Test detecting topic mismatch"""
    print("\n" + "="*60)
    print("TEST 3: Topic Mismatch Detection")
    print("="*60)
    
    # Test: Mismatching topics (Quality video, Art content)
    video_topic = "Total Quality Management"
    video_keywords = ["TQM", "quality", "management", "ISO", "six sigma", "continuous improvement"]
    
    wrong_content = """
    The Mughal Empire ruled most of northern India from the early 16th to the 
    mid-18th century. Emperor Akbar was known for his religious tolerance and 
    administrative reforms. The Taj Mahal, built by Shah Jahan, is considered 
    the finest example of Mughal architecture.
    """
    
    print(f"\nVideo Topic: {video_topic}")
    print(f"Student Content: About Mughal Empire (UNRELATED)")
    
    result = await topic_validation_service.validate_topic_relevance(
        video_topic=video_topic,
        video_keywords=video_keywords,
        student_content=wrong_content,
        threshold=0.5
    )
    
    print(f"\nResult:")
    print(f"  Is Relevant: {result.get('is_relevant')} (Should be FALSE)")
    print(f"  Relevance Score: {result.get('relevance_score')} (Should be LOW)")
    print(f"  Detected Topic: {result.get('detected_topic')}")
    print(f"  Expected Topic: {result.get('expected_topic')}")
    print(f"  Match Type: {result.get('match_type')}")
    print(f"  Reasoning: {result.get('reasoning', '')[:200]}...")
    print(f"  Recommendation: {result.get('recommendation', '')}")
    
    # Check if mismatch was detected
    if not result.get('is_relevant'):
        print("\n✅ SUCCESS: Topic mismatch correctly detected!")
    else:
        print("\n⚠️ WARNING: Topic mismatch was NOT detected. Score threshold may need adjustment.")
    
    return True


async def main():
    print("\n" + "="*60)
    print("AI TOPIC VALIDATION SERVICE - TEST SUITE")
    print("="*60)
    
    try:
        await test_topic_extraction()
        await test_topic_validation()
        await test_topic_mismatch()
        
        print("\n" + "="*60)
        print("ALL TESTS COMPLETED!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
