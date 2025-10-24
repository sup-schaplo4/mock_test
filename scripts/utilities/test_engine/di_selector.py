"""
DI Selector Module
Handles selection of Data Interpretation (DI) sets.
Each DI set contains 5 questions based on a common data set.
"""

from typing import Dict, List, Any, Set
import random

from master_loader import MasterLoader


class DISelector:
    """Handles DI set selection."""
    
    def __init__(self, master_loader: MasterLoader):
        """
        Initialize the DI selector.
        
        Args:
            master_loader: MasterLoader instance with loaded masters
        """
        self.master_loader = master_loader
        self.selected_di_set_ids: Set[str] = set()
        self.di_sets = self._organize_di_sets()
        
    def _organize_di_sets(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Organize DI questions into sets by di_set_id.
        
        Returns:
            Dictionary mapping di_set_id to list of questions
        """
        # Find DI master file
        di_master_file = None
        for filename in self.master_loader.masters.keys():
            if "di_master" in filename:
                di_master_file = filename
                break
        
        if not di_master_file:
            return {}
        
        # Get DI sets from master file
        di_sets_data = self.master_loader.masters[di_master_file].get("questions", [])
        
        di_sets = {}
        for di_set in di_sets_data:
            set_id = di_set.get("di_set_id")
            if set_id:
                # Get the questions from within this DI set
                questions = di_set.get("questions", [])
                di_sets[set_id] = questions
        
        # Sort questions within each set by question_id for consistency
        for set_id in di_sets:
            di_sets[set_id].sort(key=lambda q: q.get("question_id", ""))
        
        return di_sets
    
    def select_di_sets(
        self,
        num_sets: int,
        difficulty_distribution: Dict[str, int] = None,
        allow_duplicates: bool = False
    ) -> tuple:
        """
        Select DI sets based on requirements.
        
        Args:
            num_sets: Number of DI sets to select
            difficulty_distribution: Difficulty distribution (in questions, not sets)
            allow_duplicates: Whether to allow duplicate sets
        
        Returns:
            Tuple of (selected_sets, selection_report)
        """
        if num_sets == 0:
            return [], {"requested": 0, "selected": 0, "set_ids": []}
        
        # Get available DI sets
        available_sets = self._get_available_di_sets(allow_duplicates)
        
        if len(available_sets) < num_sets:
            print(f"   ⚠️  Warning: Only {len(available_sets)} DI sets available, need {num_sets}")
            num_sets = len(available_sets)
        
        if num_sets == 0:
            return [], {"requested": num_sets, "selected": 0, "set_ids": []}
        
        # If difficulty distribution provided, try to match it
        if difficulty_distribution:
            selected_sets = self._select_by_difficulty(
                available_sets,
                num_sets,
                difficulty_distribution
            )
        else:
            # Random selection
            selected_sets = random.sample(available_sets, min(num_sets, len(available_sets)))
        
        # Mark as selected
        if not allow_duplicates:
            for set_id in selected_sets:
                self.selected_di_set_ids.add(set_id)
        
        selection_report = {
            "requested": num_sets,
            "selected": len(selected_sets),
            "set_ids": selected_sets,
            "total_questions": len(selected_sets) * 5
        }
        
        return selected_sets, selection_report
    
    def _select_by_difficulty(
        self,
        available_sets: List[str],
        num_sets: int,
        difficulty_distribution: Dict[str, int]
    ) -> List[str]:
        """
        Select DI sets trying to match difficulty distribution.
        
        Args:
            available_sets: List of available DI set IDs
            num_sets: Number of sets to select
            difficulty_distribution: Target difficulty (in questions)
        
        Returns:
            List of selected DI set IDs
        """
        # Calculate sets needed per difficulty (each set = 5 questions)
        sets_per_difficulty = {}
        total_sets_allocated = 0
        
        for difficulty in ["Easy", "Medium", "Hard"]:
            questions_needed = difficulty_distribution.get(difficulty, 0)
            sets_needed = questions_needed // 5
            sets_per_difficulty[difficulty] = sets_needed
            total_sets_allocated += sets_needed
        
        # Adjust if total doesn't match (add extra to Medium)
        diff = num_sets - total_sets_allocated
        if diff > 0:
            sets_per_difficulty["Medium"] = sets_per_difficulty.get("Medium", 0) + diff
        elif diff < 0:
            # Too many allocated, reduce from Medium first
            sets_per_difficulty["Medium"] = max(0, sets_per_difficulty.get("Medium", 0) + diff)
        
        # Select sets for each difficulty
        selected = []
        
        for difficulty in ["Easy", "Medium", "Hard"]:
            count = sets_per_difficulty.get(difficulty, 0)
            if count == 0:
                continue
            
            # Get sets of this difficulty
            difficulty_sets = [
                set_id for set_id in available_sets
                if self._get_set_difficulty(set_id) == difficulty
                and set_id not in selected
            ]
            
            # Select required number (or all available)
            to_select = min(count, len(difficulty_sets))
            
            if to_select > 0:
                selected_batch = random.sample(difficulty_sets, to_select)
                selected.extend(selected_batch)
            
            # If we couldn't get enough from this difficulty, get from others
            if to_select < count:
                shortfall = count - to_select
                backup_sets = self._get_backup_sets(
                    available_sets,
                    selected,
                    shortfall,
                    exclude_difficulty=difficulty
                )
                selected.extend(backup_sets)
        
        return selected
    
    def _get_backup_sets(
        self,
        available_sets: List[str],
        already_selected: List[str],
        count: int,
        exclude_difficulty: str = None
    ) -> List[str]:
        """
        Get backup DI sets when primary difficulty selection falls short.
        
        Args:
            available_sets: All available set IDs
            already_selected: Already selected set IDs
            count: Number of sets needed
            exclude_difficulty: Difficulty to exclude
        
        Returns:
            List of backup set IDs
        """
        # Get remaining sets
        remaining = [
            set_id for set_id in available_sets
            if set_id not in already_selected
        ]
        
        # Filter by difficulty if needed
        if exclude_difficulty:
            remaining = [
                set_id for set_id in remaining
                if self._get_set_difficulty(set_id) != exclude_difficulty
            ]
        
        # Select randomly
        to_select = min(count, len(remaining))
        if to_select > 0:
            return random.sample(remaining, to_select)
        
        return []
    
    def _get_set_difficulty(self, set_id: str) -> str:
        """
        Get the difficulty of a DI set.
        Uses the difficulty of the first question in the set.
        
        Args:
            set_id: DI set ID
        
        Returns:
            Difficulty level
        """
        questions = self.di_sets.get(set_id, [])
        if questions:
            return questions[0].get("difficulty", "Medium")
        return "Medium"
    
    def _get_available_di_sets(self, allow_duplicates: bool = False) -> List[str]:
        """
        Get list of available DI set IDs.
        
        Args:
            allow_duplicates: Whether to include already selected sets
        
        Returns:
            List of available DI set IDs
        """
        all_set_ids = list(self.di_sets.keys())
        
        if allow_duplicates:
            return all_set_ids
        
        # Filter out already selected
        return [
            set_id for set_id in all_set_ids
            if set_id not in self.selected_di_set_ids
        ]
    
    def get_di_set_questions(self, set_id: str) -> List[Dict[str, Any]]:
        """
        Get all questions for a specific DI set.
        
        Args:
            set_id: DI set ID
        
        Returns:
            List of questions in the set
        """
        return self.di_sets.get(set_id, [])
    
    def get_all_di_sets_info(self) -> Dict[str, Any]:
        """
        Get information about all DI sets.
        
        Returns:
            Dictionary with DI sets information
        """
        info = {
            "total_sets": len(self.di_sets),
            "total_questions": sum(len(questions) for questions in self.di_sets.values()),
            "sets_by_difficulty": {"Easy": 0, "Medium": 0, "Hard": 0},
            "selected_sets": len(self.selected_di_set_ids)
        }
        
        for set_id in self.di_sets:
            difficulty = self._get_set_difficulty(set_id)
            info["sets_by_difficulty"][difficulty] = info["sets_by_difficulty"].get(difficulty, 0) + 1
        
        return info
    
    def get_questions_from_selected_sets(self, selected_set_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Get all questions from a list of selected DI set IDs.
        
        Args:
            selected_set_ids: List of DI set IDs
            
        Returns:
            List of all questions from the selected sets
        """
        all_questions = []
        for set_id in selected_set_ids:
            questions = self.get_di_set_questions(set_id)
            all_questions.extend(questions)
        return all_questions
    
    def reset(self):
        """Reset selection state."""
        self.selected_di_set_ids.clear()


# For testing
if __name__ == "__main__":
    from master_loader import load_masters
    
    print("\n🔍 Testing DI Selector")
    print("=" * 80)
    
    # Load masters
    master_files = [
        "english_master_question_bank.json",
        "general_awareness_master_question_bank.json",
        "reasoning_master_question_bank.json",
        "arithmetic_master_question_bank.json",
        "di_master_question_bank.json"
    ]
    
    # Use absolute path to master directory
    import os
    master_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "generated", "master_questions")
    loader = load_masters(master_files, master_dir)
    selector = DISelector(loader)
    
    # Print DI sets info
    info = selector.get_all_di_sets_info()
    print(f"\nDI Sets Information:")
    print(f"   Total Sets: {info['total_sets']}")
    print(f"   Total Questions: {info['total_questions']}")
    print(f"   By Difficulty: {info['sets_by_difficulty']}")
    
    # Test selection
    print(f"\n📋 Selecting 2 DI sets...")
    selected_sets, report = selector.select_di_sets(
        num_sets=2,
        difficulty_distribution={"Easy": 5, "Medium": 5, "Hard": 0}
    )
    
    print(f"\nSelection Report:")
    print(f"   Requested: {report['requested']} sets")
    print(f"   Selected: {report['selected']} sets")
    print(f"   Total Questions: {report['total_questions']}")
    print(f"   Set IDs: {report['set_ids']}")
    
    # Print questions from first set
    if selected_sets:
        first_set = selected_sets[0]
        questions = selector.get_di_set_questions(first_set)
        print(f"\n📊 Questions in set '{first_set}':")
        for q in questions:
            print(f"   • {q['question_id']}: {q.get('difficulty', 'N/A')}")
    
    # Test getting all questions from selected sets
    if selected_sets:
        all_questions = selector.get_questions_from_selected_sets(selected_sets)
        print(f"\n📋 All questions from selected sets: {len(all_questions)} questions")
        
        # Show difficulty distribution
        difficulty_count = {"Easy": 0, "Medium": 0, "Hard": 0}
        for q in all_questions:
            diff = q.get("difficulty", "Medium")
            if diff in difficulty_count:
                difficulty_count[diff] += 1
        
        print(f"   Difficulty distribution: {difficulty_count}")
    
    print("\n✅ DI Selector Test Complete\n")
