import time
from typing import Dict, List
from app.ml.inference import analyze_emotion, get_top_emotions, get_emotional_intensity
from app.config import Config


# ============================================================================
# Test Data
# ============================================================================

SHORT_TEXTS = [
    "I'm so happy and grateful today! ",
    "This is absolutely terrible and frustrating.",
    "I feel anxious and worried about tomorrow.",
    "I love spending time with my family! ",
    "I'm really confused about what to do next.",
]

MEDIUM_TEXTS = [
    """
    Today started off pretty rough.  I woke up late and felt rushed all morning. 
    But then something great happened at work - my boss complimented my project! 
    Now I'm feeling much better and more confident about things.
    """,
    
    """
    I've been feeling so lonely lately. All my friends are busy with their own lives.
    Sometimes I wonder if anyone really cares.  It's hard to stay positive when you feel
    this isolated. I wish things were different. 
    """,
    
    """
    I can't believe I finally did it! After months of preparation, I passed my exam! 
    I'm so proud of myself and grateful for everyone who supported me.
    This is truly one of the best days of my life! 
    """,
]

LONG_TEXTS = [
    """
    This morning I woke up feeling anxious about my presentation at work.  I had spent
    weeks preparing, but I still felt nervous and unsure. During breakfast, I could
    barely eat anything. My stomach was in knots.  I kept going over my notes, trying
    to memorize every detail. The commute to work felt longer than usual. 
    
    When I arrived at the office, my anxiety only grew stronger. I reviewed my slides
    one more time, making small adjustments. My hands were shaking.  I wondered if
    everyone would notice how nervous I was. What if I forgot something important?
    What if they asked questions I couldn't answer?
    
    But then something unexpected happened. When I started presenting, I found my rhythm.
    The words flowed naturally.  My colleagues were engaged and nodding along. They asked
    thoughtful questions, and I was able to answer them confidently. 
    
    After the presentation, my boss pulled me aside and said it was excellent work.
    She was really impressed!  Several teammates came up to congratulate me. I felt this
    incredible wave of relief wash over me. All that worry had been for nothing! 
    
    Now I'm sitting at my desk feeling proud and accomplished. I can't believe how much
    I doubted myself this morning. I'm so grateful for this experience.  It taught me
    that I'm more capable than I think.  I feel excited about future challenges now!
    """,
    
    """
    I went to the grocery store today.  Bought some milk and bread. The weather was okay,
    nothing special. Traffic was moderate on the way there.  Parked in the usual spot.
    
    Then I got a call from my doctor. The test results came back, and everything looks
    great! I had been so worried for weeks about this. I honestly thought something was
    seriously wrong.  But it turns out I'm perfectly healthy! 
    
    I felt this enormous sense of relief.  Like a huge weight had been lifted off my
    shoulders. I actually started crying right there in the parking lot. Happy tears,
    though.  I'm so grateful and thankful.  Life feels precious again. 
    
    After that I went home.  Made some dinner. Watched a bit of TV. Did some laundry.
    Went to bed around 10 PM. Pretty normal evening otherwise.
    """,
    
    """
    My day was completely ordinary. I had my usual breakfast of toast and coffee.
    Checked my emails.  Responded to a few work messages. Had a routine meeting that
    lasted about an hour. Nothing particularly interesting happened during it.
    
    For lunch I had a sandwich from the cafeteria. It was okay, not great but not bad.
    The afternoon was more of the same - answering emails, working on some spreadsheets,
    attending another meeting. The weather outside was cloudy. 
    
    I left work at 5 PM as usual. The drive home took about 25 minutes. There was some
    traffic but nothing too bad. When I got home, I changed into comfortable clothes. 
    Made a simple dinner of pasta and salad. Watched the news while eating.
    
    After dinner I did the dishes, which took about 15 minutes. Then I watched a TV show
    for an hour. It was a rerun I'd seen before but had nothing else to do.  Around 9 PM
    I brushed my teeth and got ready for bed.  Read a few pages of a book before falling
    asleep around 10:30 PM.  Just another regular day, really.
    """,
]


# ============================================================================
# Helper Functions
# ============================================================================

def print_header(text: str):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(text. center(80))
    print("=" * 80)


