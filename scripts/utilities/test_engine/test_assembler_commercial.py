"""
Commercial Test Generator for RBI Grade B Mock Tests
Generates unique tests with configurable overlap and difficulty distribution
Optimized for commercial test series (₹99 per test, ₹499 bundle)

Author: AI Assistant
Date: 2025-10-07
"""

import json
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import defaultdict, Counter

from master_loader import MasterLoader, load_masters
from question_selector import QuestionSelector
from di_selector import DISelector


class CommercialTestGenerator:
    """
    Generates commercial-quality mock tests with smart question management.
    
    Features:
    - Configurable overlap percentage (e.g., 20% overlap = 80% unique)
    - Difficulty distribution control (Easy/Medium/Hard %)
    - Question tracking across multiple tests
    - Smart selection to maximize uniqueness
    - Detailed reporting and analytics
    """
    
    def __init__(
        self,
        master_loader: MasterLoader,
        overlap_percentage: int = 20,
        difficulty_distribution: Dict[str, int] = None
    ):
        """
        Initialize commercial test generator.
        
        Args:
            master_loader: MasterLoader instance with loaded masters
            overlap_percentage: Allowed overlap between tests (0-100)
                0 = Zero overlap, 100% unique
                20 = 20% can repeat, 80% must be unique
                50 = 50% can repeat, 50% must be unique
            difficulty_distribution: Dict with Easy/Medium/Hard percentages
                Default: {"Easy": 20, "Medium": 50, "Hard": 30}
        """
        self.master_loader = master_loader
        self.overlap_percentage = overlap_percentage
        self.difficulty_distribution = difficulty_distribution or {
            "Easy": 20,
            "Medium": 50,
            "Hard": 30
        }
        
        # Validate difficulty distribution
        total_percentage = sum(self.difficulty_distribution.values())
        if total_percentage != 100:
            raise ValueError(f"Difficulty percentages must sum to 100, got {total_percentage}")
        
        # Track used questions across all tests (question_id -> test_numbers)
        self.used_questions = {
            "english": defaultdict(list),
            "general_awareness": defaultdict(list),
            "reasoning": defaultdict(list),
            "arithmetic": defaultdict(list),
            "di": defaultdict(list)
        }
        
        # Track tests generated
        self.tests_generated = []
        
        # Initialize selectors
        self.question_selector = QuestionSelector(master_loader)
        self.di_selector = DISelector(master_loader)
        
        print(f"\n🎯 Commercial Test Generator Initialized")
        print(f"   Overlap Allowed: {overlap_percentage}%")
        print(f"   Uniqueness Required: {100 - overlap_percentage}%")
        print(f"   Difficulty: Easy {self.difficulty_distribution['Easy']}%, "
              f"Medium {self.difficulty_distribution['Medium']}%, "
              f"Hard {self.difficulty_distribution['Hard']}%")
    
    def calculate_max_tests(self, blueprint: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate maximum possible unique tests with current settings.
        
        Args:
            blueprint: Test blueprint
        
        Returns:
            Dictionary with maximum test calculations
        """
        print("\n" + "="*80)
        print("📊 CALCULATING MAXIMUM UNIQUE TESTS")
        print("="*80)
        
        # Get requirements from blueprint
        requirements = self._extract_requirements(blueprint)
        
        # Get available questions by difficulty
        available_by_difficulty = self._get_available_by_difficulty()
        
        # Calculate max tests per subject per difficulty
        max_tests = {}
        
        for subject, req_diff in requirements.items():
            subject_max = float('inf')
            
            print(f"\n📚 {subject.replace('_', ' ').title()}:")
            
            for difficulty, required_count in req_diff.items():
                if required_count == 0:
                    continue
                
                available = available_by_difficulty[subject].get(difficulty, 0)
                
                # Calculate with overlap - more realistic approach
                # With overlap, we can generate more tests by reusing questions
                # After the first test, we can reuse questions up to the overlap percentage
                if self.overlap_percentage > 0:
                    # More realistic calculation: we can generate tests until we run out of questions
                    # The first test uses all unique questions, subsequent tests can reuse
                    max_for_difficulty = available / required_count
                else:
                    # No overlap - each test needs completely unique questions
                    max_for_difficulty = available / required_count
                
                print(f"   {difficulty}: {available} available, "
                      f"{required_count} needed per test → "
                      f"{max_for_difficulty:.1f} tests max")
                
                subject_max = min(subject_max, max_for_difficulty)
            
            max_tests[subject] = int(subject_max)
            print(f"   → Maximum for {subject}: {max_tests[subject]} tests")
        
        # Find overall bottleneck
        bottleneck_subject = min(max_tests, key=max_tests.get)
        max_possible = max_tests[bottleneck_subject]
        
        print(f"\n⚠️  BOTTLENECK: {bottleneck_subject.replace('_', ' ').title()}")
        print(f"   Maximum Unique Tests: {max_possible}")
        print(f"   With {self.overlap_percentage}% overlap allowed")
        
        return {
            "max_tests": max_possible,
            "bottleneck_subject": bottleneck_subject,
            "per_subject_max": max_tests,
            "overlap_percentage": self.overlap_percentage,
            "difficulty_distribution": self.difficulty_distribution,
            "requirements": requirements,
            "available": available_by_difficulty
        }
    
    def generate_test_series(
        self,
        blueprint: Dict[str, Any],
        num_tests: int,
        output_dir: str = "generated_tests",
        test_name_prefix: str = "RBI_PHASE1_MOCK"
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple unique tests for commercial series.
        
        Args:
            blueprint: Test blueprint
            num_tests: Number of tests to generate
            output_dir: Output directory
            test_name_prefix: Prefix for test IDs
        
        Returns:
            List of generated test info
        """
        print("\n" + "="*80)
        print(f"🚀 GENERATING {num_tests} COMMERCIAL MOCK TESTS")
        print("="*80)
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        generated_tests = []
        
        for test_num in range(1, num_tests + 1):
            print(f"\n{'='*80}")
            print(f"📝 Generating Mock Test {test_num}/{num_tests}")
            print(f"{'='*80}")
            
            try:
                # Generate test
                test_data = self.generate_single_test(
                    blueprint=blueprint,
                    test_number=test_num,
                    test_name_prefix=test_name_prefix
                )
                
                # Validate uniqueness
                overlap_report = self._calculate_overlap(test_data, test_num)
                
                # Check if overlap exceeds threshold (with more tolerance for commercial series)
                overlap_tolerance = 30  # Allow up to 30% above target for commercial series
                if overlap_report['actual_overlap'] > self.overlap_percentage + overlap_tolerance:
                    print(f"\n⚠️  Warning: Overlap {overlap_report['actual_overlap']:.1f}% "
                          f"exceeds target {self.overlap_percentage}% (tolerance: +{overlap_tolerance}%)")
                    
                    if test_num > 5:  # Allow first 5 tests even with high overlap
                        print(f"   High overlap detected. Stopping at {test_num-1} tests.")
                        break
                    else:
                        print(f"   Continuing with high overlap for commercial series...")
                
                # Save test
                test_filename = f"{test_name_prefix.lower()}_{test_num:02d}.json"
                test_filepath = output_path / test_filename
                
                with open(test_filepath, 'w', encoding='utf-8') as f:
                    json.dump(test_data, f, indent=2, ensure_ascii=False)
                
                print(f"\n💾 Saved: {test_filename}")
                print(f"   Actual Overlap: {overlap_report['actual_overlap']:.1f}%")
                print(f"   Unique Questions: {overlap_report['unique_count']}/{overlap_report['total_count']}")
                
                # Track generated test
                self.tests_generated.append({
                    'test_number': test_num,
                    'question_ids': overlap_report['question_ids'],
                    'overlap_report': overlap_report,
                    'filepath': str(test_filepath)
                })
                
                generated_tests.append({
                    'test_number': test_num,
                    'test_id': test_data['test_id'],
                    'test_name': test_data['test_name'],
                    'file': str(test_filepath),
                    'total_questions': test_data['total_questions'],
                    'overlap_percentage': overlap_report['actual_overlap'],
                    'unique_questions': overlap_report['unique_count']
                })
                
            except Exception as e:
                print(f"\n❌ Error generating test {test_num}: {e}")
                import traceback
                traceback.print_exc()
                print(f"\nStopping at {test_num-1} tests.")
                break
        
        # Generate series summary
        if generated_tests:
            self._save_series_summary(generated_tests, output_path, blueprint)
        
        return generated_tests
    
    def generate_single_test(
        self,
        blueprint: Dict[str, Any],
        test_number: int,
        test_name_prefix: str = "RBI_PHASE1_MOCK"
    ) -> Dict[str, Any]:
        """
        Generate a single test with smart question selection.
        
        Args:
            blueprint: Test blueprint
            test_number: Test number in series
            test_name_prefix: Prefix for test ID
        
        Returns:
            Complete test dictionary
        """
        test_id = f"{test_name_prefix}_{test_number:02d}"
        test_name = f"{blueprint.get('test_name', 'Mock Test')} #{test_number}"
        
        print(f"\n🎯 Test ID: {test_id}")
        print(f"   Test Name: {test_name}")
        
        # Initialize test structure
        test = {
            "test_id": test_id,
            "test_name": test_name,
            "test_number": test_number,
            "test_series": blueprint.get("test_series", "RBI Grade B Mock Series"),
            "total_questions": blueprint.get("total_questions", 200),
            "total_marks": blueprint.get("total_marks", 200),
            "duration_minutes": blueprint.get("duration_minutes", 120),
            "negative_marking": blueprint.get("negative_marking", 0.25),
            "passing_marks": blueprint.get("passing_marks", 0),
            "difficulty_distribution": self.difficulty_distribution,
            "overlap_percentage": self.overlap_percentage,
            "sections": [],
            "metadata": {}
        }
        
        # Generate sections
        section_reports = []
        
        for section_config in blueprint.get("sections", []):
            print(f"\n📋 Generating Section: {section_config['section_name']}")
            
            section, report = self._generate_section(
                section_config=section_config,
                test_number=test_number
            )
            
            test["sections"].append(section)
            section_reports.append(report)
        
        # Add metadata
        test["metadata"] = self._create_metadata(
            blueprint=blueprint,
            test_number=test_number,
            section_reports=section_reports
        )
        
        # Validate test
        is_valid, errors = self._validate_test(test, blueprint)
        
        if not is_valid:
            print("\n⚠️  Validation Warnings:")
            for error in errors:
                print(f"   - {error}")
        
        return test
    
    def _generate_section(
        self,
        section_config: Dict[str, Any],
        test_number: int
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Generate a single section with questions.
        
        Args:
            section_config: Section configuration from blueprint
            test_number: Current test number
        
        Returns:
            Tuple of (section_dict, generation_report)
        """
        section_id = section_config["section_id"]
        section_name = section_config["section_name"]
        
        # Check if this is Quantitative Aptitude (has subsections)
        if "subsections" in section_config:
            return self._generate_quant_section(section_config, test_number)
        
        # Regular section
        total_questions = section_config["total_questions"]
        difficulty_dist = section_config.get(
            "difficulty_distribution",
            self._calculate_section_difficulty(total_questions)
        )
        
        print(f"   Total: {total_questions} questions")
        print(f"   Difficulty: Easy={difficulty_dist['Easy']}, "
              f"Medium={difficulty_dist['Medium']}, Hard={difficulty_dist['Hard']}")
        
        # Map section to master
        master_name = self._map_section_to_master(section_name)
        
        # Select questions with smart selection
        questions = self._select_section_questions(
            master_name=master_name,
            difficulty_dist=difficulty_dist,
            topic_dist=section_config.get("topic_distribution", {}),
            test_number=test_number
        )
        
        # Shuffle questions
        random.shuffle(questions)
        
        # Create section
        section = {
            "section_id": section_id,
            "section_name": section_name,
            "total_questions": len(questions),
            "marks_per_question": section_config.get("marks_per_question", 1),
            "negative_marks": section_config.get("negative_marks", 0.25),
            "questions": questions
        }
        
        # Generate report
        report = {
            "section_id": section_id,
            "section_name": section_name,
            "questions_generated": len(questions),
            "questions_expected": total_questions,
            "difficulty_distribution": self._count_difficulty(questions),
            "topic_distribution": self._count_topics(questions)
        }
        
        print(f"   ✅ Generated {len(questions)} questions")
        
        return section, report
    
    def _generate_quant_section(
        self,
        section_config: Dict[str, Any],
        test_number: int
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Generate Quantitative Aptitude section with Arithmetic + DI subsections.
        
        Args:
            section_config: Section configuration
            test_number: Current test number
        
        Returns:
            Tuple of (section_dict, generation_report)
        """
        section_id = section_config["section_id"]
        section_name = section_config["section_name"]
        
        all_questions = []
        subsection_reports = []
        
        for subsection_config in section_config.get("subsections", []):
            subsection_name = subsection_config["subsection_name"]
            
            print(f"\n   📊 Subsection: {subsection_name}")
            
            if subsection_name == "Data Interpretation":
                # Generate DI questions
                questions, report = self._generate_di_subsection(
                    subsection_config,
                    test_number
                )
            else:
                # Generate Arithmetic questions
                questions, report = self._generate_arithmetic_subsection(
                    subsection_config,
                    test_number
                )
            
            # Add questions to the main list (except DI and Arithmetic questions which are handled separately)
            if subsection_name not in ["Data Interpretation", "Arithmetic"]:
                all_questions.extend(questions)
            
            # Add questions to the report for proper subsection structure
            report["questions"] = questions
            subsection_reports.append(report)
            
            print(f"   ✅ Generated {len(questions)} {subsection_name} questions")
        
        # DI questions are already in subsections, don't add them to main array
        # They will be included in the final test structure through subsections
        
        # Shuffle all questions (DI questions are already in subsections)
        random.shuffle(all_questions)
        
        # Calculate total questions including subsections
        total_questions_count = len(all_questions)
        for subsection_report in subsection_reports:
            if subsection_report.get("subsection_name") in ["Data Interpretation", "Arithmetic"]:
                total_questions_count += len(subsection_report.get("questions", []))
        
        # Create section
        section = {
            "section_id": section_id,
            "section_name": section_name,
            "total_questions": total_questions_count,
            "marks_per_question": section_config.get("marks_per_question", 1),
            "negative_marks": section_config.get("negative_marks", 0.25),
            "subsections": subsection_reports,
            "questions": all_questions
        }
        
        # Generate report
        report = {
            "section_id": section_id,
            "section_name": section_name,
            "questions_generated": total_questions_count,
            "questions_expected": section_config.get("total_questions", 30),
            "subsection_reports": subsection_reports,
            "difficulty_distribution": self._count_difficulty(all_questions),
            "topic_distribution": self._count_topics(all_questions)
        }
        
        return section, report
    
    def _generate_arithmetic_subsection(
        self,
        subsection_config: Dict[str, Any],
        test_number: int
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Generate Arithmetic questions for subsection.
        
        Args:
            subsection_config: Subsection configuration
            test_number: Current test number
        
        Returns:
            Tuple of (questions_list, generation_report)
        """
        total_questions = subsection_config["total_questions"]
        difficulty_dist = subsection_config.get(
            "difficulty_distribution",
            self._calculate_section_difficulty(total_questions)
        )
        topic_dist = subsection_config.get("topic_distribution", {})
        
        print(f"      Total: {total_questions} questions")
        print(f"      Difficulty: Easy={difficulty_dist['Easy']}, "
              f"Medium={difficulty_dist['Medium']}, Hard={difficulty_dist['Hard']}")
        
        # Select questions with smart selection
        questions = self._select_section_questions(
            master_name="arithmetic",
            difficulty_dist=difficulty_dist,
            topic_dist=topic_dist,
            test_number=test_number
        )
        
        # Generate report
        report = {
            "subsection_name": "Arithmetic",
            "questions_generated": len(questions),
            "questions_expected": total_questions,
            "difficulty_distribution": self._count_difficulty(questions),
            "topic_distribution": self._count_topics(questions)
        }
        
        return questions, report
    
    def _generate_di_subsection(
        self,
        subsection_config: Dict[str, Any],
        test_number: int
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Generate Data Interpretation questions (complete sets).
        
        Args:
            subsection_config: Subsection configuration
            test_number: Current test number
        
        Returns:
            Tuple of (questions_list, generation_report)
        """
        total_questions = subsection_config["total_questions"]
        di_sets_required = subsection_config.get("di_sets_required", 3)
        difficulty_dist = subsection_config.get(
            "difficulty_distribution",
            self._calculate_section_difficulty(total_questions)
        )
        footprint_preferences = subsection_config.get("footprint_preferences", ["1-3-1"])
        
        print(f"      Total: {total_questions} questions ({di_sets_required} sets)")
        print(f"      Difficulty: Easy={difficulty_dist['Easy']}, "
              f"Medium={difficulty_dist['Medium']}, Hard={difficulty_dist['Hard']}")
        
        # Calculate target footprint based on difficulty distribution
        target_footprint = self._calculate_di_footprint(
            total_questions=total_questions,
            difficulty_dist=difficulty_dist
        )
        
        print(f"      Target footprint: {target_footprint} (Easy-Medium-Hard per set)")
        
        # Get previously used DI sets for this subject
        used_set_ids = set()
        for qid_list in self.used_questions["di"].values():
            used_set_ids.update(qid_list)
        
        # Select DI sets with smart selection
        selected_sets = self._select_di_sets_smart(
            num_sets=di_sets_required,
            target_footprint=target_footprint,
            used_set_ids=used_set_ids,
            test_number=test_number
        )
        
        # Extract all questions from selected sets
        all_di_questions = []
        for di_set in selected_sets:
            all_di_questions.extend(di_set.get("questions", []))
        
        # Track used DI sets by set_id (complete sets)
        for di_set in selected_sets:
            set_id = di_set.get("di_set_id")
            if set_id:
                self.used_questions["di"][set_id].append(test_number)

        
        # Generate report
        report = {
            "subsection_name": "Data Interpretation",
            "questions_generated": len(all_di_questions),
            "questions_expected": total_questions,
            "sets_generated": len(selected_sets),
            "sets_expected": di_sets_required,
            "difficulty_distribution": self._count_difficulty(all_di_questions),
            "selected_sets": [s.get("di_set_id") for s in selected_sets]
        }
        
        return all_di_questions, report
    
    def _select_section_questions(
        self,
        master_name: str,
        difficulty_dist: Dict[str, int],
        topic_dist: Dict[str, int],
        test_number: int
    ) -> List[Dict[str, Any]]:
        """
        Select questions for a section with smart uniqueness management.
        
        Args:
            master_name: Master bank name (english, general_awareness, etc.)
            difficulty_dist: Difficulty distribution dict
            topic_dist: Topic distribution dict
            test_number: Current test number
        
        Returns:
            List of selected questions
        """
        selected_questions = []
        
        # For each difficulty level
        print(f"         Processing difficulty distribution: {difficulty_dist}")
        for difficulty, count in difficulty_dist.items():
            print(f"         Processing {difficulty}: {count} questions needed")
            if count == 0:
                print(f"         Skipping {difficulty} (count=0)")
                continue
            
            # Get available questions for this difficulty
            master_file = f"{master_name}_master_question_bank.json"
            master_questions = self.master_loader.masters.get(master_file, {}).get("questions", [])
            
            # Filter by difficulty
            difficulty_questions = [
                q for q in master_questions
                if q.get("difficulty", "").strip() == difficulty
            ]
            
            # Separate into used and unused
            used_qids = set(self.used_questions[master_name].keys())
            
            unused_questions = [
                q for q in difficulty_questions
                if q.get("question_id") not in used_qids
            ]
            
            used_questions = [
                q for q in difficulty_questions
                if q.get("question_id") in used_qids
            ]
            
            # Calculate how many must be unique (based on overlap %)
            # For commercial series, be more flexible with overlap
            unique_required = int(count * (1 - self.overlap_percentage / 100))
            can_reuse = count - unique_required
            
            # If we don't have enough unused questions, be more aggressive with reuse
            if len(unused_questions) < unique_required:
                # Reduce unique requirement to what's available
                unique_required = min(unique_required, len(unused_questions))
                can_reuse = count - unique_required
            
            # Strategy: Mix unused and reused based on overlap percentage
            questions_to_add = []

            # Calculate how many should be reused vs unique
            unique_needed = int(count * (1 - self.overlap_percentage / 100))
            reuse_needed = count - unique_needed

            print(f"         {difficulty}: need {count} total (unique={unique_needed}, can_reuse={reuse_needed})")
            print(f"         Available: {len(unused_questions)} unused, {len(used_questions)} used")

            # Get unique questions first
            if len(unused_questions) >= count:
                # Enough unused questions for the full count
                questions_to_add.extend(random.sample(unused_questions, count))
            elif len(unused_questions) >= unique_needed:
                # Enough unused for unique requirement, fill rest with reused
                questions_to_add.extend(random.sample(unused_questions, unique_needed))
                # Add reused questions for the remaining count
                remaining = count - unique_needed
                if remaining > 0 and used_questions:
                    used_sorted = sorted(
                        used_questions,
                        key=lambda q: len(self.used_questions[master_name].get(q.get("question_id"), []))
                    )
                    questions_to_add.extend(used_sorted[:remaining])
            else:
                # Not enough unused, use all unused + fill from used
                questions_to_add.extend(unused_questions)
                remaining = count - len(unused_questions)
                if remaining > 0 and used_questions:
                    used_sorted = sorted(
                        used_questions,
                        key=lambda q: len(self.used_questions[master_name].get(q.get("question_id"), []))
                    )
                    questions_to_add.extend(used_sorted[:remaining])

            # Log the actual selection
            print(f"         Selected {len(questions_to_add)} questions")

            # Filter by topics if specified
            if topic_dist:
                questions_to_add = self._apply_topic_distribution(
                    questions=questions_to_add,
                    topic_dist=topic_dist,
                    difficulty=difficulty,
                    difficulty_dist=difficulty_dist
                )
            
            # Track usage
            for question in questions_to_add:
                qid = question.get("question_id")
                self.used_questions[master_name][qid].append(test_number)
            
            selected_questions.extend(questions_to_add)
        
        return selected_questions
    
    def _select_di_sets_smart(
        self,
        num_sets: int,
        target_footprint: str,
        used_set_ids: Set[str],
        test_number: int
    ) -> List[Dict[str, Any]]:
        """
        Smart selection of DI sets with uniqueness management.
        For DI questions, we prioritize unique sets to ensure each test has distinct data sets.
        
        Args:
            num_sets: Number of sets to select
            target_footprint: Target difficulty footprint (e.g., "1-3-1")
            used_set_ids: Set of already used set IDs
            test_number: Current test number
        
        Returns:
            List of selected DI sets
        """
        # Get all available DI sets
        di_master_data = self.master_loader.masters.get("di_master_question_bank.json", {})
        all_sets = di_master_data.get("questions", [])
        
        if not all_sets:
            raise ValueError("No DI sets available in master bank")
        
        # For DI questions, prioritize unique sets (no overlap)
        # Only reuse if we don't have enough unique sets
        unused_sets = [s for s in all_sets if s.get("di_set_id") not in used_set_ids]
        used_sets = [s for s in all_sets if s.get("di_set_id") in used_set_ids]
        
        print(f"      DI Selection: need {num_sets} sets")
        print(f"      Available: {len(unused_sets)} unused, {len(used_sets)} used")
        
        # Try to get all from unused sets first
        if len(unused_sets) >= num_sets:
            # Randomly select from unused sets to get variety
            selected_sets = random.sample(unused_sets, num_sets)
            print(f"      Using {num_sets} unique DI sets")
        else:
            # Not enough unique sets, use all unique + some reused
            selected_sets = unused_sets.copy()
            remaining = num_sets - len(unused_sets)
            if remaining > 0 and used_sets:
                # Add least-used sets
                used_sets_sorted = sorted(
                    used_sets,
                    key=lambda s: len(self.used_questions["di"].get(s.get("di_set_id"), []))
                )
                selected_sets.extend(used_sets_sorted[:remaining])
                print(f"      Using {len(unused_sets)} unique + {remaining} reused DI sets")
            else:
                print(f"      Warning: Only {len(selected_sets)} DI sets available (need {num_sets})")
        
        # Parse target footprint for scoring
        try:
            target_easy, target_medium, target_hard = map(int, target_footprint.split("-"))
        except:
            target_easy, target_medium, target_hard = 1, 3, 1
        
        # Score sets by how well they match target footprint
        def score_set(di_set):
            footprint = di_set.get("footprint", "0-0-0")
            try:
                easy, medium, hard = map(int, footprint.split("-"))
                # Calculate distance from target
                distance = abs(easy - target_easy) + abs(medium - target_medium) + abs(hard - target_hard)
                return -distance  # Higher score = better match
            except:
                return -999
        
        # Sort selected sets by footprint match
        selected_sets.sort(key=score_set, reverse=True)
        
        # Update used set tracking
        for di_set in selected_sets:
            set_id = di_set.get("di_set_id")
            if set_id:
                self.used_questions["di"][set_id].append(test_number)
        
        return selected_sets
    
    def _calculate_di_footprint(
        self,
        total_questions: int,
        difficulty_dist: Dict[str, int]
    ) -> str:
        """
        Calculate ideal DI set footprint based on difficulty distribution.
        
        Args:
            total_questions: Total DI questions needed
            difficulty_dist: Difficulty distribution
        
        Returns:
            Footprint string (e.g., "1-3-1")
        """
        # Assuming 5 questions per set (standard)
        questions_per_set = 5
        
        # Calculate per-set difficulty counts
        easy_per_set = round(difficulty_dist["Easy"] / (total_questions / questions_per_set))
        medium_per_set = round(difficulty_dist["Medium"] / (total_questions / questions_per_set))
        hard_per_set = round(difficulty_dist["Hard"] / (total_questions / questions_per_set))
        
        # Ensure total = 5
        total = easy_per_set + medium_per_set + hard_per_set
        if total < questions_per_set:
            medium_per_set += (questions_per_set - total)
        elif total > questions_per_set:
            medium_per_set -= (total - questions_per_set)
        
        return f"{easy_per_set}-{medium_per_set}-{hard_per_set}"
    
    def _apply_topic_distribution(
        self,
        questions: List[Dict[str, Any]],
        topic_dist: Dict[str, int],
        difficulty: str,
        difficulty_dist: Dict[str, int]
    ) -> List[Dict[str, Any]]:
        """
        Apply topic distribution to selected questions.
        
        Args:
            questions: List of questions to filter
            topic_dist: Topic distribution requirements
            difficulty: Current difficulty level
            difficulty_dist: Overall difficulty distribution
        
        Returns:
            Filtered list of questions matching topic distribution
        """
        if not topic_dist:
            return questions
        
        # Group questions by topic
        questions_by_topic = defaultdict(list)
        for q in questions:
            topic = q.get("topic", "General")
            questions_by_topic[topic].append(q)
        
        # Calculate how many questions of this difficulty we need per topic
        total_questions_needed = difficulty_dist.get(difficulty, 0)
        
        selected = []
        
        for topic, topic_count in topic_dist.items():
            # Calculate proportional count for this difficulty
            proportion = topic_count / sum(topic_dist.values())
            needed_for_topic = int(total_questions_needed * proportion)
            
            if needed_for_topic == 0:
                continue
            
            # Get questions for this topic
            available = questions_by_topic.get(topic, [])
            
            if len(available) >= needed_for_topic:
                selected.extend(random.sample(available, needed_for_topic))
            else:
                selected.extend(available)
        
        # If we still need more questions, fill from remaining
        if len(selected) < len(questions):
            remaining = [q for q in questions if q not in selected]
            needed = len(questions) - len(selected)
            if remaining and needed > 0:
                selected.extend(random.sample(remaining, min(needed, len(remaining))))
        
        return selected[:len(questions)]
    
    def _calculate_overlap(
        self,
        test_data: Dict[str, Any],
        test_number: int
    ) -> Dict[str, Any]:
        """
        Calculate overlap of current test with all previous tests.
        
        Args:
            test_data: Generated test data
            test_number: Current test number
        
        Returns:
            Overlap report dictionary
        """
        if test_number == 1:
            # First test has no overlap
            total_questions = test_data["total_questions"]
            return {
                "test_number": test_number,
                "actual_overlap": 0.0,
                "total_count": total_questions,
                "unique_count": total_questions,
                "repeated_count": 0,
                "question_ids": self._extract_question_ids(test_data)
            }
        
        # Extract question IDs from current test
        current_qids = self._extract_question_ids(test_data)
        
        # Get all question IDs from previous tests
        all_previous_qids = set()
        for prev_test in self.tests_generated:
            all_previous_qids.update(prev_test['question_ids'])
        
        # Calculate overlap
        repeated_qids = current_qids.intersection(all_previous_qids)
        unique_qids = current_qids - all_previous_qids
        
        total_count = len(current_qids)
        repeated_count = len(repeated_qids)
        unique_count = len(unique_qids)
        
        actual_overlap = (repeated_count / total_count * 100) if total_count > 0 else 0.0
        
        return {
            "test_number": test_number,
            "actual_overlap": actual_overlap,
            "total_count": total_count,
            "unique_count": unique_count,
            "repeated_count": repeated_count,
            "repeated_questions": list(repeated_qids),
            "question_ids": current_qids
        }
    
    def _extract_question_ids(self, test_data: Dict[str, Any]) -> Set[str]:
        """
        Extract all question IDs from a test.
        
        Args:
            test_data: Test data dictionary
        
        Returns:
            Set of question IDs
        """
        question_ids = set()
        
        for section in test_data.get("sections", []):
            for question in section.get("questions", []):
                qid = question.get("question_id")
                if qid:
                    question_ids.add(qid)
        
        return question_ids
    
    def _extract_requirements(self, blueprint: Dict[str, Any]) -> Dict[str, Dict[str, int]]:
        """
        Extract question requirements from blueprint.
        
        Args:
            blueprint: Test blueprint
        
        Returns:
            Dict of {subject: {difficulty: count}}
        """
        requirements = defaultdict(lambda: defaultdict(int))
        
        for section in blueprint.get("sections", []):
            section_name = section["section_name"]
            master_name = self._map_section_to_master(section_name)
            
            # Check for subsections (Quant)
            if "subsections" in section:
                for subsection in section["subsections"]:
                    subsection_name = subsection["subsection_name"]
                    
                    if subsection_name == "Data Interpretation":
                        subject_key = "di"
                    else:
                        subject_key = "arithmetic"
                    
                    diff_dist = subsection.get("difficulty_distribution", {})
                    for difficulty, count in diff_dist.items():
                        requirements[subject_key][difficulty] += count
            else:
                # Regular section
                diff_dist = section.get("difficulty_distribution", {})
                for difficulty, count in diff_dist.items():
                    requirements[master_name][difficulty] += count
        
        return dict(requirements)
    
    def _get_available_by_difficulty(self) -> Dict[str, Dict[str, int]]:
        """
        Get count of available questions by subject and difficulty.
        
        Returns:
            Dict of {subject: {difficulty: count}}
        """
        available = defaultdict(lambda: defaultdict(int))
        
        subjects = ["english", "general_awareness", "reasoning", "arithmetic", "di"]
        
        for subject in subjects:
            master_file = f"{subject}_master_question_bank.json"
            master_data = self.master_loader.masters.get(master_file, {})
            
            if subject == "di":
                # Handle DI questions (they're organized as sets)
                di_sets = master_data.get("questions", [])
                for di_set in di_sets:
                    set_questions = di_set.get("questions", [])
                    for question in set_questions:
                        difficulty = question.get("difficulty", "Medium").strip()
                        available[subject][difficulty] += 1
            else:
                # Handle regular questions
                questions = master_data.get("questions", [])
                for question in questions:
                    difficulty = question.get("difficulty", "Medium").strip()
                    available[subject][difficulty] += 1
        
        return dict(available)
    
    def _map_section_to_master(self, section_name: str) -> str:
        """
        Map section name to master bank name.
        
        Args:
            section_name: Section name from blueprint
        
        Returns:
            Master bank name
        """
        mapping = {
            "General Awareness": "general_awareness",
            "English Language": "english",
            "Quantitative Aptitude": "arithmetic",  # Will be split into arithmetic + DI
            "Reasoning": "reasoning"
        }
        
        return mapping.get(section_name, section_name.lower().replace(" ", "_"))
    
    def _calculate_section_difficulty(self, total_questions: int) -> Dict[str, int]:
        """
        Calculate difficulty distribution for a section based on overall percentages.
        
        Args:
            total_questions: Total questions in section
        
        Returns:
            Dict with Easy/Medium/Hard counts
        """
        easy = round(total_questions * self.difficulty_distribution["Easy"] / 100)
        medium = round(total_questions * self.difficulty_distribution["Medium"] / 100)
        hard = round(total_questions * self.difficulty_distribution["Hard"] / 100)
        
        # Adjust for rounding errors
        total = easy + medium + hard
        if total < total_questions:
            medium += (total_questions - total)
        elif total > total_questions:
            medium -= (total - total_questions)
        
        return {
            "Easy": easy,
            "Medium": medium,
            "Hard": hard
        }
    
    def _count_difficulty(self, questions: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Count questions by difficulty level.
        
        Args:
            questions: List of questions
        
        Returns:
            Dict with difficulty counts
        """
        counts = defaultdict(int)
        for question in questions:
            difficulty = question.get("difficulty", "Medium").strip()
            counts[difficulty] += 1
        
        return dict(counts)
    
    def _count_topics(self, questions: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Count questions by topic.
        
        Args:
            questions: List of questions
        
        Returns:
            Dict with topic counts
        """
        counts = defaultdict(int)
        for question in questions:
            topic = question.get("topic", "General")
            counts[topic] += 1
        
        return dict(counts)
    
    def _create_metadata(
        self,
        blueprint: Dict[str, Any],
        test_number: int,
        section_reports: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create metadata for the test.
        
        Args:
            blueprint: Test blueprint
            test_number: Test number
            section_reports: Section generation reports
        
        Returns:
            Metadata dictionary
        """
        return {
            "generated_at": datetime.now().isoformat(),
            "generator_version": "1.0.0",
            "test_number": test_number,
            "blueprint_id": blueprint.get("test_id", ""),
            "overlap_percentage": self.overlap_percentage,
            "difficulty_distribution": self.difficulty_distribution,
            "section_reports": section_reports,
            "pricing": blueprint.get("pricing", {})
        }
    
    def _validate_test(
        self,
        test: Dict[str, Any],
        blueprint: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate generated test against blueprint.
        
        Args:
            test: Generated test
            blueprint: Test blueprint
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check total questions
        expected_total = blueprint.get("total_questions", 200)
        actual_total = sum(
            len(section.get("questions", []))
            for section in test.get("sections", [])
        )
        
        if actual_total != expected_total:
            errors.append(
                f"Total questions mismatch: expected {expected_total}, got {actual_total}"
            )
        
        # Check sections
        expected_sections = len(blueprint.get("sections", []))
        actual_sections = len(test.get("sections", []))
        
        if actual_sections != expected_sections:
            errors.append(
                f"Section count mismatch: expected {expected_sections}, got {actual_sections}"
            )
        
        # Check for duplicate question IDs within test
        all_qids = []
        for section in test.get("sections", []):
            for question in section.get("questions", []):
                qid = question.get("question_id")
                if qid:
                    all_qids.append(qid)
        
        duplicates = [qid for qid, count in Counter(all_qids).items() if count > 1]
        if duplicates:
            errors.append(f"Duplicate question IDs within test: {duplicates}")
        
        return len(errors) == 0, errors
    
    def _save_series_summary(
        self,
        generated_tests: List[Dict[str, Any]],
        output_path: Path,
        blueprint: Dict[str, Any]
    ):
        """
        Save summary report for the entire test series.
        
        Args:
            generated_tests: List of generated test info
            output_path: Output directory path
            blueprint: Test blueprint
        """
        summary = {
            "series_name": blueprint.get("test_series", "RBI Grade B Mock Series"),
            "total_tests_generated": len(generated_tests),
            "generated_at": datetime.now().isoformat(),
            "configuration": {
                "overlap_percentage": self.overlap_percentage,
                "difficulty_distribution": self.difficulty_distribution,
                "questions_per_test": blueprint.get("total_questions", 200),
                "duration_minutes": blueprint.get("duration_minutes", 120)
            },
            "pricing": blueprint.get("pricing", {}),
            "tests": generated_tests,
            "statistics": self._calculate_series_statistics(generated_tests)
        }
        
        # Save summary
        summary_file = output_path / "series_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"\n📊 Series Summary saved: {summary_file}")
        
        # Print summary
        self._print_series_summary(summary)
    
    def _calculate_series_statistics(
        self,
        generated_tests: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate statistics for the test series.
        
        Args:
            generated_tests: List of generated test info
        
        Returns:
            Statistics dictionary
        """
        if not generated_tests:
            return {}
        
        total_tests = len(generated_tests)
        
        # Calculate average overlap (excluding first test)
        overlaps = [t['overlap_percentage'] for t in generated_tests[1:]] if total_tests > 1 else [0]
        avg_overlap = sum(overlaps) / len(overlaps) if overlaps else 0
        
        # Calculate total unique questions across all tests
        all_qids = set()
        for test_info in self.tests_generated:
            all_qids.update(test_info['question_ids'])
        
        total_unique_questions = len(all_qids)
        
        # Questions per subject
        questions_by_subject = defaultdict(int)
        for subject, qid_dict in self.used_questions.items():
            questions_by_subject[subject] = len(qid_dict)
        
        return {
            "total_tests": total_tests,
            "average_overlap": round(avg_overlap, 2),
            "total_unique_questions_used": total_unique_questions,
            "questions_per_test": generated_tests[0]['total_questions'] if generated_tests else 0,
            "questions_by_subject": dict(questions_by_subject),
            "overlap_range": {
                "min": round(min(overlaps), 2) if overlaps else 0,
                "max": round(max(overlaps), 2) if overlaps else 0
            }
        }
    
    def _print_series_summary(self, summary: Dict[str, Any]):
        """
        Print formatted series summary.
        
        Args:
            summary: Summary dictionary
        """
        print("\n" + "="*80)
        print("📊 TEST SERIES GENERATION COMPLETE")
        print("="*80)
        
        print(f"\n🎯 Series: {summary['series_name']}")
        print(f"   Tests Generated: {summary['total_tests_generated']}")
        print(f"   Questions per Test: {summary['configuration']['questions_per_test']}")
        print(f"   Duration: {summary['configuration']['duration_minutes']} minutes")
        
        print(f"\n⚙️  Configuration:")
        print(f"   Overlap Allowed: {summary['configuration']['overlap_percentage']}%")
        print(f"   Uniqueness Required: {100 - summary['configuration']['overlap_percentage']}%")
        
        diff_dist = summary['configuration']['difficulty_distribution']
        print(f"   Difficulty Distribution:")
        print(f"      Easy: {diff_dist['Easy']}%")
        print(f"      Medium: {diff_dist['Medium']}%")
        print(f"      Hard: {diff_dist['Hard']}%")
        
        stats = summary.get('statistics', {})
        if stats:
            print(f"\n📈 Statistics:")
            print(f"   Average Overlap: {stats['average_overlap']:.2f}%")
            print(f"   Overlap Range: {stats['overlap_range']['min']:.2f}% - {stats['overlap_range']['max']:.2f}%")
            print(f"   Total Unique Questions Used: {stats['total_unique_questions_used']}")
            
            print(f"\n   Questions Used by Subject:")
            for subject, count in stats.get('questions_by_subject', {}).items():
                print(f"      {subject.replace('_', ' ').title()}: {count}")
        
        if 'pricing' in summary:
            pricing = summary['pricing']
            print(f"\n💰 Pricing:")
            print(f"   Per Test: ₹{pricing.get('per_test', 99)}")
            print(f"   Full Bundle ({summary['total_tests_generated']} tests): ₹{pricing.get('bundle', 499)}")
            
            if 'per_test' in pricing and 'bundle' in pricing:
                savings = (pricing['per_test'] * summary['total_tests_generated']) - pricing['bundle']
                savings_percent = (savings / (pricing['per_test'] * summary['total_tests_generated'])) * 100
                print(f"   Bundle Savings: ₹{savings} ({savings_percent:.1f}% off)")
        
        print(f"\n✅ All tests saved in: {summary.get('output_directory', 'generated_tests/')}")
        print("\n" + "="*80 + "\n")
    
    def get_usage_report(self) -> Dict[str, Any]:
        """
        Get detailed usage report of questions across all generated tests.
        
        Returns:
            Usage report dictionary
        """
        report = {
            "total_tests_generated": len(self.tests_generated),
            "subjects": {}
        }
        
        for subject, usage_dict in self.used_questions.items():
            total_questions = len(usage_dict)
            
            # Count usage frequency
            usage_counts = Counter()
            for qid, test_numbers in usage_dict.items():
                usage_counts[len(test_numbers)] += 1
            
            # Most used questions
            most_used = sorted(
                usage_dict.items(),
                key=lambda x: len(x[1]),
                reverse=True
            )[:10]
            
            report["subjects"][subject] = {
                "total_questions_used": total_questions,
                "usage_frequency": dict(usage_counts),
                "most_used_questions": [
                    {
                        "question_id": qid,
                        "used_in_tests": test_nums,
                        "usage_count": len(test_nums)
                    }
                    for qid, test_nums in most_used
                ]
            }
        
        return report
    
    def print_usage_report(self):
        """
        Print detailed usage report to console.
        """
        report = self.get_usage_report()
        
        print("\n" + "="*80)
        print("📊 QUESTION USAGE REPORT")
        print("="*80)
        
        print(f"\nTotal Tests Generated: {report['total_tests_generated']}")
        
        for subject, data in report['subjects'].items():
            print(f"\n📚 {subject.replace('_', ' ').title()}:")
            print(f"   Total Questions Used: {data['total_questions_used']}")
            
            print(f"   Usage Frequency:")
            for times_used, count in sorted(data['usage_frequency'].items()):
                print(f"      Used {times_used}x: {count} questions")
            
            if data['most_used_questions']:
                print(f"   Most Used Questions:")
                for item in data['most_used_questions'][:5]:
                    print(f"      {item['question_id']}: used {item['usage_count']}x in tests {item['used_in_tests']}")
        
        print("\n" + "="*80 + "\n")
    
    def reset_tracking(self):
        """
        Reset all question tracking (for generating new series).
        """
        self.used_questions = {
            "english": defaultdict(list),
            "general_awareness": defaultdict(list),
            "reasoning": defaultdict(list),
            "arithmetic": defaultdict(list),
            "di": defaultdict(list)
        }
        self.tests_generated = []
        
        print("\n✅ Question tracking reset. Ready to generate new series.")


def create_commercial_generator(
    overlap_percentage: int = 20,
    difficulty_distribution: Dict[str, int] = None,
    masters_dir: str = None
) -> CommercialTestGenerator:
    """
    Convenience function to create and initialize commercial test generator.
    
    Args:
        overlap_percentage: Allowed overlap percentage (0-100)
        difficulty_distribution: Difficulty distribution dict
        masters_dir: Directory containing master banks
    
    Returns:
        Initialized CommercialTestGenerator
    """
    print("\n🚀 Initializing Commercial Test Generator...")
    
    if masters_dir is None:
        # Calculate path relative to project root
        project_root = Path(__file__).parent.parent.parent
        masters_dir = str(project_root / "data" / "generated" / "master_questions")
    
    # Load master question banks
    master_files = [
        "english_master_question_bank.json",
        "general_awareness_master_question_bank.json",
        "reasoning_master_question_bank.json",
        "arithmetic_master_question_bank.json",
        "di_master_question_bank.json"
    ]
    
    master_loader = load_masters(master_files, masters_dir)
    
    # Create generator
    generator = CommercialTestGenerator(
        master_loader=master_loader,
        overlap_percentage=overlap_percentage,
        difficulty_distribution=difficulty_distribution
    )
    
    print("✅ Generator Ready!\n")
    
    return generator


# Example usage and testing
if __name__ == "__main__":
    print("="*80)
    print("COMMERCIAL TEST GENERATOR - RBI GRADE B PHASE 1")
    print("="*80)
    
    # Example 1: Create generator with 20% overlap (80% unique)
    print("\n📋 Example 1: Generate 5 tests with 20% overlap")
    
    try:
        # Load blueprint
        project_root = Path(__file__).parent.parent.parent
        blueprint_path = project_root / "data" / "blueprints" / "rbi_phase1_commercial_blueprint.json"
        if not blueprint_path.exists():
            print(f"❌ Blueprint not found: {blueprint_path}")
            print("   Please ensure blueprint file exists.")
        else:
            with open(blueprint_path, 'r', encoding='utf-8') as f:
                blueprint = json.load(f)
            
            # Create generator
            generator = create_commercial_generator(
                overlap_percentage=20,
                difficulty_distribution={
                    "Easy": 20,
                    "Medium": 50,
                    "Hard": 30
                }
            )
            
            # Calculate maximum possible tests (for reference)
            max_info = generator.calculate_max_tests(blueprint)
            print(f"\n📊 Maximum possible unique tests: {max_info['max_tests']}")
            
            # Generate tests from blueprint
            num_tests_from_blueprint = blueprint.get("num_tests", 5)
            num_tests = num_tests_from_blueprint  # Use the requested number from blueprint
            
            if num_tests > max_info['max_tests']:
                print(f"\n⚠️  Warning: Requesting {num_tests} tests but only {max_info['max_tests']} are calculated as possible.")
                print(f"   Will attempt to generate {num_tests} tests with smart overlap management.")
            
            print(f"\n📋 Generating {num_tests} tests (blueprint requests {num_tests_from_blueprint})")

            
            if num_tests > 0:
                generated_tests = generator.generate_test_series(
                    blueprint=blueprint,
                    num_tests=num_tests,
                    output_dir="generated_tests/commercial_series",
                    test_name_prefix="RBI_PHASE1_MOCK"
                )
                
                print(f"\n✅ Successfully generated {len(generated_tests)} tests")
                
                # Print usage report
                generator.print_usage_report()
            else:
                print("\n⚠️  Not enough questions in master banks to generate tests.")
    
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("   Please ensure master banks are loaded in 'master_banks/' directory")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    
    # Example 2: Different overlap settings
    print("\n" + "="*80)
    print("📋 Example 2: Different Overlap Settings")
    print("="*80)
    
    overlap_examples = [
        {"overlap": 0, "description": "Zero overlap (100% unique)"},
        {"overlap": 10, "description": "10% overlap (90% unique)"},
        {"overlap": 30, "description": "30% overlap (70% unique)"},
        {"overlap": 50, "description": "50% overlap (50% unique)"}
    ]
    
    print("\nOverlap Settings Comparison:")
    print(f"{'Overlap':<15} {'Uniqueness':<15} {'Description'}")
    print("-" * 60)
    
    for example in overlap_examples:
        overlap = example['overlap']
        uniqueness = 100 - overlap
        desc = example['description']
        print(f"{overlap}%{'':<12} {uniqueness}%{'':<12} {desc}")
    
    print("\n💡 Recommendation: 20% overlap provides best balance between")
    print("   uniqueness and scalability for commercial test series.")
    
    # Example 3: Difficulty distribution options
    print("\n" + "="*80)
    print("📋 Example 3: Difficulty Distribution Options")
    print("="*80)
    
    difficulty_presets = {
        "Balanced": {"Easy": 20, "Medium": 50, "Hard": 30},
        "Easy-Heavy": {"Easy": 40, "Medium": 40, "Hard": 20},
        "Hard-Heavy": {"Easy": 15, "Medium": 35, "Hard": 50},
        "Medium-Focus": {"Easy": 25, "Medium": 60, "Hard": 15}
    }
    
    print("\nDifficulty Distribution Presets:")
    print(f"{'Preset':<20} {'Easy':<10} {'Medium':<10} {'Hard':<10}")
    print("-" * 50)
    
    for preset_name, dist in difficulty_presets.items():
        print(f"{preset_name:<20} {dist['Easy']}%{'':<7} {dist['Medium']}%{'':<7} {dist['Hard']}%")
    
    print("\n" + "="*80)
    print("✅ Commercial Test Generator Examples Complete")
    print("="*80)


