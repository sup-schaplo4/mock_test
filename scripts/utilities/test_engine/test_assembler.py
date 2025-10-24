"""
Test Generator Module
Main orchestrator that generates complete mock tests from blueprints.
Integrates blueprint loading, question selection, DI selection, and test assembly.
"""

import json
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from master_loader import MasterLoader, load_masters
from question_selector import QuestionSelector
from di_selector import DISelector


class TestGenerator:
    """Generates complete mock tests from blueprints."""
    
    def __init__(self, master_loader: MasterLoader):
        """
        Initialize the test generator.
        
        Args:
            master_loader: MasterLoader instance with loaded masters
        """
        self.master_loader = master_loader
        self.question_selector = QuestionSelector(master_loader)
        self.di_selector = DISelector(master_loader)
        self.generation_log = []
        
    def generate_test(
        self,
        blueprint: Dict[str, Any],
        shuffle_questions: bool = True,
        allow_duplicates: bool = False
    ) -> Dict[str, Any]:
        """
        Generate a complete test from a blueprint.
        
        Args:
            blueprint: Blueprint dictionary (already loaded JSON)
            shuffle_questions: Whether to shuffle questions within sections
            allow_duplicates: Whether to allow duplicate questions
        
        Returns:
            Complete test dictionary
        """
        test_id = blueprint.get("test_id", "UNKNOWN")
        test_name = blueprint.get("test_name", "Unknown Test")
        
        print(f"\n🚀 Generating test: {test_name} ({test_id})")
        print("=" * 80)
        
        # Reset selectors for fresh selection
        self.question_selector.reset()
        self.di_selector.reset()
        
        # Initialize test structure
        test = {
            "test_id": test_id,
            "test_name": test_name,
            "total_questions": blueprint.get("total_questions", 0),
            "total_marks": blueprint.get("total_marks", blueprint.get("total_questions", 0)),
            "duration_minutes": blueprint.get("duration_minutes", 120),
            "generated_at": datetime.now().isoformat(),
            "sections": []
        }
        
        # Generate each section
        all_reports = []
        
        for section_config in blueprint.get("sections", []):
            section_data, section_report = self._generate_section(
                section_config,
                shuffle_questions,
                allow_duplicates
            )
            
            test["sections"].append(section_data)
            all_reports.append(section_report)
        
        # Add generation metadata
        test["generation_metadata"] = self._create_metadata(blueprint, all_reports)
        
        # Validate test
        is_valid, validation_errors = self._validate_test(test, blueprint)
        
        if not is_valid:
            print("\n❌ Test validation failed:")
            for error in validation_errors:
                print(f"   {error}")
        else:
            print(f"\n✅ Test generation completed successfully!")
            print(f"   Total Questions: {test['total_questions']}")
            print(f"   Total Sections: {len(test['sections'])}")
        
        return test
    
    def _generate_section(
        self,
        section_config: Dict[str, Any],
        shuffle: bool,
        allow_duplicates: bool
    ) -> tuple:
        """
        Generate a complete section with questions.
        
        Args:
            section_config: Section configuration from blueprint
            shuffle: Whether to shuffle questions
            allow_duplicates: Whether to allow duplicate questions
        
        Returns:
            Tuple of (section_data, section_report)
        """
        section_id = section_config.get("section_id", "UNKNOWN")
        section_name = section_config.get("section_name", "Unknown Section")
        
        print(f"\n📝 Generating section: {section_name} ({section_id})")
        print("-" * 80)
        
        # Initialize section structure
        section = {
            "section_id": section_id,
            "section_name": section_name,
            "total_questions": section_config.get("total_questions", 0),
            "questions": []
        }
        
        # Check if section has DI
        topic_distribution = section_config.get("topic_distribution", {})
        di_questions_needed = topic_distribution.get("Data Interpretation", 0)
        
        reports = {}
        
        # Handle DI if present
        if di_questions_needed > 0:
            # In blueprints, "Data Interpretation": N means N DI sets, not N questions
            # Each DI set contains 5 questions
            di_sets_needed = di_questions_needed
            di_questions_needed = di_sets_needed * 5  # Convert to actual question count
            
            print(f"   📊 DI sets needed: {di_sets_needed} (total: {di_questions_needed} questions)")
            
            # Calculate DI difficulty distribution
            di_difficulty = self._calculate_di_difficulty(
                section_config.get("difficulty_distribution", {}),
                section_config.get("total_questions", 0),
                di_questions_needed
            )
            
            print(f"   📊 Selecting {di_sets_needed} DI sets...")
            
            # Select DI sets
            di_sets, di_report = self.di_selector.select_di_sets(
                di_sets_needed,
                di_difficulty,
                allow_duplicates
            )
            
            # Get questions from DI sets
            di_questions = self.di_selector.get_questions_from_selected_sets(di_sets)
            section["questions"].extend(di_questions)
            reports["di"] = di_report
            
            print(f"   ✅ Added {len(di_questions)} DI questions")
        
        # Select regular questions (non-DI)
        print(f"   📝 Selecting regular questions...")
        regular_questions, regular_report = self.question_selector.select_questions_for_section(
            section_config,
            allow_duplicates
        )
        
        section["questions"].extend(regular_questions)
        reports["regular"] = regular_report
        
        print(f"   ✅ Added {len(regular_questions)} regular questions")
        
        # Shuffle questions if requested
        if shuffle:
            random.shuffle(section["questions"])
            print(f"   🔀 Questions shuffled")
        
        # Add question numbers
        for idx, question in enumerate(section["questions"], 1):
            question["question_number"] = idx
        
        print(f"\n✅ Section '{section_id}' complete: {len(section['questions'])} total questions")
        
        return section, reports
    
    def _calculate_di_difficulty(
        self,
        section_difficulty: Dict[str, int],
        section_total: int,
        di_total: int
    ) -> Dict[str, int]:
        """
        Calculate proportional difficulty distribution for DI.
        
        Args:
            section_difficulty: Section-level difficulty distribution
            section_total: Total questions in section
            di_total: Total DI questions needed
        
        Returns:
            Difficulty distribution for DI questions
        """
        if section_total == 0:
            return {"Easy": 0, "Medium": 0, "Hard": 0}
        
        di_difficulty = {}
        total_allocated = 0
        
        for difficulty in ["Easy", "Medium", "Hard"]:
            section_count = section_difficulty.get(difficulty, 0)
            proportion = section_count / section_total
            allocated = round(proportion * di_total)
            di_difficulty[difficulty] = allocated
            total_allocated += allocated
        
        # Adjust for rounding errors
        diff = di_total - total_allocated
        if diff != 0:
            max_difficulty = max(di_difficulty.keys(), key=lambda k: di_difficulty[k])
            di_difficulty[max_difficulty] += diff
        
        return di_difficulty
    
    def _create_metadata(
        self,
        blueprint: Dict[str, Any],
        section_reports: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create generation metadata.
        
        Args:
            blueprint: Blueprint dictionary
            section_reports: List of section generation reports
        
        Returns:
            Metadata dictionary
        """
        return {
            "generated_at": datetime.now().isoformat(),
            "blueprint_id": blueprint.get("test_id"),
            "source_blueprint": blueprint.get("test_name"),
            "total_sections": len(blueprint.get("sections", [])),
            "section_reports": section_reports,
            "selection_statistics": self.question_selector.get_selection_statistics()
        }
    
    def _validate_test(
        self,
        test: Dict[str, Any],
        blueprint: Dict[str, Any]
    ) -> tuple:
        """
        Validate generated test against blueprint.
        
        Args:
            test: Generated test dictionary
            blueprint: Blueprint dictionary
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Check total questions
        actual_total = sum(len(s["questions"]) for s in test["sections"])
        expected_total = blueprint.get("total_questions", 0)
        
        if actual_total != expected_total:
            errors.append(
                f"Total questions mismatch: Expected {expected_total}, got {actual_total}"
            )
        
        # Check each section
        for idx, section in enumerate(test["sections"]):
            section_config = blueprint["sections"][idx]
            section_id = section["section_id"]
            
            expected_count = section_config.get("total_questions", 0)
            actual_count = len(section["questions"])
            
            if actual_count != expected_count:
                errors.append(
                    f"Section '{section_id}': Expected {expected_count} questions, got {actual_count}"
                )
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def save_test(self, test: Dict[str, Any], output_path: str):
        """
        Save generated test to JSON file.
        
        Args:
            test: Generated test dictionary
            output_path: Path to save file
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(test, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Test saved to: {output_path}")


# Convenience function
def generate_test_from_blueprint(
    blueprint_path: str,
    master_loader: MasterLoader,
    output_path: Optional[str] = None,
    shuffle_questions: bool = True,
    allow_duplicates: bool = False
) -> Dict[str, Any]:
    """
    Convenience function to generate a test from a blueprint file.
    
    Args:
        blueprint_path: Path to blueprint JSON file
        master_loader: MasterLoader instance
        output_path: Optional path to save generated test
        shuffle_questions: Whether to shuffle questions
        allow_duplicates: Whether to allow duplicate questions
    
    Returns:
        Generated test dictionary
    """
    # Load blueprint from file
    with open(blueprint_path, 'r', encoding='utf-8') as f:
        blueprint = json.load(f)
    
    # Generate test
    generator = TestGenerator(master_loader)
    test = generator.generate_test(blueprint, shuffle_questions, allow_duplicates)
    
    # Save if output path provided
    if output_path:
        generator.save_test(test, output_path)
    
    return test


# For testing
if __name__ == "__main__":
    print("\n🔍 Testing Test Generator")
    print("=" * 80)
    
    # Master files
    master_files = [
        "english_master_question_bank.json",
        "general_awareness_master_question_bank.json",
        "reasoning_master_question_bank.json",
        "arithmetic_master_question_bank.json",
        "di_master_question_bank.json"
    ]
    
    try:
        # Load masters
        print("\n📚 Loading master files...")
        loader = load_masters(master_files)
        
        # Load blueprint
        blueprint_path = "data/blueprints/RBI_P1_MOCK_01.json"
        print(f"\n📋 Loading blueprint: {blueprint_path}")
        
        with open(blueprint_path, 'r', encoding='utf-8') as f:
            blueprint = json.load(f)
        
        # Generate test
        generator = TestGenerator(loader)
        test = generator.generate_test(
            blueprint,
            shuffle_questions=True,
            allow_duplicates=False
        )
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 Test Generation Summary")
        print("=" * 80)
        print(f"Test ID: {test['test_id']}")
        print(f"Test Name: {test['test_name']}")
        print(f"Total Questions: {test['total_questions']}")
        print(f"Total Sections: {len(test['sections'])}")
        
        print("\nSection Breakdown:")
        for section in test["sections"]:
            print(f"   {section['section_id']}: {len(section['questions'])} questions")
            
            # Count difficulty
            difficulty_count = {"Easy": 0, "Medium": 0, "Hard": 0}
            for q in section["questions"]:
                diff = q.get("difficulty", "Medium")
                if diff in difficulty_count:
                    difficulty_count[diff] += 1
            
            print(f"      Difficulty: Easy={difficulty_count['Easy']}, "
                  f"Medium={difficulty_count['Medium']}, Hard={difficulty_count['Hard']}")
        
        # Save test
        output_path = "data/generated/tests/RBI_P1_MOCK_01_generated.json"
        generator.save_test(test, output_path)
        
        print("\n✅ Test Generator Test Completed Successfully\n")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}\n")
        import traceback
        traceback.print_exc()
