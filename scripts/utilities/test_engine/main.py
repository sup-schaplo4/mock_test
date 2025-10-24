"""
Main Pipeline Script
Orchestrates the complete test generation pipeline:
1. Load and validate blueprints
2. Load master question banks
3. Generate tests from blueprints
4. Save generated tests
5. Generate reports
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from master_loader import load_masters
from test_assembler import TestGenerator


class TestGenerationPipeline:
    """Main pipeline for test generation."""
    
    def __init__(
        self,
        blueprints_dir: str = None,
        masters_dir: str = None,
        output_dir: str = None
    ):
        """
        Initialize the pipeline.
        
        Args:
            blueprints_dir: Directory containing blueprint files
            masters_dir: Directory containing master question banks
            output_dir: Directory to save generated tests
        """
        # Calculate paths relative to project root
        project_root = Path(__file__).parent.parent.parent
        
        if blueprints_dir is None:
            blueprints_dir = project_root / "data" / "blueprints"
        if masters_dir is None:
            masters_dir = project_root / "data" / "generated" / "master_questions"
        if output_dir is None:
            output_dir = project_root / "data" / "generated" / "tests"
        
        self.blueprints_dir = Path(blueprints_dir)
        self.masters_dir = Path(masters_dir)
        self.output_dir = Path(output_dir)
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.master_loader = None
        self.test_generator = None
        self.pipeline_report = {
            "started_at": None,
            "completed_at": None,
            "blueprints_processed": 0,
            "tests_generated": 0,
            "errors": [],
            "warnings": [],
            "generated_tests": []
        }
    
    def run(
        self,
        blueprint_files: List[str] = None,
        master_files: List[str] = None,
        shuffle_questions: bool = True,
        allow_duplicates: bool = False
    ):
        """
        Run the complete test generation pipeline.
        
        Args:
            blueprint_files: List of blueprint filenames (None = all blueprints)
            master_files: List of master filenames (None = default set)
            shuffle_questions: Whether to shuffle questions within sections
            allow_duplicates: Whether to allow duplicate questions across tests
        """
        self.pipeline_report["started_at"] = datetime.now().isoformat()
        
        print("\n" + "=" * 80)
        print("🚀 TEST GENERATION PIPELINE")
        print("=" * 80)
        
        try:
            # Step 1: Load master question banks
            self._load_masters(master_files)
            
            # Step 2: Load blueprints
            blueprints = self._load_blueprints(blueprint_files)
            
            # Step 3: Generate tests
            self._generate_tests(blueprints, shuffle_questions, allow_duplicates)
            
            # Step 4: Generate summary report
            self._generate_summary_report()
            
            print("\n" + "=" * 80)
            print("✅ PIPELINE COMPLETED SUCCESSFULLY")
            print("=" * 80)
            
        except Exception as e:
            error_msg = f"Pipeline failed: {str(e)}"
            self.pipeline_report["errors"].append(error_msg)
            print(f"\n❌ {error_msg}\n")
            import traceback
            traceback.print_exc()
            
        finally:
            self.pipeline_report["completed_at"] = datetime.now().isoformat()
    
    def _load_masters(self, master_files: List[str] = None):
        """
        Load master question banks.
        
        Args:
            master_files: List of master filenames
        """
        print("\n📚 STEP 1: Loading Master Question Banks")
        print("-" * 80)
        
        if master_files is None:
            master_files = [
                "english_master_question_bank.json",
                "general_awareness_master_question_bank.json",
                "reasoning_master_question_bank.json",
                "arithmetic_master_question_bank.json",
                "di_master_question_bank.json"
            ]
        
        print(f"Loading {len(master_files)} master files:")
        for mf in master_files:
            print(f"   • {mf}")
        
        self.master_loader = load_masters(master_files, str(self.masters_dir))
        self.test_generator = TestGenerator(self.master_loader)
        
        print("\n✅ Master question banks loaded successfully")
    
    def _load_blueprints(self, blueprint_files: List[str] = None) -> List[Dict[str, Any]]:
        """
        Load blueprint files.
        
        Args:
            blueprint_files: List of blueprint filenames (None = all)
        
        Returns:
            List of blueprint dictionaries
        """
        print("\n📋 STEP 2: Loading Blueprints")
        print("-" * 80)
        
        blueprints = []
        
        if blueprint_files is None:
            # Load all blueprint files
            blueprint_files = [
                f.name for f in self.blueprints_dir.glob("*.json")
            ]
        
        if not blueprint_files:
            raise ValueError(f"No blueprints found in {self.blueprints_dir}")
        
        print(f"Loading {len(blueprint_files)} blueprint(s):")
        
        for blueprint_file in blueprint_files:
            try:
                blueprint_path = self.blueprints_dir / blueprint_file
                
                with open(blueprint_path, 'r', encoding='utf-8') as f:
                    blueprint = json.load(f)
                
                blueprints.append({
                    "filename": blueprint_file,
                    "data": blueprint
                })
                
                print(f"   ✅ {blueprint_file}")
                
            except Exception as e:
                error_msg = f"Failed to load {blueprint_file}: {str(e)}"
                self.pipeline_report["errors"].append(error_msg)
                print(f"   ❌ {error_msg}")
        
        print(f"\n✅ Loaded {len(blueprints)} blueprint(s) successfully")
        
        return blueprints
    
    def _generate_tests(
        self,
        blueprints: List[Dict[str, Any]],
        shuffle_questions: bool,
        allow_duplicates: bool
    ):
        """
        Generate tests from blueprints.
        
        Args:
            blueprints: List of blueprint dictionaries
            shuffle_questions: Whether to shuffle questions
            allow_duplicates: Whether to allow duplicate questions
        """
        print("\n🎯 STEP 3: Generating Tests")
        print("-" * 80)
        
        for idx, blueprint_info in enumerate(blueprints, 1):
            filename = blueprint_info["filename"]
            blueprint = blueprint_info["data"]
            
            print(f"\n[{idx}/{len(blueprints)}] Processing: {filename}")
            print("-" * 80)
            
            try:
                # Generate test
                test = self.test_generator.generate_test(
                    blueprint,
                    shuffle_questions,
                    allow_duplicates
                )
                
                # Save test
                output_filename = filename.replace(".json", "_generated.json")
                output_path = self.output_dir / output_filename
                self.test_generator.save_test(test, str(output_path))
                
                # Update report
                self.pipeline_report["blueprints_processed"] += 1
                self.pipeline_report["tests_generated"] += 1
                self.pipeline_report["generated_tests"].append({
                    "blueprint": filename,
                    "test_id": test["test_id"],
                    "test_name": test["test_name"],
                    "output_file": output_filename,
                    "total_questions": test["total_questions"],
                    "sections": len(test["sections"])
                })
                
                print(f"\n✅ Test generated successfully: {output_filename}")
                
                # Reset selectors if not allowing duplicates
                if not allow_duplicates:
                    self.test_generator.question_selector.reset()
                    self.test_generator.di_selector.reset()
                
            except Exception as e:
                error_msg = f"Failed to generate test from {filename}: {str(e)}"
                self.pipeline_report["errors"].append(error_msg)
                print(f"\n❌ {error_msg}")
                import traceback
                traceback.print_exc()
        
        print(f"\n✅ Generated {self.pipeline_report['tests_generated']} test(s)")
    
    def _generate_summary_report(self):
        """Generate and save pipeline summary report."""
        print("\n📊 STEP 4: Generating Summary Report")
        print("-" * 80)
        
        report_path = self.output_dir / "pipeline_report.json"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.pipeline_report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Pipeline Report:")
        print(f"   Started: {self.pipeline_report['started_at']}")
        print(f"   Completed: {self.pipeline_report['completed_at']}")
        print(f"   Blueprints Processed: {self.pipeline_report['blueprints_processed']}")
        print(f"   Tests Generated: {self.pipeline_report['tests_generated']}")
        
        if self.pipeline_report["errors"]:
            print(f"   ❌ Errors: {len(self.pipeline_report['errors'])}")
            for error in self.pipeline_report["errors"]:
                print(f"      • {error}")
        
        if self.pipeline_report["warnings"]:
            print(f"   ⚠️  Warnings: {len(self.pipeline_report['warnings'])}")
            for warning in self.pipeline_report["warnings"]:
                print(f"      • {warning}")
        
        print(f"\n💾 Report saved to: {report_path}")
        
        # Print generated tests summary
        if self.pipeline_report["generated_tests"]:
            print(f"\n📝 Generated Tests:")
            for test_info in self.pipeline_report["generated_tests"]:
                print(f"   • {test_info['test_name']} ({test_info['test_id']})")
                print(f"     File: {test_info['output_file']}")
                print(f"     Questions: {test_info['total_questions']}, Sections: {test_info['sections']}")


def main():
    """Main entry point."""
    print("\n" + "=" * 80)
    print("RBI GRADE B PHASE 1 - MOCK TEST GENERATOR")
    print("=" * 80)
    
    # Create and run pipeline
    pipeline = TestGenerationPipeline()
    
    # Generate tests from all blueprints
    pipeline.run(
        blueprint_files=None,  # Process all blueprints
        master_files=None,     # Use default master files
        shuffle_questions=True,
        allow_duplicates=False
    )
    
    print("\n" + "=" * 80)
    print("Thank you for using the Mock Test Generator!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