def print_subheader(text: str):
    """Print a formatted subheader."""
    print("\n" + "-" * 80)
    print(text)
    print("-" * 80)


def print_result(result: Dict, show_details: bool = False):
    """Print emotion analysis result in a formatted way."""
    print(f"\n📊 Analysis Results:")
    print(f"   Method: {result. get('method', 'N/A')}")
    print(f"   Word count: {result.get('word_count', 'N/A')}")
    print(f"   Sentences analyzed: {result.get('num_sentences', 'N/A')}")
    
    print(f"\n🎭 Top Emotion:  {result['top_emotion']. upper()}")
    print(f"   Confidence: {result['top_confidence']:.1%}")
    
    print(f"\n🌡️  Emotional Intensity:  {result['emotional_intensity']:.1f}/10")
    intensity = result['emotional_intensity']
    if intensity <= 3:
        print(f"   (Very Negative)")
    elif intensity <= 4.5:
        print(f"   (Negative)")
    elif intensity <= 6:
        print(f"   (Neutral)")
    elif intensity <= 7.5:
        print(f"   (Positive)")
    else:
        print(f"   (Very Positive)")
    
    print(f"\n🎯 Top 3 Emotions:")
    for i, emotion in enumerate(result['top_3_emotions'], 1):
        bar_length = int(emotion['confidence'] * 40)
        bar = "█" * bar_length + "░" * (40 - bar_length)
        print(f"   {i}. {emotion['emotion']: <15} {bar} {emotion['confidence']:.1%}")
    
    # Show sentence-level details for long texts
    if show_details and 'sentence_details' in result:
        print(f"\n📝 Sentence Analysis:")
        for detail in result['sentence_details']: 
            importance_bar = "●" * int(detail['importance'] * 10)
            print(f"\n   Importance: {importance_bar} ({detail['importance']:.2f})")
            print(f"   Emotion: {detail['emotion']} ({detail['confidence']:.1%})")
            print(f"   Text: \"{detail['sentence'][: 80]}... \"")


def compare_methods(text:  str):
    """Compare different analysis methods side by side."""
    print_subheader("Method Comparison")
    
    print("\n📝 Text Preview:")
    preview = text. strip().replace('\n', ' ')[: 150]
    print(f"   \"{preview}... \"")
    
    methods = [
        ("Direct Classification", False, "keyword"),
        ("Adaptive (Keyword)", True, "keyword"),
        ("Adaptive (ML)", True, "ml"),
    ]
    
    results = []
    
    for method_name, adaptive, importance_method in methods:
        print(f"\n⏱️  Testing:  {method_name}...")
        start_time = time.time()
        
        try:
            result = analyze_emotion(text, adaptive=adaptive, importance_method=importance_method)
            elapsed = time.time() - start_time
            
            results.append({
                'method': method_name,
                'emotion': result['top_emotion'],
                'confidence': result['top_confidence'],
                'intensity': result['emotional_intensity'],
                'time': elapsed,
                'analysis_method': result.get('method', 'N/A')
            })
            
            print(f"   ✓ Complete in {elapsed:.3f}s")
        except Exception as e:
            print(f"   ✗ Error: {e}")
            results.append({
                'method': method_name,
                'emotion': 'ERROR',
                'confidence': 0,
                'intensity': 0,
                'time': 0,
                'analysis_method': 'N/A'
            })
    
    # Print comparison table
    print("\n" + "=" * 80)
    print(f"{'Method':<25} {'Emotion':<15} {'Confidence':<12} {'Intensity':<12} {'Time':<10}")
    print("-" * 80)
    for r in results:
        print(f"{r['method']:<25} {r['emotion']:<15} {r['confidence']:<12.1%} "
              f"{r['intensity']:<12.1f} {r['time']:<10.3f}s")
    print("=" * 80)


def batch_test(texts: List[str], title: str):
    """Test a batch of texts."""
    print_subheader(f"{title} ({len(texts)} texts)")
    
    for i, text in enumerate(texts, 1):
        print(f"\n[{i}/{len(texts)}] Testing text...")
        preview = text.strip().replace('\n', ' ')[:80]
        print(f"Preview: \"{preview}... \"")
        
        start_time = time.time()
        result = analyze_emotion(text, adaptive=True)
        elapsed = time.time() - start_time
        
        print(f"Result: {result['top_emotion']} ({result['top_confidence']:.1%}) "
              f"| Intensity: {result['emotional_intensity']:.1f}/10 "
              f"| Method: {result.get('method', 'N/A')} "
              f"| Time: {elapsed:.3f}s")


