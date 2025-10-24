"""
Blueprint Validator Module
Validates blueprint JSON structure and constraints.
"""

import json
from typing import Dict, List, Tuple, Any
from pathlib import Path


class BlueprintValidator:
    """Validates test blueprints before generation."""
    
    REQUIRED_BLUEPRINT_KEYS = [
        "test_id", "test_name", "total_questions", "sections"
    ]
    
    REQUIRED_SECTION_KEYS = [
        "section_id", "section_name", "total_questions", 
        "source_files", "difficulty_distribution", "topic_distribution"
    ]
    
    VALID_DIFFICULTIES = ["Easy", "Medium", "Hard"]
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def validate(self, blueprint_path: str) -> Tuple[bool, List[str], List[str]]:
        """
        Validate blueprint file.
        
        Args:
            blueprint_path: Path to the blueprint JSON file
        
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []
        
        # Check if file exists
        if not Path(blueprint_path).exists():
            self.errors.append(f"❌ Blueprint file not found: {blueprint_path}")
            return False, self.errors, self.warnings
        
        # Load and parse JSON
        try:
            with open(blueprint_path, 'r', encoding='utf-8') as f:
                blueprint = json.load(f)
        except json.JSONDecodeError as e:
            self.errors.append(f"❌ Invalid JSON in blueprint: {e}")
            return False, self.errors, self.warnings
        except Exception as e:
            self.errors.append(f"❌ Error reading blueprint file: {e}")
            return False, self.errors, self.warnings
        
        # Validate top-level structure
        self._validate_top_level(blueprint)
        
        # Validate sections
        if "sections" in blueprint:
            self._validate_sections(blueprint)
        
        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings
    
    def _validate_top_level(self, blueprint: Dict[str, Any]) -> None:
        """Validate top-level blueprint structure."""
        
        # Check required keys
        for key in self.REQUIRED_BLUEPRINT_KEYS:
            if key not in blueprint:
                self.errors.append(f"❌ Missing required key in blueprint: '{key}'")
        
        # Validate test_id format
        if "test_id" in blueprint:
            test_id = blueprint["test_id"]
            if not isinstance(test_id, str) or not test_id.strip():
                self.errors.append(f"❌ Invalid test_id: must be a non-empty string")
        
        # Validate total_questions
        if "total_questions" in blueprint:
            total_q = blueprint["total_questions"]
            if not isinstance(total_q, int) or total_q <= 0:
                self.errors.append(f"❌ Invalid total_questions: must be a positive integer")
        
        # Validate sections is a list
        if "sections" in blueprint:
            if not isinstance(blueprint["sections"], list):
                self.errors.append(f"❌ 'sections' must be a list")
            elif len(blueprint["sections"]) == 0:
                self.errors.append(f"❌ 'sections' cannot be empty")
    
    def _validate_sections(self, blueprint: Dict[str, Any]) -> None:
        """Validate all sections in the blueprint."""
        
        sections = blueprint.get("sections", [])
        total_questions_blueprint = blueprint.get("total_questions", 0)
        total_questions_sections = 0
        section_ids = set()
        
        for idx, section in enumerate(sections):
            section_num = idx + 1
            
            # Validate section structure
            self._validate_section_structure(section, section_num)
            
            # Check for duplicate section IDs
            if "section_id" in section:
                sid = section["section_id"]
                if sid in section_ids:
                    self.errors.append(
                        f"❌ Duplicate section_id found: '{sid}'"
                    )
                section_ids.add(sid)
            
            # Validate section content
            if all(key in section for key in self.REQUIRED_SECTION_KEYS):
                self._validate_section_content(section, section_num)
                total_questions_sections += section.get("total_questions", 0)
        
        # Validate total questions match across blueprint and sections
        if total_questions_blueprint > 0 and total_questions_sections > 0:
            if total_questions_blueprint != total_questions_sections:
                self.errors.append(
                    f"❌ Total questions mismatch: "
                    f"Blueprint says {total_questions_blueprint}, "
                    f"but sections sum to {total_questions_sections}"
                )
    
    def _validate_section_structure(self, section: Dict[str, Any], section_num: int) -> None:
        """Validate section has required keys."""
        
        for key in self.REQUIRED_SECTION_KEYS:
            if key not in section:
                self.errors.append(
                    f"❌ Section {section_num}: Missing required key '{key}'"
                )
    
    def _validate_section_content(self, section: Dict[str, Any], section_num: int) -> None:
        """Validate section content and constraints."""
        
        section_id = section.get("section_id", f"Section_{section_num}")
        total_questions = section.get("total_questions", 0)
        
        # Validate total_questions
        if not isinstance(total_questions, int) or total_questions <= 0:
            self.errors.append(
                f"❌ {section_id}: total_questions must be a positive integer"
            )
            return  # Can't continue validation without valid total
        
        # Validate source_files
        self._validate_source_files(section, section_id)
        
        # Validate difficulty_distribution
        self._validate_difficulty_distribution(section, section_id, total_questions)
        
        # Validate topic_distribution
        self._validate_topic_distribution(section, section_id, total_questions)
    
    def _validate_source_files(self, section: Dict[str, Any], section_id: str) -> None:
        """Validate source_files field."""
        
        source_files = section.get("source_files", [])
        
        if not isinstance(source_files, list):
            self.errors.append(
                f"❌ {section_id}: source_files must be a list"
            )
            return
        
        if len(source_files) == 0:
            self.errors.append(
                f"❌ {section_id}: source_files cannot be empty"
            )
            return
        
        for sf in source_files:
            if not isinstance(sf, str) or not sf.strip():
                self.errors.append(
                    f"❌ {section_id}: Invalid source file name in source_files"
                )
    
    def _validate_difficulty_distribution(
        self, 
        section: Dict[str, Any], 
        section_id: str, 
        total_questions: int
    ) -> None:
        """Validate difficulty_distribution field."""
        
        diff_dist = section.get("difficulty_distribution", {})
        
        if not isinstance(diff_dist, dict):
            self.errors.append(
                f"❌ {section_id}: difficulty_distribution must be a dictionary"
            )
            return
        
        # Check all difficulties are valid
        for difficulty in diff_dist.keys():
            if difficulty not in self.VALID_DIFFICULTIES:
                self.errors.append(
                    f"❌ {section_id}: Invalid difficulty level '{difficulty}'. "
                    f"Must be one of: {', '.join(self.VALID_DIFFICULTIES)}"
                )
        
        # Check all values are positive integers
        total_diff_questions = 0
        for difficulty, count in diff_dist.items():
            if not isinstance(count, int) or count < 0:
                self.errors.append(
                    f"❌ {section_id}: difficulty_distribution['{difficulty}'] "
                    f"must be a non-negative integer"
                )
            else:
                total_diff_questions += count
        
        # Check sum matches total_questions
        if total_diff_questions != total_questions:
            self.errors.append(
                f"❌ {section_id}: difficulty_distribution sum ({total_diff_questions}) "
                f"doesn't match total_questions ({total_questions})"
            )
        
        # Warn if any difficulty is missing
        for difficulty in self.VALID_DIFFICULTIES:
            if difficulty not in diff_dist:
                self.warnings.append(
                    f"⚠️  {section_id}: Missing difficulty level '{difficulty}' "
                    f"in difficulty_distribution (assuming 0)"
                )
    
    def _validate_topic_distribution(
        self, 
        section: Dict[str, Any], 
        section_id: str, 
        total_questions: int
    ) -> None:
        """Validate topic_distribution field."""
        
        topic_dist = section.get("topic_distribution", {})
        
        if not isinstance(topic_dist, dict):
            self.errors.append(
                f"❌ {section_id}: topic_distribution must be a dictionary"
            )
            return
        
        if len(topic_dist) == 0:
            self.errors.append(
                f"❌ {section_id}: topic_distribution cannot be empty"
            )
            return
        
        # Check all topics have valid counts
        total_topic_questions = 0
        for topic, count in topic_dist.items():
            if not isinstance(topic, str) or not topic.strip():
                self.errors.append(
                    f"❌ {section_id}: Invalid topic name in topic_distribution"
                )
            
            if not isinstance(count, int) or count <= 0:
                self.errors.append(
                    f"❌ {section_id}: topic_distribution['{topic}'] "
                    f"must be a positive integer"
                )
            else:
                total_topic_questions += count
        
        # Special handling for Data Interpretation (DI sets)
        # If section has DI, need to account for 5 questions per set
        source_files = section.get("source_files", [])
        has_di = any("di_master" in sf.lower() for sf in source_files)
        
        if has_di and "Data Interpretation" in topic_dist:
            di_sets = topic_dist["Data Interpretation"]
            di_questions = di_sets * 5
            
            # Adjust total for DI sets
            non_di_total = sum(
                count for topic, count in topic_dist.items() 
                if topic != "Data Interpretation"
            )
            expected_total = non_di_total + di_questions
            
            if expected_total != total_questions:
                self.errors.append(
                    f"❌ {section_id}: topic_distribution sum error. "
                    f"Data Interpretation: {di_sets} sets × 5 = {di_questions} questions. "
                    f"Other topics: {non_di_total} questions. "
                    f"Total: {expected_total} (expected {total_questions})"
                )
        else:
            # Regular validation: sum must equal total_questions
            if total_topic_questions != total_questions:
                self.errors.append(
                    f"❌ {section_id}: topic_distribution sum ({total_topic_questions}) "
                    f"doesn't match total_questions ({total_questions})"
                )


def validate_blueprint(blueprint_path: str) -> Tuple[bool, List[str], List[str]]:
    """
    Convenience function to validate a blueprint.
    
    Args:
        blueprint_path: Path to blueprint JSON file
    
    Returns:
        Tuple of (is_valid, errors, warnings)
    """
    validator = BlueprintValidator()
    return validator.validate(blueprint_path)


# For testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python blueprint_validator.py <blueprint_file.json>")
        sys.exit(1)
    
    blueprint_file = sys.argv[1]
    
    print(f"\n🔍 Validating blueprint: {blueprint_file}")
    print("=" * 80)
    
    is_valid, errors, warnings = validate_blueprint(blueprint_file)
    
    if warnings:
        print("\n⚠️  WARNINGS:")
        for warning in warnings:
            print(f"  {warning}")
    
    if errors:
        print("\n❌ ERRORS:")
        for error in errors:
            print(f"  {error}")
        print("\n❌ Validation FAILED\n")
        sys.exit(1)
    else:
        print("\n✅ Validation PASSED")
        print(f"✅ Blueprint is valid and ready for test generation\n")
        sys.exit(0)
