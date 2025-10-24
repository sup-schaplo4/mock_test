"""
Master Loader Module
Loads and parses all master question bank files.
Handles different JSON structures for each subject.
"""

import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from collections import defaultdict


class MasterLoader:
    """Loads and indexes master question files."""
    
    def __init__(self, master_dir: str = "data/generated/master_questions"):
        """
        Initialize the master loader.
        
        Args:
            master_dir: Directory containing master question files
        """
        self.master_dir = Path(master_dir)
        self.masters = {}
        self.indexes = {}
        
        if not self.master_dir.exists():
            raise FileNotFoundError(f"Master directory not found: {master_dir}")
    
    def load_master(self, filename: str) -> Dict[str, Any]:
        """
        Load a master file and return its data.
        
        Args:
            filename: Name of the master file (e.g., "english_master.json")
        
        Returns:
            Dictionary containing the master file data
        
        Raises:
            FileNotFoundError: If master file doesn't exist
            json.JSONDecodeError: If file contains invalid JSON
        """
        file_path = self.master_dir / filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"Master file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.masters[filename] = data
            print(f"✅ Loaded: {filename}")
            
            return data
            
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON in {filename}: {e.msg}",
                e.doc,
                e.pos
            )
        except Exception as e:
            raise Exception(f"Error loading {filename}: {str(e)}")
    
    def load_all_masters(self, source_files: List[str]) -> Dict[str, Any]:
        """
        Load multiple master files.
        
        Args:
            source_files: List of master filenames to load
        
        Returns:
            Dictionary mapping filename to master data
        """
        loaded = {}
        
        for filename in source_files:
            try:
                loaded[filename] = self.load_master(filename)
            except Exception as e:
                print(f"❌ Failed to load {filename}: {str(e)}")
                raise
        
        return loaded
    
    def build_index(self, filename: str) -> Dict[str, Any]:
        """
        Build searchable indexes for a master file.
        Creates indexes by: topic, difficulty, and topic+difficulty.
        
        Args:
            filename: Name of the master file
        
        Returns:
            Dictionary containing indexes
        """
        if filename not in self.masters:
            raise ValueError(f"Master file not loaded: {filename}")
        
        master_data = self.masters[filename]
        
        # Handle different master file structures
        if "di_master" in filename:
            index = self._build_di_index(master_data)
        else:
            index = self._build_regular_index(master_data)
        
        self.indexes[filename] = index
        return index
    
    def _build_regular_index(self, master_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build index for regular master files (non-DI).
        
        Structure:
        {
            "by_topic": {
                "Topic Name": [question_obj1, question_obj2, ...],
                ...
            },
            "by_difficulty": {
                "Easy": [question_obj1, ...],
                "Medium": [...],
                "Hard": [...]
            },
            "by_topic_difficulty": {
                "Topic Name": {
                    "Easy": [question_obj1, ...],
                    "Medium": [...],
                    "Hard": [...]
                },
                ...
            },
            "all_questions": [all question objects],
            "total_count": 290
        }
        """
        questions = master_data.get("questions", [])
        
        index = {
            "by_topic": defaultdict(list),
            "by_difficulty": defaultdict(list),
            "by_topic_difficulty": defaultdict(lambda: defaultdict(list)),
            "all_questions": questions,
            "total_count": len(questions)
        }
        
        for question in questions:
            # Get topic (handle different field names)
            topic = (
                question.get("topic") or 
                question.get("reasoning_topic") or 
                question.get("sub_topic") or
                "Unknown"
            )
            
            difficulty = question.get("difficulty", "Medium")
            
            # Build indexes
            index["by_topic"][topic].append(question)
            index["by_difficulty"][difficulty].append(question)
            index["by_topic_difficulty"][topic][difficulty].append(question)
        
        # Convert defaultdicts to regular dicts for JSON serialization
        index["by_topic"] = dict(index["by_topic"])
        index["by_difficulty"] = dict(index["by_difficulty"])
        index["by_topic_difficulty"] = {
            topic: dict(difficulties) 
            for topic, difficulties in index["by_topic_difficulty"].items()
        }
        
        return index
    
    def _build_di_index(self, master_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build index for DI master file.
        
        DI sets are atomic units (all 5 questions together).
        
        Structure:
        {
            "di_sets": [
                {
                    "di_set_id": "DI_BAR_CHART_001",
                    "topic": "Bar Chart - Sales Revenue Analysis",
                    "set_difficulty": "Easy",
                    "questions": [5 question objects],
                    "difficulty_footprint": {
                        "Easy": 2,
                        "Medium": 2,
                        "Hard": 1
                    }
                },
                ...
            ],
            "by_footprint": {
                "2-2-1": [set_obj1, set_obj2, ...],  # Easy-Medium-Hard counts
                "1-3-1": [...],
                ...
            },
            "all_sets": [all DI set objects],
            "total_sets": 25,
            "total_questions": 125
        }
        """
        di_questions = master_data.get("questions", [])
        
        index = {
            "di_sets": [],
            "by_footprint": defaultdict(list),
            "all_sets": [],
            "total_sets": len(di_questions),
            "total_questions": len(di_questions) * 5  # 5 questions per set
        }
        
        for di_set in di_questions:
            # Calculate difficulty footprint for this set
            footprint = {"Easy": 0, "Medium": 0, "Hard": 0}
            
            questions = di_set.get("questions", [])
            
            if len(questions) != 5:
                print(f"⚠️  Warning: DI set {di_set.get('di_set_id')} has {len(questions)} questions (expected 5)")
            
            for q in questions:
                difficulty = q.get("difficulty", "Medium")
                if difficulty in footprint:
                    footprint[difficulty] += 1
            
            # Create set object
            set_obj = {
                "di_set_id": di_set.get("di_set_id"),
                "topic": di_set.get("topic"),
                "set_difficulty": di_set.get("difficulty"),  # Set-level (not used)
                "questions": questions,
                "difficulty_footprint": footprint
            }
            
            index["di_sets"].append(set_obj)
            index["all_sets"].append(set_obj)
            
            # Create footprint key (e.g., "2-2-1" for 2 Easy, 2 Medium, 1 Hard)
            footprint_key = f"{footprint['Easy']}-{footprint['Medium']}-{footprint['Hard']}"
            index["by_footprint"][footprint_key].append(set_obj)
        
        # Convert defaultdict to regular dict
        index["by_footprint"] = dict(index["by_footprint"])
        
        return index
    
    def get_questions_by_topic_difficulty(
        self, 
        filename: str, 
        topic: str, 
        difficulty: str
    ) -> List[Dict[str, Any]]:
        """
        Get questions filtered by topic and difficulty.
        
        Args:
            filename: Master filename
            topic: Topic name
            difficulty: Difficulty level (Easy/Medium/Hard)
        
        Returns:
            List of question objects
        """
        if filename not in self.indexes:
            self.build_index(filename)
        
        index = self.indexes[filename]
        
        # Handle DI separately
        if "di_master" in filename:
            return []  # DI sets handled by separate method
        
        return index["by_topic_difficulty"].get(topic, {}).get(difficulty, [])
    
    def get_di_sets(self, filename: str = "di_master_question_bank.json") -> List[Dict[str, Any]]:
        """
        Get all DI sets.
        
        Args:
            filename: DI master filename
        
        Returns:
            List of DI set objects
        """
        if filename not in self.indexes:
            self.build_index(filename)
        
        return self.indexes[filename]["all_sets"]
    
    def get_statistics(self, filename: str) -> Dict[str, Any]:
        """
        Get statistics for a master file.
        
        Args:
            filename: Master filename
        
        Returns:
            Dictionary containing statistics
        """
        if filename not in self.indexes:
            self.build_index(filename)
        
        index = self.indexes[filename]
        
        if "di_master" in filename:
            return {
                "total_sets": index["total_sets"],
                "total_questions": index["total_questions"],
                "footprint_distribution": {
                    key: len(sets) 
                    for key, sets in index["by_footprint"].items()
                }
            }
        else:
            return {
                "total_questions": index["total_count"],
                "topics": list(index["by_topic"].keys()),
                "topic_counts": {
                    topic: len(questions) 
                    for topic, questions in index["by_topic"].items()
                },
                "difficulty_counts": {
                    difficulty: len(questions)
                    for difficulty, questions in index["by_difficulty"].items()
                }
            }
    
    def validate_availability(
        self, 
        filename: str, 
        topic: str, 
        difficulty: str, 
        required: int
    ) -> tuple[bool, int, int]:
        """
        Check if enough questions are available for a topic/difficulty.
        
        Args:
            filename: Master filename
            topic: Topic name
            difficulty: Difficulty level
            required: Required number of questions
        
        Returns:
            Tuple of (is_sufficient, available, missing)
        """
        available_questions = self.get_questions_by_topic_difficulty(
            filename, topic, difficulty
        )
        
        available = len(available_questions)
        missing = max(0, required - available)
        is_sufficient = available >= required
        
        return is_sufficient, available, missing


# Convenience functions
def load_masters(source_files: List[str], master_dir: str = "data/generated/master_questions") -> MasterLoader:
    """
    Load master files and build indexes.
    
    Args:
        source_files: List of master filenames
        master_dir: Directory containing master files
    
    Returns:
        MasterLoader instance with loaded and indexed data
    """
    loader = MasterLoader(master_dir)
    loader.load_all_masters(source_files)
    
    # Build indexes for all loaded masters
    for filename in source_files:
        loader.build_index(filename)
        
        # Print statistics
        stats = loader.get_statistics(filename)
        if "total_sets" in stats:
            print(f"   📊 {filename}: {stats['total_sets']} sets, {stats['total_questions']} questions")
        else:
            print(f"   📊 {filename}: {stats['total_questions']} questions, {len(stats['topics'])} topics")
    
    return loader


# For testing
if __name__ == "__main__":
    print("\n🔍 Testing Master Loader")
    print("=" * 80)
    
    # Test loading all masters
    all_masters = [
        "english_master_question_bank.json",
        "general_awareness_master_question_bank.json",
        "reasoning_master_question_bank.json",
        "arithmetic_master_question_bank.json",
        "di_master_question_bank.json"
    ]
    
    try:
        loader = load_masters(all_masters)
        
        print("\n📋 Summary:")
        print("-" * 80)
        
        for filename in all_masters:
            stats = loader.get_statistics(filename)
            print(f"\n{filename}:")
            
            if "total_sets" in stats:
                print(f"  Total Sets: {stats['total_sets']}")
                print(f"  Total Questions: {stats['total_questions']}")
                print(f"  Footprint Distribution:")
                for footprint, count in stats['footprint_distribution'].items():
                    print(f"    {footprint}: {count} sets")
            else:
                print(f"  Total Questions: {stats['total_questions']}")
                print(f"  Topics: {len(stats['topics'])}")
                print(f"  Difficulty Distribution:")
                for diff, count in stats['difficulty_counts'].items():
                    print(f"    {diff}: {count}")
        
        print("\n✅ Master Loader Test Completed Successfully\n")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}\n")
        import traceback
        traceback.print_exc()