# ============================================================================
# Main Test Suite
# ============================================================================

def test_basic_functionality():
    """Test 1: Basic functionality with short texts."""
    print_header("TEST 1: Basic Functionality")
    
    text = "I'm feeling incredibly happy and excited about my new job!"
    print(f"\n📝 Input: \"{text}\"")
    
    result = analyze_emotion(text)
    print_result(result)


def test_short_texts():
    """Test 2: Multiple short texts."""
    print_header("TEST 2: Short Texts")
    batch_test(SHORT_TEXTS, "Short Text Batch")


def test_medium_texts():
    """Test 3: Medium-length texts."""
    print_header("TEST 3: Medium-Length Texts")
    
    for i, text in enumerate(MEDIUM_TEXTS, 1):
        print_subheader(f"Medium Text {i}")
        print(f"\n📝 Full Text:")
        print(text. strip())
        
        result = analyze_emotion(text, adaptive=True, importance_method="keyword")
        print_result(result, show_details=True)
        
        input("\nPress Enter to continue to next text...")


def test_long_texts():
    """Test 4: Long texts with detailed analysis."""
    print_header("TEST 4: Long Texts (Detailed Analysis)")
    
    for i, text in enumerate(LONG_TEXTS, 1):
        print_subheader(f"Long Text {i}")
        
        # Show first few sentences
        sentences = text.strip().split('.')[:3]
        print(f"\n📝 Text Preview (first 3 sentences):")
        for sent in sentences:
            if sent. strip():
                print(f"   • {sent.strip()}...")
        
        result = analyze_emotion(text, adaptive=True, importance_method="keyword")
        print_result(result, show_details=True)
        
        input("\nPress Enter to continue to next text...")


def test_method_comparison():
    """Test 5: Compare different methods."""
    print_header("TEST 5: Method Comparison")
    
    # Test with emotional peak in long text
    text = LONG_TEXTS[1]  # The doctor results text
    compare_methods(text)
    
    input("\nPress Enter to continue...")
    
    # Test with mostly neutral text
    text = LONG_TEXTS[2]  # The boring day text
    compare_methods(text)


def test_edge_cases():
    """Test 6: Edge cases."""
    print_header("TEST 6: Edge Cases")
    
    edge_cases = [
        ("Empty string", ""),
        ("Very short", "OK. "),
        ("Only punctuation", "! !!  ??? "),
        ("Numbers only", "123 456 789"),
        ("Single word", "happy"),
        ("Repeated word", "happy happy happy happy happy"),
        ("Mixed emotions", "I'm happy but also sad and confused at the same time."),
    ]
    
    for case_name, text in edge_cases:
        print(f"\n📝 {case_name}:  \"{text}\"")
        try:
            result = analyze_emotion(text, adaptive=True)
            print(f"   Result: {result['top_emotion']} ({result['top_confidence']:.1%})")
            if 'error' in result:
                print(f"   Error: {result['error']}")
        except Exception as e:
            print(f"   Exception: {e}")


def test_convenience_functions():
    """Test 7: Convenience functions."""
    print_header("TEST 7: Convenience Functions")
    
    text = "I'm so excited and grateful for this amazing opportunity!"
    
    print(f"\n📝 Input: \"{text}\"")
    
    print("\n1️⃣  get_top_emotions(k=3):")
    top_3 = get_top_emotions(text, k=3)
    for i, emotion in enumerate(top_3, 1):
        print(f"   {i}.  {emotion['emotion']}:  {emotion['confidence']:.1%}")
    
    print("\n2️⃣  get_emotional_intensity():")
    intensity = get_emotional_intensity(text)
    print(f"   Intensity: {intensity:.1f}/10")
    
    print("\n3️⃣  analyze_emotion() full result:")
    result = analyze_emotion(text)
    print(f"   Top emotion: {result['top_emotion']}")
    print(f"   Confidence: {result['top_confidence']:.1%}")
    print(f"   Intensity: {result['emotional_intensity']:.1f}/10")
    print(f"   Method: {result.get('method', 'N/A')}")


