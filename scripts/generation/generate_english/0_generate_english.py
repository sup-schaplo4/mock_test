import json
from collections import Counter

# Load your master dataset
with open('data/RBI_Master_Dataset.json', 'r') as f:
    data = json.load(f)

# Filter English questions
english_questions = [q for q in data['questions'] if q['subject'] == 'English']

print(f"Total English questions in dataset: {len(english_questions)}")

# Analyze by year
years = Counter([q['year'] for q in english_questions])
print(f"\nYear-wise distribution: {dict(years)}")

# Try to infer topics (if metadata exists)
topics = Counter([q.get('topics', ['Unknown'])[0] if q.get('topics') else 'Unknown' 
                  for q in english_questions])
print(f"\nTopic distribution: {dict(topics)}")

# Analyze difficulty
difficulty = Counter([q.get('difficulty', 'Unknown') for q in english_questions])
print(f"\nDifficulty distribution: {dict(difficulty)}")

# Check quality scores
avg_quality = sum([q.get('quality_score', 0) for q in english_questions]) / len(english_questions)
print(f"\nAverage quality score: {avg_quality:.2f}")

# Save filtered English questions for reference
output = {
    "total_count": len(english_questions),
    "questions": english_questions
}

with open('data/english_reference_set.json', 'w') as f:
    json.dump(output, f, indent=2)

print(f"\n✅ Saved English reference set to data/english_reference_set.json")
