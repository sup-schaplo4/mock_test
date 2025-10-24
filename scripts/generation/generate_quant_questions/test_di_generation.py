"""
Simple test script to generate a Table-based DI set
"""

import os
import json
from openai import OpenAI
from prompts.di_prompts import get_di_generation_prompt, get_di_system_prompt

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_table_di():
    """Generate a simple table-based DI set"""
    
    print("🚀 Starting Table DI Generation...")
    print("=" * 60)
    
    # Get prompts
    system_prompt = get_di_system_prompt()
    user_prompt = get_di_generation_prompt(
        di_type="Table",
        topic="Sales & Revenue Analysis",
        difficulty="Medium",
        num_questions=5
    )
    
    print("\n📝 System Prompt:")
    print("-" * 60)
    print(system_prompt[:200] + "...")
    
    print("\n📝 User Prompt:")
    print("-" * 60)
    print(user_prompt[:500] + "...")
    
    print("\n⏳ Calling OpenAI API...")
    
    try:
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=4000
        )
        
        # Extract response
        content = response.choices[0].message.content
        
        print("\n✅ Response received!")
        print("=" * 60)
        
        # Try to parse JSON
        # Remove markdown code blocks if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        # Parse JSON
        di_set = json.loads(content)
        
        print("\n📊 Generated DI Set:")
        print("=" * 60)
        print(f"ID: {di_set.get('di_set_id')}")
        print(f"Topic: {di_set.get('topic')}")
        print(f"Difficulty: {di_set.get('difficulty')}")
        print(f"Number of Questions: {len(di_set.get('questions', []))}")
        
        print("\n📋 Data Source:")
        print("-" * 60)
        print(json.dumps(di_set.get('data_source'), indent=2))
        
        print("\n❓ Questions:")
        print("-" * 60)
        for idx, q in enumerate(di_set.get('questions', []), 1):
            print(f"\nQ{idx}. {q.get('question')}")
            print(f"   Correct Answer: {q.get('correct_answer')}")
            print(f"   Difficulty: {q.get('difficulty')}")
        
        # Save to file
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        
        output_file = os.path.join(output_dir, "test_table_di.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(di_set, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Saved to: {output_file}")
        print("\n✅ Test completed successfully!")
        
        return di_set
        
    except json.JSONDecodeError as e:
        print(f"\n❌ JSON parsing error: {e}")
        print("\nRaw response:")
        print(content)
        return None
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None


if __name__ == "__main__":
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not found in environment variables")
        print("Please set it using: export OPENAI_API_KEY='your-key-here'")
    else:
        print("✅ API Key found")
        di_set = generate_table_di()
        
        if di_set:
            print("\n" + "="*60)
            print("🎉 SUCCESS! DI set generated and saved.")
            print("="*60)
