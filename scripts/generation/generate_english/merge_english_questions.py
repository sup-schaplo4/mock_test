#!/usr/bin/env python3
"""
Merge English Reference Questions with Master Question Bank
Keeps only the fields that exist in the master file structure
"""

import json
from datetime import datetime
from pathlib import Path

def merge_english_questions():
    """Merge reference questions with master question bank."""
    
    # File paths
    reference_file = "data/reference_questions/english/english_reference_set_classified.json"
    master_file = "data/generated/master_questions/english_master_question_bank.json"
    output_file = "data/generated/master_questions/english_master_question_bank_merged.json"
    
    print("🔄 Loading reference questions...")
    with open(reference_file, 'r', encoding='utf-8') as f:
        reference_data = json.load(f)
    
    print("🔄 Loading master question bank...")
    with open(master_file, 'r', encoding='utf-8') as f:
        master_data = json.load(f)
    
    # Get the structure of master questions to know which fields to keep
    master_question_fields = set()
    if master_data.get("questions") and len(master_data["questions"]) > 0:
        master_question_fields = set(master_data["questions"][0].keys())
        print(f"📋 Master question fields: {sorted(master_question_fields)}")
    
    # Process reference questions
    merged_questions = []
    reference_questions = reference_data.get("questions", [])
    
    print(f"📊 Processing {len(reference_questions)} reference questions...")
    
    for idx, ref_question in enumerate(reference_questions):
        # Create a new question with only master file fields
        merged_question = {}
        
        # Map reference fields to master fields
        field_mapping = {
            "questions": "question",  # Reference uses "questions", master uses "question"
            "id": "question_id",     # Reference uses "id", master uses "question_id"
            "topic": "topic",        # Same field name
            "difficulty": "difficulty",  # Same field name
            "subject": "subject",    # Same field name
            "options": "options",    # Same field name
            "correct_answer": "correct_answer",  # Same field name
            "explanation": "explanation"  # Same field name
        }
        
        # Map fields that exist in both
        for ref_field, master_field in field_mapping.items():
            if ref_field in ref_question and master_field in master_question_fields:
                merged_question[master_field] = ref_question[ref_field]
        
        # Add default values for required master fields that don't exist in reference
        if "generated_date" in master_question_fields and "generated_date" not in merged_question:
            merged_question["generated_date"] = datetime.now().isoformat()
        
        if "source" in master_question_fields and "source" not in merged_question:
            merged_question["source"] = "Reference_Questions"
        
        if "reference_count" in master_question_fields and "reference_count" not in merged_question:
            merged_question["reference_count"] = 0
        
        if "generation_model" in master_question_fields and "generation_model" not in merged_question:
            merged_question["generation_model"] = "Reference_Data"
        
        if "merged_date" in master_question_fields and "merged_date" not in merged_question:
            merged_question["merged_date"] = datetime.now().isoformat()
        
        # Generate question_id if not present
        if "question_id" not in merged_question:
            merged_question["question_id"] = f"REF_{idx+1:04d}"
        
        merged_questions.append(merged_question)
    
    # Create merged data structure
    merged_data = {
        "metadata": {
            "title": "RBI Grade B Phase 1 - English Master Question Bank (Merged)",
            "total_questions": len(master_data.get("questions", [])) + len(merged_questions),
            "creation_date": datetime.now().isoformat(),
            "version": "2.0",
            "source_files": {
                "master": "english_master_question_bank.json",
                "reference": "english_reference_set_classified.json"
            },
            "source_counts": {
                "master": len(master_data.get("questions", [])),
                "reference": len(merged_questions),
                "total": len(master_data.get("questions", [])) + len(merged_questions)
            },
            "merge_date": datetime.now().isoformat()
        },
        "questions": master_data.get("questions", []) + merged_questions
    }
    
    # Update difficulty and topic distributions
    difficulty_dist = {"Easy": 0, "Medium": 0, "Hard": 0}
    topic_dist = {}
    
    for question in merged_data["questions"]:
        diff = question.get("difficulty", "Medium")
        if diff in difficulty_dist:
            difficulty_dist[diff] += 1
        
        topic = question.get("topic", "Unknown")
        topic_dist[topic] = topic_dist.get(topic, 0) + 1
    
    merged_data["metadata"]["difficulty_distribution"] = difficulty_dist
    merged_data["metadata"]["topic_distribution"] = topic_dist
    
    # Save merged data
    print(f"💾 Saving merged data to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print("\n" + "="*80)
    print("✅ MERGE COMPLETED SUCCESSFULLY")
    print("="*80)
    print(f"📊 Master questions: {len(master_data.get('questions', []))}")
    print(f"📊 Reference questions: {len(merged_questions)}")
    print(f"📊 Total questions: {len(merged_data['questions'])}")
    print(f"📊 Difficulty distribution: {difficulty_dist}")
    print(f"📊 Topics: {len(topic_dist)} unique topics")
    print(f"💾 Output file: {output_file}")
    print("="*80)

if __name__ == "__main__":
    merge_english_questions()
