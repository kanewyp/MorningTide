import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from datetime import datetime, timedelta

def populate_diary_entries():
    """Populate database with realistic diary entries from Jan 10-23"""
    
    conn = sqlite3.connect('morningtide.db')
    cursor = conn.cursor()
    
    # First, get or create a test user
    cursor.execute("SELECT id FROM users LIMIT 1")
    user = cursor.fetchone()
    
    if not user:
        print("❌ No users found in database. Please create a user account first.")
        conn.close()
        return
    
    user_id = user[0]
    print(f"✅ Found user ID: {user_id}")
    
    # Diary entries with emotional journey
    entries = [
        {
            "date": "2026-01-10",
            "content": """Today started off rough. I woke up with this heavy feeling in my chest, like something was weighing me down. Work has been incredibly demanding lately, and I feel like I'm drowning in deadlines. My manager keeps piling on more tasks without acknowledging how much I'm already handling. I tried to speak up in the team meeting, but my voice came out shaky and uncertain. I hate feeling this way - so small and powerless. By the end of the day, I just wanted to crawl into bed and disappear."""
        },
        {
            "date": "2026-01-11",
            "content": """Barely slept last night. My mind was racing with all the things I need to do, replaying yesterday's meeting over and over. Why didn't I speak up more confidently? I keep thinking about all the things I should have said. Went through the motions at work today, but it felt like I was watching myself from outside my body. Everything feels foggy and distant. Skipped lunch because my stomach was in knots. Called Mom tonight - she could tell something was wrong, but I didn't want to worry her. Just told her I was tired."""
        },
        {
            "date": "2026-01-12",
            "content": """Sunday morning, and I should feel relaxed, but I don't. Tried to do some self-care - took a long bath, made my favorite breakfast, put on a face mask. It helped a little. The quiet was nice. Started reading that book Sarah recommended about mindfulness. Some of it resonated with me, especially the part about not judging your thoughts. I realized I'm so hard on myself all the time. Maybe that's something I need to work on. Felt a tiny bit lighter after journaling this morning."""
        },
        {
            "date": "2026-01-13",
            "content": """Back to work. Monday blues hit hard. But something was different today - I remembered what I read yesterday about being present. When I started feeling overwhelmed, I actually took a few deep breaths before responding to emails. It sounds small, but it felt like a tiny victory. Had coffee with Jamie from accounting - she's dealing with similar stress. It was comforting to know I'm not alone in feeling this way. We talked about maybe starting a lunch walking group to decompress during the day."""
        },
        {
            "date": "2026-01-14",
            "content": """Today was better! I actually felt like myself for the first time in days. Finished a big project that's been hanging over my head for weeks. My manager even sent a brief 'good job' email - it's not much, but I'll take it. Went for a walk during lunch with Jamie like we discussed. The fresh air and movement helped clear my head. I noticed the trees starting to bud, and it made me think about growth and new beginnings. Maybe I'm turning a corner?"""
        },
        {
            "date": "2026-01-15",
            "content": """Woke up feeling energized. Made it to my morning yoga class for the first time in three weeks! It felt so good to move my body and breathe deeply. Throughout the day, I noticed myself being more patient - with myself and with others. When a coworker snapped at me, instead of taking it personally, I remembered they're probably dealing with their own stress. Set some boundaries today too - actually said no to taking on an extra project. My heart was pounding when I said it, but I did it! Proud of myself."""
        },
        {
            "date": "2026-01-16",
            "content": """Hit a small setback today. Got some critical feedback on a presentation I worked really hard on. My first instinct was to spiral into negative self-talk, but I caught myself. Took a walk, called my therapist and left a message asking if we could move up our next appointment. The old me would have just stewed in it. I'm trying to be more proactive about my mental health. Spent the evening doing art therapy - just sketching and painting without judgment. The colors felt therapeutic."""
        },
        {
            "date": "2026-01-17",
            "content": """Therapy session today was intense but helpful. We talked about my tendency to seek external validation and how it affects my self-worth. Dr. Martinez helped me see patterns I hadn't noticed - how I constantly check if others approve of me, and how crushing it feels when they don't. She gave me homework: write down three things I did well each day, regardless of whether anyone notices. It feels silly, but I'm going to try. Today: 1) I was honest about my feelings, 2) I showed up for myself, 3) I'm choosing growth over comfort."""
        },
        {
            "date": "2026-01-18",
            "content": """Weekend! Spent today with friends - something I've been avoiding lately because I felt like I didn't have the energy to 'perform' being happy. But I was honest with them about struggling, and they were so supportive. We had a game night, and I actually laughed - like really laughed - for the first time in weeks. It reminded me that connection is healing. I don't have to go through hard times alone. Made plans to see them again next week. Baby steps."""
        },
        {
            "date": "2026-01-19",
            "content": """Quiet Sunday. Needed to recharge after yesterday's socializing (even good things can be draining when you're recovering). Did my three accomplishments practice: 1) I honored my need for rest, 2) I cooked a healthy meal instead of ordering takeout, 3) I responded to texts instead of avoiding them. Started planning some goals for the next month - nothing too ambitious, just small things that make me feel good. Like going to yoga twice a week, reading for 20 minutes before bed, and limiting work email after 7 PM."""
        },
        {
            "date": "2026-01-20",
            "content": """Monday hit differently this week. Still challenging, but I feel more equipped to handle it. Had a project meeting and actually contributed ideas without second-guessing myself. My coworker Alex said my suggestion was really creative - and I let myself accept the compliment instead of deflecting. That's progress! The anxiety is still there - it's not gone - but it's quieter now. More like background noise than a screaming alarm. I'm learning to coexist with it rather than let it run the show."""
        },
        {
            "date": "2026-01-21",
            "content": """Tough day. Didn't sleep well - old anxious thoughts crept back in around 2 AM. Why does it always hit at 2 AM? Spent half the night worrying about an upcoming presentation. At work, I felt off-balance, like I was back at square one. But here's the difference: I didn't beat myself up about it. Recovery isn't linear - Dr. Martinez's words keep echoing in my head. I let myself have a hard day without making it mean I'm failing. Ordered comfort food, watched my favorite show, went to bed early. Tomorrow is a new day."""
        },
        {
            "date": "2026-01-22",
            "content": """Presentation day. I was so nervous this morning I almost called in sick. But I didn't. I showed up. I did the thing. And you know what? It went... okay. Not perfect, not terrible, just okay. And that's enough. A few people asked good questions, which means they were actually listening. Afterward, I didn't immediately ask everyone if I did okay - that's huge for me. Celebrated by treating myself to that expensive coffee I always skip. Started thinking about what I want to talk about in therapy next week - maybe my fear of being seen as 'too much' or 'not enough.'"""
        },
        {
            "date": "2026-01-23",
            "content": """Reflecting on these past two weeks. I've been on a roller coaster - some really low lows and some encouraging highs. But overall, I feel like I'm moving in a direction that feels healthier. I'm learning to be gentler with myself, to ask for help, to celebrate small wins, and to not catastrophize setbacks. The anxiety and self-doubt are still there - I'm not 'cured' - but I'm building tools to manage them. Three accomplishments today: 1) I'm showing up for myself in this journal, 2) I'm committed to my therapy journey, 3) I'm choosing hope even when it's hard. Here's to continued growth."""
        }
    ]
    
    print(f"\n📝 Adding {len(entries)} diary entries...")
    
    # Clear existing entries for these dates (if any) for this user
    cursor.execute("""
        DELETE FROM journal_entries 
        WHERE user_id = ? AND date BETWEEN '2026-01-10' AND '2026-01-23'
    """, (user_id,))
    
    # Insert new entries
    for entry in entries:
        cursor.execute("""
            INSERT INTO journal_entries (user_id, content, date, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            user_id,
            entry['content'],
            entry['date'],
            datetime.now(),
            datetime.now()
        ))
    
    conn.commit()
    print(f"✅ Successfully added {len(entries)} entries")
    
    # Verify
    cursor.execute("""
        SELECT date, substr(content, 1, 50) as preview 
        FROM journal_entries 
        WHERE user_id = ? 
        ORDER BY date ASC
    """, (user_id,))
    
    print("\n📊 Entries in database:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}...")
    
    conn.close()

if __name__ == '__main__':
    print("="*70)
    print("📔 MorningTide Diary Entries Population Script")
    print("="*70)
    print()
    print("This will add 14 diary entries from January 10-23, 2026")
    print("The entries follow an emotional journey with ups and downs:")
    print("  • Days 1-2: Deep struggle with work stress and anxiety")
    print("  • Days 3-5: Small improvements, trying new coping strategies")
    print("  • Days 6-7: Ups and downs, learning to set boundaries")
    print("  • Days 8-10: Therapy insights, reconnecting with friends")
    print("  • Days 11-14: Progress with setbacks, building resilience")
    print()
    
    response = input("Continue? (yes/no): ")
    
    if response.lower() == 'yes':
        populate_diary_entries()
        print()
        print("="*70)
        print("✅ Done! Your diary now has realistic entries to test RAG features.")
        print("="*70)
    else:
        print("❌ Cancelled")