def test_performance():
    """Test 8: Performance benchmarking."""
    print_header("TEST 8: Performance Benchmarking")
    
    print("\n📊 Testing inference speed across different text lengths...")
    
    test_cases = [
        ("Short (10 words)", "I'm feeling happy and excited about today and tomorrow's opportunities!", False),
        ("Short (10 words) - Adaptive", "I'm feeling happy and excited about today and tomorrow's opportunities!", True),
        ("Medium (50 words)", MEDIUM_TEXTS[0], True),
        ("Long (200+ words)", LONG_TEXTS[0], True),
    ]
    
    print(f"\n{'Test Case':<30} {'Method':<20} {'Time (ms)':<15} {'Sentences':<12}")
    print("-" * 77)
    
    for case_name, text, adaptive in test_cases:
        times = []
        for _ in range(3):  # Run 3 times for average
            start = time.time()
            result = analyze_emotion(text, adaptive=adaptive, importance_method="keyword")
            times.append((time.time() - start) * 1000)
        
        avg_time = sum(times) / len(times)
        method = result.get('method', 'N/A')
        num_sentences = result.get('num_sentences', 1)
        
        print(f"{case_name:<30} {method:<20} {avg_time: <15.1f} {num_sentences:<12}")
    
    print("-" * 77)


def test_interactive_mode():
    """Test 9: Interactive testing."""
    print_header("TEST 9: Interactive Mode")
    
    print("\n📝 Enter your own journal entries to test the system.")
    print("   Type 'quit' to exit interactive mode.\n")
    
    while True:
        text = input("Your journal entry: ").strip()
        
        if text.lower() in ['quit', 'exit', 'q']: 
            print("Exiting interactive mode...")
            break
        
        if not text:
            continue
        
        print("\n⚙️  Analyzing...")
        result = analyze_emotion(text, adaptive=True, importance_method="keyword")
        print_result(result, show_details=True)
        print()


def run_all_tests():
    """Run all tests in sequence."""
    print_header("🧪 EMOTION ANALYSIS TEST SUITE 🧪")
    print(f"\nConfiguration:")
    print(f"  Device: {Config. DEVICE}")
    print(f"  Model: {Config.MODEL_NAME}")
    print(f"  Adaptive Analysis: {Config.ADAPTIVE_ANALYSIS_ENABLED}")
    print(f"  Default Method: {Config.DEFAULT_IMPORTANCE_METHOD}")
    print(f"  Short Text Threshold: {Config.SHORT_TEXT_THRESHOLD} words")
    
    tests = [
        ("1", "Basic Functionality", test_basic_functionality),
        ("2", "Short Texts", test_short_texts),
        ("3", "Medium Texts", test_medium_texts),
        ("4", "Long Texts", test_long_texts),
        ("5", "Method Comparison", test_method_comparison),
        ("6", "Edge Cases", test_edge_cases),
        ("7", "Convenience Functions", test_convenience_functions),
        ("8", "Performance Benchmarking", test_performance),
        ("9", "Interactive Mode", test_interactive_mode),
    ]
    
    print("\n\nAvailable Tests:")
    for num, name, _ in tests:
        print(f"  [{num}] {name}")
    print(f"  [A] Run all tests")
    print(f"  [Q] Quit")
    
    while True:
        choice = input("\nSelect test to run (1-9, A, or Q): ").strip().upper()
        
        if choice == 'Q':
            print("Goodbye!")
            break
        elif choice == 'A':
            for num, name, test_func in tests:
                try:
                    test_func()
                except KeyboardInterrupt:
                    print("\n\nTest interrupted.  Returning to menu...")
                    break
                except Exception as e:
                    print(f"\n❌ Test failed with error: {e}")
                    import traceback
                    traceback. print_exc()
                
                if num != "9":  # Don't pause after interactive mode
                    input("\nPress Enter to continue to next test...")
            break
        else:
            for num, name, test_func in tests:
                if choice == num:
                    try:
                        test_func()
                    except Exception as e:
                        print(f"\n❌ Test failed with error: {e}")
                        import traceback
                        traceback.print_exc()
                    break
            else:
                print("Invalid choice. Please try again.")


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__": 
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()