"""
Test Validation Script
Validates generated tests for quality, completeness, and correctness.
Checks difficulty distribution, topic coverage, and structural integrity.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import Counter

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))


class TestValidator:
    """Validates generated test quality."""
    
    def __init__(self):
        """Initialize the validator."""
        self.validation_report = {
            "tests_validated": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "test_results": []
        }
    
    def validate_test_file(self, test_path: str) -> Dict[str, Any]:
        """
        Validate a single test file.
        
        Args:
            test_path: Path to test JSON file
        
        Returns:
            Validation report dictionary
        """
        print(f"\n{'='*80}")
        print(f"🔍 Validating: {Path(test_path).name}")
        print(f"{'='*80}")
        
        # Load test
        with open(test_path, 'r', encoding='utf-8') as f:
            test = json.load(f)
        
        # Initialize validation results
        results = {
            "test_id": test.get("test_id"),
            "test_name": test.get("test_name"),
            "file": Path(test_path).name,
            "passed": True,
            "errors": [],
            "warnings": [],
            "info": {}
        }
        
        # Run validation checks
        self._validate_structure(test, results)
        self._validate_question_count(test, results)
        self._validate_sections(test, results)
        self._validate_difficulty_distribution(test, results)
        self._validate_topic_distribution(test, results)
        self._validate_question_ids(test, results)
        self._check_duplicates(test, results)
        
        # Determine if test passed
        results["passed"] = len(results["errors"]) == 0
        
        # Update counters
        self.validation_report["tests_validated"] += 1
        if results["passed"]:
            self.validation_report["tests_passed"] += 1
        else:
            self.validation_report["tests_failed"] += 1
        
        self.validation_report["test_results"].append(results)
        
        # Print results
        self._print_validation_results(results)
        
        return results
    
    def _validate_structure(self, test: Dict[str, Any], results: Dict[str, Any]):
        """Validate basic test structure."""
        required_fields = [
            "test_id", "test_name", "total_questions", 
            "total_marks", "duration_minutes", "sections"
        ]
        
        for field in required_fields:
            if field not in test:
                results["errors"].append(f"Missing required field: {field}")
        
        if not isinstance(test.get("sections"), list):
            results["errors"].append("'sections' must be a list")
        elif len(test.get("sections", [])) == 0:
            results["errors"].append("Test has no sections")
    
    def _validate_question_count(self, test: Dict[str, Any], results: Dict[str, Any]):
        """Validate question counts."""
        expected_total = test.get("total_questions", 0)
        
        actual_total = 0
        for section in test.get("sections", []):
            actual_total += len(section.get("questions", []))
        
        results["info"]["expected_questions"] = expected_total
        results["info"]["actual_questions"] = actual_total
        
        if actual_total != expected_total:
            results["errors"].append(
                f"Question count mismatch: Expected {expected_total}, got {actual_total}"
            )
        
        # Validate each section
        for section in test.get("sections", []):
            section_id = section.get("section_id", "Unknown")
            expected_section = section.get("total_questions", 0)
            actual_section = len(section.get("questions", []))
            
            if actual_section != expected_section:
                results["errors"].append(
                    f"Section '{section_id}': Expected {expected_section} questions, got {actual_section}"
                )
    
    def _validate_sections(self, test: Dict[str, Any], results: Dict[str, Any]):
        """Validate section structure."""
        section_ids = []
        
        for idx, section in enumerate(test.get("sections", []), 1):
            section_id = section.get("section_id", f"Section_{idx}")
            section_ids.append(section_id)
            
            # Check required fields
            required_fields = ["section_id", "section_name", "total_questions", "questions"]
            for field in required_fields:
                if field not in section:
                    results["errors"].append(
                        f"Section '{section_id}': Missing field '{field}'"
                    )
            
            # Check questions
            questions = section.get("questions", [])
            if not isinstance(questions, list):
                results["errors"].append(
                    f"Section '{section_id}': 'questions' must be a list"
                )
        
        # Check for duplicate section IDs
        duplicate_sections = [sid for sid, count in Counter(section_ids).items() if count > 1]
        if duplicate_sections:
            results["errors"].append(
                f"Duplicate section IDs: {', '.join(duplicate_sections)}"
            )
        
        results["info"]["total_sections"] = len(test.get("sections", []))
    
    def _validate_difficulty_distribution(self, test: Dict[str, Any], results: Dict[str, Any]):
        """Validate difficulty distribution."""
        overall_difficulty = {"Easy": 0, "Medium": 0, "Hard": 0, "Unknown": 0}
        section_difficulty = {}
        
        for section in test.get("sections", []):
            section_id = section.get("section_id", "Unknown")
            section_diff = {"Easy": 0, "Medium": 0, "Hard": 0, "Unknown": 0}
            
            for question in section.get("questions", []):
                difficulty = question.get("difficulty", "Unknown")
                
                if difficulty in overall_difficulty:
                    overall_difficulty[difficulty] += 1
                    section_diff[difficulty] += 1
                else:
                    overall_difficulty["Unknown"] += 1
                    section_diff["Unknown"] += 1
                    results["warnings"].append(
                        f"Question {question.get('question_id', 'Unknown')} has invalid difficulty: {difficulty}"
                    )
            
            section_difficulty[section_id] = section_diff
        
        results["info"]["overall_difficulty"] = overall_difficulty
        results["info"]["section_difficulty"] = section_difficulty
        
        # Warn if no difficulty distribution
        if overall_difficulty["Unknown"] > 0:
            results["warnings"].append(
                f"{overall_difficulty['Unknown']} questions have unknown difficulty"
            )
    
    def _validate_topic_distribution(self, test: Dict[str, Any], results: Dict[str, Any]):
        """Validate topic distribution."""
        overall_topics = Counter()
        section_topics = {}
        
        for section in test.get("sections", []):
            section_id = section.get("section_id", "Unknown")
            section_topic_counter = Counter()
            
            for question in section.get("questions", []):
                topic = question.get("topic", "Unknown")
                subtopic = question.get("subtopic", "Unknown")
                
                overall_topics[topic] += 1
                section_topic_counter[topic] += 1
            
            section_topics[section_id] = dict(section_topic_counter)
        
        results["info"]["overall_topics"] = dict(overall_topics)
        results["info"]["section_topics"] = section_topics
    
    def _validate_question_ids(self, test: Dict[str, Any], results: Dict[str, Any]):
        """Validate question IDs."""
        all_question_ids = []
        
        for section in test.get("sections", []):
            for question in section.get("questions", []):
                qid = question.get("question_id")
                
                if not qid:
                    results["warnings"].append(
                        f"Question in section '{section.get('section_id')}' missing question_id"
                    )
                else:
                    all_question_ids.append(qid)
        
        results["info"]["total_question_ids"] = len(all_question_ids)
    
    def _check_duplicates(self, test: Dict[str, Any], results: Dict[str, Any]):
        """Check for duplicate questions."""
        question_ids = []
        
        for section in test.get("sections", []):
            for question in section.get("questions", []):
                qid = question.get("question_id")
                if qid:
                    question_ids.append(qid)
        
        # Find duplicates
        duplicate_ids = [qid for qid, count in Counter(question_ids).items() if count > 1]
        
        if duplicate_ids:
            results["errors"].append(
                f"Found {len(duplicate_ids)} duplicate question IDs: {', '.join(duplicate_ids[:5])}..."
            )
        
        results["info"]["duplicate_questions"] = len(duplicate_ids)
    
    def _print_validation_results(self, results: Dict[str, Any]):
        """Print validation results."""
        print(f"\n{'='*80}")
        
        if results["passed"]:
            print("✅ VALIDATION PASSED")
        else:
            print("❌ VALIDATION FAILED")
        
        print(f"{'='*80}")
        
        # Print info
        print("\n📊 Test Information:")
        print(f"   Test ID: {results['test_id']}")
        print(f"   Test Name: {results['test_name']}")
        print(f"   Total Questions: {results['info'].get('actual_questions', 0)}")
        print(f"   Total Sections: {results['info'].get('total_sections', 0)}")
        
        # Print difficulty distribution
        difficulty = results['info'].get('overall_difficulty', {})
        print(f"\n📈 Difficulty Distribution:")
        print(f"   Easy: {difficulty.get('Easy', 0)}")
        print(f"   Medium: {difficulty.get('Medium', 0)}")
        print(f"   Hard: {difficulty.get('Hard', 0)}")
        
        # Print topic distribution
        topics = results['info'].get('overall_topics', {})
        if topics:
            print(f"\n📚 Topic Distribution:")
            for topic, count in sorted(topics.items(), key=lambda x: x[1], reverse=True):
                print(f"   {topic}: {count}")
        
        # Print errors
        if results["errors"]:
            print(f"\n❌ Errors ({len(results['errors'])}):")
            for error in results["errors"]:
                print(f"   • {error}")
        
        # Print warnings
        if results["warnings"]:
            print(f"\n⚠️  Warnings ({len(results['warnings'])}):")
            for warning in results["warnings"][:10]:  # Limit to first 10
                print(f"   • {warning}")
            if len(results["warnings"]) > 10:
                print(f"   ... and {len(results['warnings']) - 10} more warnings")
    
    def validate_all_tests(self, tests_dir: str = "generated_tests/commercial_series"):
        """
        Validate all tests in directory.
        
        Args:
            tests_dir: Directory containing generated tests
        """
        tests_path = Path(tests_dir)
        test_files = list(tests_path.glob("*_generated.json"))
        
        if not test_files:
            print(f"\n❌ No test files found in {tests_dir}")
            return
        
        print(f"\n{'='*80}")
        print(f"🔍 VALIDATING {len(test_files)} TEST(S)")
        print(f"{'='*80}")
        
        for test_file in test_files:
            self.validate_test_file(str(test_file))
        
        # Print summary
        self._print_summary()
    
    def _print_summary(self):
        """Print validation summary."""
        print(f"\n{'='*80}")
        print("📊 VALIDATION SUMMARY")
        print(f"{'='*80}")
        
        print(f"\nTotal Tests Validated: {self.validation_report['tests_validated']}")
        print(f"✅ Passed: {self.validation_report['tests_passed']}")
        print(f"❌ Failed: {self.validation_report['tests_failed']}")
        
        # List failed tests
        if self.validation_report['tests_failed'] > 0:
            print("\n❌ Failed Tests:")
            for result in self.validation_report['test_results']:
                if not result['passed']:
                    print(f"   • {result['file']}")
                    print(f"     Errors: {len(result['errors'])}")
        
        # Save report
        report_path = Path("generated_tests/commercial_series/validation_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.validation_report, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Validation report saved to: {report_path}")


def main():
    """Main entry point."""
    print("\n" + "=" * 80)
    print("TEST VALIDATION SCRIPT")
    print("=" * 80)
    
    validator = TestValidator()
    validator.validate_all_tests()
    
    print("\n" + "=" * 80)
    print("Validation Complete!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
