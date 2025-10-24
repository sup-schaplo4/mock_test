import json
from pathlib import Path
from collections import Counter
import uuid

def make_question_ids_unique(masters_dir: str = "data/generated/master_questions"):
    """
    Make all question IDs unique across all master bank JSON files.
    
    Args:
        masters_dir: Directory containing master bank JSON files
    """
    masters_path = Path(masters_dir)
    
    if not masters_path.exists():
        print(f"❌ Directory not found: {masters_dir}")
        return
    
    print("\n" + "="*80)
    print("🔧 MAKING QUESTION IDs UNIQUE")
    print("="*80)
    
    # Find all JSON files
    json_files = list(masters_path.glob("*.json"))
    
    if not json_files:
        print(f"\n❌ No JSON files found in {masters_dir}")
        return
    
    print(f"\n📁 Found {len(json_files)} JSON files")
    
    # Track all IDs across all files
    all_ids = []
    
    # Process each file
    for json_file in json_files:
        print(f"\n📄 Processing: {json_file.name}")
        
        try:
            # Load JSON
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            subject_name = data.get("subject", json_file.stem)
            
            # Handle DI (has di_sets structure)
            if "di_sets" in data:
                print(f"   Type: Data Interpretation Sets")
                total_questions = 0
                
                for set_idx, di_set in enumerate(data["di_sets"], 1):
                    # Make set_id unique
                    old_set_id = di_set.get("set_id", "")
                    new_set_id = f"DI_SET_{set_idx:03d}"
                    di_set["set_id"] = new_set_id
                    
                    # Make question IDs unique within the set
                    for q_idx, question in enumerate(di_set.get("questions", []), 1):
                        old_qid = question.get("question_id", "")
                        new_qid = f"DI_SET_{set_idx:03d}_Q{q_idx:02d}"
                        question["question_id"] = new_qid
                        all_ids.append(new_qid)
                        total_questions += 1
                
                print(f"   ✅ Updated {len(data['di_sets'])} DI sets, {total_questions} questions")
            
            # Handle regular questions
            elif "questions" in data:
                print(f"   Type: Regular Questions")
                questions = data["questions"]
                
                # Get subject prefix (first 3 letters, uppercase)
                prefix = subject_name[:3].upper()
                
                for idx, question in enumerate(questions, 1):
                    old_qid = question.get("question_id", "")
                    new_qid = f"{prefix}_Q{idx:04d}"
                    question["question_id"] = new_qid
                    all_ids.append(new_qid)
                
                print(f"   ✅ Updated {len(questions)} questions")
            
            else:
                print(f"   ⚠️  Unknown structure, skipping")
                continue
            
            # Save updated JSON
            backup_file = json_file.with_suffix('.json.backup')
            
            # Create backup
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Save updated file
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"   💾 Saved (backup created: {backup_file.name})")
        
        except Exception as e:
            print(f"   ❌ Error processing {json_file.name}: {e}")
    
    # Check for duplicates
    print("\n" + "="*80)
    print("🔍 VERIFICATION")
    print("="*80)
    
    id_counts = Counter(all_ids)
    duplicates = {qid: count for qid, count in id_counts.items() if count > 1}
    
    if duplicates:
        print(f"\n⚠️  WARNING: Found {len(duplicates)} duplicate IDs:")
        for qid, count in list(duplicates.items())[:10]:
            print(f"   {qid}: appears {count} times")
        if len(duplicates) > 10:
            print(f"   ... and {len(duplicates) - 10} more")
    else:
        print(f"\n✅ SUCCESS! All {len(all_ids)} question IDs are unique!")
    
    print("\n" + "="*80)
    print("✅ COMPLETED")
    print("="*80)
    print(f"\n📝 Summary:")
    print(f"   Total IDs processed: {len(all_ids)}")
    print(f"   Unique IDs: {len(set(all_ids))}")
    print(f"   Files processed: {len(json_files)}")
    print(f"   Backups created: {len(json_files)} (.json.backup files)")
    print("\n💡 Original files backed up with .json.backup extension")


if __name__ == "__main__":
    # Run the script
    make_question_ids_unique("data/generated/master_questions")
    
    print("\n" + "="*80)
    print("Press Enter to exit...")
    input()
