"""
Question Selector Module
Handles intelligent question selection from master question banks.
Implements filtering, selection strategies, and duplicate prevention.
"""

from typing import Dict, List, Any, Optional, Set
from collections import defaultdict
import random

from master_loader import MasterLoader


class QuestionSelector:
    """Handles question selection from master banks."""
    
    def __init__(self, master_loader: MasterLoader):
        """
        Initialize the question selector.
        
        Args:
            master_loader: MasterLoader instance with loaded masters
        """
        self.master_loader = master_loader
        self.selected_question_ids: Set[str] = set()
        self.selection_log = []
        
    def select_questions_for_section(
        self,
        section_config: Dict[str, Any],
        allow_duplicates: bool = False
    ) -> tuple:
        """
        Select questions for a section based on configuration.
        
        Args:
            section_config: Section configuration from blueprint
            allow_duplicates: Whether to allow duplicate questions
        
        Returns:
            Tuple of (selected_questions, selection_report)
        """
        section_id = section_config.get("section_id", "UNKNOWN")
        topic_distribution = section_config.get("topic_distribution", {})
        difficulty_distribution = section_config.get("difficulty_distribution", {})
        
        # Remove DI from topic distribution (handled separately)
        topic_distribution = {
            topic: count for topic, count in topic_distribution.items()
            if topic != "Data Interpretation"
        }
        
        selected_questions = []
        selection_report = {
            "section_id": section_id,
            "requested": {},
            "selected": {},
            "shortfall": {}
        }
        
        # Select questions for each topic
        for topic, required_count in topic_distribution.items():
            if required_count == 0:
                continue
            
            # Calculate difficulty distribution for this topic
            topic_difficulty = self._calculate_topic_difficulty(
                difficulty_distribution,
                section_config.get("total_questions", 0),
                required_count,
                topic_distribution
            )
            
            # Select questions for this topic
            topic_questions = self._select_questions_by_topic(
                topic,
                topic_difficulty,
                allow_duplicates
            )
            
            selected_questions.extend(topic_questions)
            
            # Update report
            selection_report["requested"][topic] = required_count
            selection_report["selected"][topic] = len(topic_questions)
            
            shortfall = required_count - len(topic_questions)
            if shortfall > 0:
                selection_report["shortfall"][topic] = shortfall
        
        return selected_questions, selection_report
    
    def _calculate_topic_difficulty(
        self,
        section_difficulty: Dict[str, int],
        section_total: int,
        topic_count: int,
        topic_distribution: Dict[str, int]
    ) -> Dict[str, int]:
        """
        Calculate proportional difficulty distribution for a topic.
        
        Args:
            section_difficulty: Section-level difficulty distribution
            section_total: Total questions in section
            topic_count: Number of questions needed for this topic
            topic_distribution: All topics in section
        
        Returns:
            Difficulty distribution for this topic
        """
        # Calculate total non-DI questions
        total_non_di = sum(topic_distribution.values())
        
        if total_non_di == 0:
            return {"Easy": 0, "Medium": 0, "Hard": 0}
        
        # Calculate proportion for this topic
        topic_difficulty = {}
        total_allocated = 0
        
        for difficulty in ["Easy", "Medium", "Hard"]:
            section_count = section_difficulty.get(difficulty, 0)
            
            # Calculate this topic's share of the difficulty
            proportion = topic_count / total_non_di
            allocated = round(proportion * section_count)
            
            topic_difficulty[difficulty] = allocated
            total_allocated += allocated
        
        # Adjust for rounding errors
        diff = topic_count - total_allocated
        if diff != 0:
            # Add/subtract from Medium difficulty
            topic_difficulty["Medium"] = max(0, topic_difficulty.get("Medium", 0) + diff)
        
        return topic_difficulty
    
    def _select_questions_by_topic(
        self,
        topic: str,
        difficulty_distribution: Dict[str, int],
        allow_duplicates: bool
    ) -> List[Dict[str, Any]]:
        """
        Select questions for a specific topic with difficulty distribution.
        
        Args:
            topic: Topic name
            difficulty_distribution: Required difficulty counts
            allow_duplicates: Whether to allow duplicate questions
        
        Returns:
            List of selected questions
        """
        selected = []
        
        for difficulty, count in difficulty_distribution.items():
            if count == 0:
                continue
            
            # Get available questions
            available = self._get_available_questions(
                topic=topic,
                difficulty=difficulty,
                allow_duplicates=allow_duplicates
            )
            
            # Select required number (or all available if less)
            to_select = min(count, len(available))
            
            if to_select > 0:
                selected_batch = random.sample(available, to_select)
                selected.extend(selected_batch)
                
                # Mark as selected
                if not allow_duplicates:
                    for q in selected_batch:
                        self.selected_question_ids.add(q["question_id"])
            
            # If we couldn't get enough, try to get from other difficulties
            if to_select < count:
                shortfall = count - to_select
                backup_questions = self._get_backup_questions(
                    topic=topic,
                    exclude_difficulty=difficulty,
                    count=shortfall,
                    allow_duplicates=allow_duplicates
                )
                selected.extend(backup_questions)
        
        return selected
    
    def _get_backup_questions(
        self,
        topic: str,
        exclude_difficulty: str,
        count: int,
        allow_duplicates: bool
    ) -> List[Dict[str, Any]]:
        """
        Get backup questions from other difficulties when primary selection falls short.
        
        Args:
            topic: Topic name
            exclude_difficulty: Difficulty to exclude
            count: Number of questions needed
            allow_duplicates: Whether to allow duplicates
        
        Returns:
            List of backup questions
        """
        backup = []
        
        # Try other difficulties in order: Medium, Easy, Hard
        difficulty_order = ["Medium", "Easy", "Hard"]
        if exclude_difficulty in difficulty_order:
            difficulty_order.remove(exclude_difficulty)
        
        for difficulty in difficulty_order:
            if len(backup) >= count:
                break
            
            available = self._get_available_questions(
                topic=topic,
                difficulty=difficulty,
                allow_duplicates=allow_duplicates
            )
            
            needed = count - len(backup)
            to_select = min(needed, len(available))
            
            if to_select > 0:
                selected_batch = random.sample(available, to_select)
                backup.extend(selected_batch)
                
                if not allow_duplicates:
                    for q in selected_batch:
                        self.selected_question_ids.add(q["question_id"])
        
        return backup
    
    def _get_available_questions(
        self,
        topic: str = None,
        subtopic: str = None,
        difficulty: str = None,
        allow_duplicates: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get available questions matching criteria.
        
        Args:
            topic: Topic filter
            subtopic: Subtopic filter
            difficulty: Difficulty filter
            allow_duplicates: Whether to include already selected questions
        
        Returns:
            List of available questions
        """
        available = []
        
        # Iterate through all master files
        for filename, master_data in self.master_loader.masters.items():
            if "di_master" in filename:
                continue  # Skip DI questions (handled separately)
            
            # Get questions from this master file
            questions = master_data.get("questions", [])
            
            for question in questions:
                # Check if already selected
                if not allow_duplicates:
                    if question.get("question_id") in self.selected_question_ids:
                        continue
                
                # Apply filters
                if topic and question.get("topic") != topic:
                    continue
                
                if subtopic and question.get("subtopic") != subtopic:
                    continue
                
                if difficulty and question.get("difficulty") != difficulty:
                    continue
                
                available.append(question)
        
        return available
    
    def get_selection_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about question selection.
        
        Returns:
            Statistics dictionary
        """
        return {
            "total_selected": len(self.selected_question_ids),
            "selected_ids": list(self.selected_question_ids)
        }
    
    def reset(self):
        """Reset selection state."""
        self.selected_question_ids.clear()
        self.selection_log.clear()


# For testing
if __name__ == "__main__":
    from master_loader import load_masters
    
    print("\n🔍 Testing Question Selector")
    print("=" * 80)
    
    # Load masters
    master_files = [
        "english_master_question_bank.json",
        "general_awareness_master_question_bank.json",
        "reasoning_master_question_bank.json",
        "arithmetic_master_question_bank.json"
    ]
    
    # Use absolute path to master directory
    import os
    master_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "generated", "master_questions")
    loader = load_masters(master_files, master_dir)
    selector = QuestionSelector(loader)
    
    # Test selection
    section_config = {
        "section_id": "TEST",
        "total_questions": 20,
        "topic_distribution": {
            "Banking_Sector": 10,
            "RBI_Functions": 10
        },
        "difficulty_distribution": {
            "Easy": 6,
            "Medium": 8,
            "Hard": 6
        }
    }
    
    questions, report = selector.select_questions_for_section(section_config)
    
    print(f"\nSelected {len(questions)} questions")
    print(f"Report: {report}")
    
    print("\n✅ Question Selector Test Complete\n")
