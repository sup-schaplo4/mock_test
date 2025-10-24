# ==================== CLEAN REASONING PROMPTS ====================

REASONING_PROMPTS = {
    "Linear Seating Arrangement": {
        "expert_role": "You are an expert question setter for {exam_name}, specializing in Linear Seating Arrangement puzzles.",
        "instructions": """Generate a '{difficulty}' difficulty Linear Seating Arrangement question.

**DIFFICULTY GUIDELINES FOR {difficulty}:**
{difficulty_guidelines}

**QUESTION STRUCTURE:**
1. Present 6-10 people sitting in a straight line
2. Provide 5-10 clues about their positions
3. Ask a specific question about the arrangement
4. Provide 5 options (A, B, C, D, E)
5. Include a detailed explanation with step-by-step solution

**CRITICAL RULES:**
1. All clues must be necessary and consistent
2. Must have UNIQUE solution only
3. Use clear, unambiguous language
4. Include both direct and relative position clues
5. Distractors should be actual people in the arrangement""",
        "difficulty_parameters": {
            "Easy": {
                "num_people": "6 people",
                "num_clues": "5-6 clues",
                "complexity": "Simple direct positions and immediate neighbors",
                "guidelines": "Use straightforward clues with clear positions. Avoid complex relative positioning."
            },
            "Medium": {
                "num_people": "7-8 people",
                "num_clues": "7-8 clues",
                "complexity": "Mix of direct positions, relative positions, and gaps",
                "guidelines": "Include a mix of direct positions, relative positions, and gaps. May include some negative clues."
            },
            "Hard": {
                "num_people": "8-10 people",
                "num_clues": "8-10 clues",
                "complexity": "Complex relative positioning with multiple constraints",
                "guidelines": "Use complex relative positioning, multiple constraints, negative clues, and require multi-step deduction."
            }
        },
        "main_category": "Puzzles & Seating Arrangements"
    },

    "Circular Seating Arrangement": {
        "expert_role": "You are an expert question setter for {exam_name}, specializing in Circular Seating Arrangement puzzles.",
        "instructions": """Generate a '{difficulty}' difficulty Circular Seating Arrangement question.

**DIFFICULTY GUIDELINES FOR {difficulty}:**
{difficulty_guidelines}

**QUESTION STRUCTURE:**
1. Present 6-10 people sitting around a circular table
2. Provide 5-10 clues about their positions
3. Ask a specific question about the arrangement
4. Provide 5 options (A, B, C, D, E)
5. Include a detailed explanation with circular diagram

**CRITICAL RULES:**
1. Direction matters: left/right depends on facing direction
2. All clues must be necessary and consistent
3. Must have UNIQUE solution only
4. Use clear, unambiguous language
5. Distractors should be actual people in the arrangement""",
        "difficulty_parameters": {
            "Easy": {
                "num_people": "6 people",
                "num_clues": "5-6 clues",
                "complexity": "Simple immediate neighbors and opposite positions",
                "guidelines": "Use straightforward immediate neighbor clues and simple opposite positions. Avoid complex relative positioning."
            },
            "Medium": {
                "num_people": "7-8 people",
                "num_clues": "7-8 clues",
                "complexity": "Mix of immediate neighbors, second-to-left/right, and opposite positions",
                "guidelines": "Include immediate neighbors, second-to-left/right positions, opposite positions, and simple gap clues."
            },
            "Hard": {
                "num_people": "8-10 people",
                "num_clues": "9-10 clues",
                "complexity": "Complex relative positioning with multiple constraints",
                "guidelines": "Use complex relative positioning, multiple constraints, negative clues, and require multi-step deduction."
            }
        },
        "main_category": "Puzzles & Seating Arrangements"
    },

    "Square/Rectangular/Triangular Seating": {
        "expert_role": "You are an expert question setter for {exam_name}, specializing in Special Shape Seating Arrangements.",
        "instructions": """Generate a '{difficulty}' difficulty Square/Rectangular/Triangular Seating Arrangement question.

**DIFFICULTY GUIDELINES FOR {difficulty}:**
{difficulty_guidelines}

**QUESTION STRUCTURE:**
1. Present 6-12 people sitting around a square/rectangular/triangular table
2. Provide 5-10 clues about their positions
3. Ask a specific question about the arrangement
4. Provide 5 options (A, B, C, D, E)
5. Include a detailed explanation with shape diagram

**CRITICAL RULES:**
1. Specify the exact shape and number of sides
2. All clues must be necessary and consistent
3. Must have UNIQUE solution only
4. Use clear, unambiguous language
5. Distractors should be actual people in the arrangement""",
        "difficulty_parameters": {
            "Easy": {
                "shape": "Square table (4 sides) OR Rectangular table with equal sides",
                "num_people": "6-8 people (1-2 per side)",
                "num_clues": "5-6 clues",
                "complexity": "Simple corner/middle/side positions",
                "guidelines": "Use straightforward corner/middle/side positions, simple adjacent/opposite relationships."
            },
            "Medium": {
                "shape": "Square table (4 sides) OR Rectangular table (unequal sides) OR Triangular table",
                "num_people": "6-8 people (2 per side for square, 2-3 per side for rectangular)",
                "num_clues": "7-8 clues",
                "complexity": "Mix of corner vs middle, same-side relationships, opposite positions",
                "guidelines": "Include corner vs middle distinctions, same-side relationships, opposite positions, diagonal considerations."
            },
            "Hard": {
                "shape": "Square/Rectangular table with mixed facing OR Triangular with complex arrangement",
                "num_people": "8-12 people (2-3 per side)",
                "num_clues": "9-10 clues",
                "complexity": "Complex positioning with mixed facing directions and multiple constraints",
                "guidelines": "Use complex positioning with mixed facing directions, multiple constraints, and require multi-step deduction."
            }
        },
        "main_category": "Puzzles & Seating Arrangements"
    },

    "Floor Based Puzzle": {
        "expert_role": "You are an expert question setter for {exam_name}, specializing in Floor Based Puzzles.",
        "instructions": """Generate a '{difficulty}' difficulty Floor Based Puzzle question.

**DIFFICULTY GUIDELINES FOR {difficulty}:**
{difficulty_guidelines}

**QUESTION STRUCTURE:**
1. Present 5-10 people living on different floors of a building
2. Provide 5-10 clues about their floor positions
3. Ask a specific question about the floor arrangement
4. Provide 5 options (A, B, C, D, E)
5. Include a detailed explanation with floor arrangement table

**CRITICAL RULES:**
1. All clues must be necessary and consistent
2. Must have UNIQUE solution only
3. Use clear, unambiguous language
4. Include both direct and relative floor clues
5. Distractors should be actual people in the arrangement""",
        "difficulty_parameters": {
            "Easy": {
                "num_people": "5-6 people",
                "num_floors": "5-6 floors",
                "num_clues": "5-6 clues",
                "complexity": "Simple direct floor clues and immediate above/below",
                "guidelines": "Use simple direct floor clues, immediate above/below, and basic gap clues."
            },
            "Medium": {
                "num_people": "7-8 people",
                "num_floors": "7-8 floors",
                "num_clues": "7-8 clues",
                "complexity": "Mix of direct floors, relative positions, and gap clues",
                "guidelines": "Include relative positions, gap clues (1-2 floors between), even/odd floor constraints."
            },
            "Hard": {
                "num_people": "8-10 people",
                "num_floors": "8-10 floors",
                "num_clues": "9-10 clues",
                "complexity": "Complex relative positioning with multiple constraints",
                "guidelines": "Use complex relative positioning, multiple constraints, negative clues, and require multi-step deduction."
            }
        },
        "main_category": "Puzzles & Seating Arrangements"
    },

    "Box Based Puzzle": {
        "expert_role": "You are an expert question setter for {exam_name}, specializing in Box Based Puzzles.",
        "instructions": """Generate a '{difficulty}' difficulty Box Based Puzzle question.

**DIFFICULTY GUIDELINES FOR {difficulty}:**
{difficulty_guidelines}

**QUESTION STRUCTURE:**
1. Present 5-10 boxes stacked vertically
2. Provide 5-10 clues about their positions and contents
3. Ask a specific question about the box arrangement
4. Provide 5 options (A, B, C, D, E)
5. Include a detailed explanation with box arrangement diagram

**CRITICAL RULES:**
1. All clues must be necessary and consistent
2. Must have UNIQUE solution only
3. Use clear, unambiguous language
4. Include both direct and relative position clues
5. Distractors should be actual boxes in the arrangement""",
        "difficulty_parameters": {
            "Easy": {
                "num_boxes": "5-6 boxes",
                "num_clues": "5-6 clues",
                "complexity": "Simple direct positions and immediate above/below",
                "guidelines": "Use straightforward position assignments, immediate above/below relationships, and simple gap clues."
            },
            "Medium": {
                "num_boxes": "7-8 boxes",
                "num_clues": "7-8 clues",
                "complexity": "Mix of direct positions, above/below relationships, and gap clues",
                "guidelines": "Include direct positions, above/below relationships, gap clues (1-2 boxes between), extreme position constraints."
            },
            "Hard": {
                "num_boxes": "8-10 boxes",
                "num_clues": "9-10 clues",
                "complexity": "Complex relative positioning with multiple constraints",
                "guidelines": "Use complex relative positioning, multiple constraints, negative clues, and require multi-step deduction."
            }
        },
        "main_category": "Puzzles & Seating Arrangements"
    },

    "Scheduling Puzzle": {
        "expert_role": "You are an expert question setter for {exam_name}, specializing in Scheduling Puzzles.",
        "instructions": """Generate a '{difficulty}' difficulty Scheduling Puzzle question.

**DIFFICULTY GUIDELINES FOR {difficulty}:**
{difficulty_guidelines}

**QUESTION STRUCTURE:**
1. Present 5-10 events/people to be scheduled
2. Provide 5-10 clues about their scheduling constraints
3. Ask a specific question about the schedule
4. Provide 5 options (A, B, C, D, E)
5. Include a detailed explanation with schedule table

**CRITICAL RULES:**
1. All clues must be necessary and consistent
2. Must have UNIQUE solution only
3. Use clear, unambiguous language
4. Include both direct and relative scheduling clues
5. Distractors should be actual events/people in the schedule""",
        "difficulty_parameters": {
            "Easy": {
                "time_period": "5-6 days OR 5-6 months",
                "num_events": "5-6 events/people",
                "num_clues": "5-6 clues",
                "complexity": "Simple direct day/month assignments and basic before/after relationships",
                "guidelines": "Use straightforward day/month assignments, simple before/after relationships, and basic gap clues."
            },
            "Medium": {
                "time_period": "7 days (full week) OR 6-8 months",
                "num_events": "7-8 events/people",
                "num_clues": "7-8 clues",
                "complexity": "Mix of direct day/month clues, before/after relationships, and gap clues",
                "guidelines": "Include direct day/month clues, before/after relationships, gap clues (1-2 between), weekend/weekday constraints."
            },
            "Hard": {
                "time_period": "7 days with multiple sessions OR 8-12 months",
                "num_events": "8-10 events/people",
                "num_clues": "9-10 clues",
                "complexity": "Complex scheduling with multiple constraints and conditional logic",
                "guidelines": "Use complex scheduling with multiple constraints, conditional logic, and require multi-step deduction."
            }
        },
        "main_category": "Puzzles & Seating Arrangements"
    },

    "Multi-Variable Puzzle": {
        "expert_role": "You are an expert question setter for {exam_name}, specializing in Multi-Variable Puzzles.",
        "instructions": """Generate a '{difficulty}' difficulty Multi-Variable Puzzle question.

**DIFFICULTY GUIDELINES FOR {difficulty}:**
{difficulty_guidelines}

**QUESTION STRUCTURE:**
1. Present 4-7 people with multiple attributes (name, profession, city, hobby, etc.)
2. Provide 5-10 clues about their attributes and relationships
3. Ask a specific question about the matching
4. Provide 5 options (A, B, C, D, E)
5. Include a detailed explanation with complete matching table

**CRITICAL RULES:**
1. All clues must be necessary and consistent
2. Must have UNIQUE solution only
3. Use clear, unambiguous language
4. Include both direct and relative attribute clues
5. Distractors should be actual people in the arrangement""",
        "difficulty_parameters": {
            "Easy": {
                "num_people": "4-5 people",
                "num_variables": "3 variables (Name + 2 attributes)",
                "num_clues": "5-6 clues",
                "complexity": "Simple direct links and basic negative constraints",
                "guidelines": "Use straightforward direct links, simple negative links, and basic attribute connections."
            },
            "Medium": {
                "num_people": "5-6 people",
                "num_variables": "4 variables (Name + 3 attributes)",
                "num_clues": "7-8 clues",
                "complexity": "Mix of direct links, negative constraints, and chain connections",
                "guidelines": "Include direct links, negative constraints, chain connections, and require connecting 2-3 clues for deduction."
            },
            "Hard": {
                "num_people": "6-7 people",
                "num_variables": "4-5 variables (Name + 3-4 attributes)",
                "num_clues": "9-10 clues",
                "complexity": "Complex multi-step reasoning with multiple interlocking clues",
                "guidelines": "Use complex multi-step reasoning, multiple interlocking clues, and require connecting 3-4 clues for deduction."
            }
        },
        "main_category": "Puzzles & Seating Arrangements"
    },

    "Syllogisms": {
        "expert_role": "You are an expert question setter for {exam_name}, specializing in Syllogisms.",
        "instructions": """Generate a '{difficulty}' difficulty Syllogisms question.

**DIFFICULTY GUIDELINES FOR {difficulty}:**
{difficulty_guidelines}

**QUESTION STRUCTURE:**
1. Present 2-3 statements (premises)
2. Ask which conclusion follows from the given statements
3. Provide 5 options (A, B, C, D, E)
4. Include a detailed explanation with Venn diagram analysis

**CRITICAL RULES:**
1. Use standard logical forms (All A are B, Some A are B, No A are B)
2. All statements must be clear and unambiguous
3. Only one conclusion should follow logically
4. Use banking/finance/business vocabulary
5. Include Venn diagram explanation""",
        "difficulty_parameters": {
            "Easy": {
                "num_statements": "2 statements",
                "statement_types": "All/Some/No statements only",
                "conclusion_types": "Direct conclusion from premises",
                "guidelines": "Use simple All/Some/No statements with direct conclusions."
            },
            "Medium": {
                "num_statements": "2-3 statements",
                "statement_types": "Mix of All/Some/No statements",
                "conclusion_types": "Direct or indirect conclusion",
                "guidelines": "Include mix of statement types with both direct and indirect conclusions."
            },
            "Hard": {
                "num_statements": "3 statements",
                "statement_types": "Complex All/Some/No statements with exceptions",
                "conclusion_types": "Complex multi-step conclusion",
                "guidelines": "Use complex statements with exceptions and require multi-step logical reasoning."
            }
        },
        "main_category": "Verbal & Logical Reasoning"
    },

    "Blood Relations": {
        "expert_role": "You are an expert question setter for {exam_name}, specializing in Blood Relations.",
        "instructions": """Generate a '{difficulty}' difficulty Blood Relations question.

**DIFFICULTY GUIDELINES FOR {difficulty}:**
{difficulty_guidelines}

**QUESTION STRUCTURE:**
1. Present 3-6 people with their relationships
2. Provide 2-4 clues about their family relationships
3. Ask a specific question about the relationship
4. Provide 5 options (A, B, C, D, E)
5. Include a detailed explanation with family tree diagram

**CRITICAL RULES:**
1. Use standard relationship terms (father, mother, son, daughter, brother, sister, etc.)
2. All relationships must be clear and unambiguous
3. Gender consistency is critical
4. Use clear, unambiguous language
5. Include family tree diagram in explanation""",
        "difficulty_parameters": {
            "Easy": {
                "num_people": "3-4 people",
                "num_clues": "2-3 clues",
                "complexity": "Simple direct relationships",
                "guidelines": "Use simple direct relationships with clear family terms."
            },
            "Medium": {
                "num_people": "4-5 people",
                "num_clues": "3-4 clues",
                "complexity": "Mix of direct and indirect relationships",
                "guidelines": "Include mix of direct and indirect relationships requiring 2-step reasoning."
            },
            "Hard": {
                "num_people": "5-6 people",
                "num_clues": "4-5 clues",
                "complexity": "Complex multi-step relationships",
                "guidelines": "Use complex multi-step relationships requiring 3-4 step reasoning."
            }
        },
        "main_category": "Verbal & Logical Reasoning"
    },

    "Coding-Decoding": {
        "expert_role": "You are an expert question setter for {exam_name}, specializing in Coding-Decoding.",
        "instructions": """Generate a '{difficulty}' difficulty Coding-Decoding question.

**DIFFICULTY GUIDELINES FOR {difficulty}:**
{difficulty_guidelines}

**QUESTION STRUCTURE:**
1. Present 2-4 examples of coded words/numbers
2. Ask to find the code for a given word/number
3. Provide 5 options (A, B, C, D, E)
4. Include a detailed explanation with pattern identification

**CRITICAL RULES:**
1. Pattern must be consistent and logical
2. All examples must follow the same pattern
3. Use clear, unambiguous language
4. Include step-by-step pattern explanation
5. Test the pattern on all examples""",
        "difficulty_parameters": {
            "Easy": {
                "num_examples": "2 examples",
                "pattern_types": "Simple letter/number substitution",
                "complexity": "Direct one-to-one mapping",
                "guidelines": "Use simple letter/number substitution with direct mapping."
            },
            "Medium": {
                "num_examples": "3 examples",
                "pattern_types": "Mix of letter/number substitution and position-based coding",
                "complexity": "Two-step pattern application",
                "guidelines": "Include mix of substitution and position-based coding requiring 2-step reasoning."
            },
            "Hard": {
                "num_examples": "4 examples",
                "pattern_types": "Complex multi-step coding with multiple rules",
                "complexity": "Multi-step pattern application",
                "guidelines": "Use complex multi-step coding with multiple rules requiring 3-4 step reasoning."
            }
        },
        "main_category": "Verbal & Logical Reasoning"
    },

    "Direction Sense": {
        "expert_role": "You are an expert question setter for {exam_name}, specializing in Direction Sense.",
        "instructions": """Generate a '{difficulty}' difficulty Direction Sense question.

**DIFFICULTY GUIDELINES FOR {difficulty}:**
{difficulty_guidelines}

**QUESTION STRUCTURE:**
1. Present a person starting from a point and moving in different directions
2. Provide 3-6 movement clues
3. Ask about the final position or direction
4. Provide 5 options (A, B, C, D, E)
5. Include a detailed explanation with path diagram

**CRITICAL RULES:**
1. Use standard directions (North, South, East, West, Northeast, etc.)
2. All movements must be clear and unambiguous
3. Include coordinate system in explanation
4. Use clear, unambiguous language
5. Include path diagram with coordinate system""",
        "difficulty_parameters": {
            "Easy": {
                "num_movements": "3-4 movements",
                "direction_types": "Basic North, South, East, West only",
                "complexity": "Simple straight-line movements",
                "guidelines": "Use basic directions with simple straight-line movements."
            },
            "Medium": {
                "num_movements": "4-5 movements",
                "direction_types": "Mix of basic and diagonal directions",
                "complexity": "Mix of straight-line and diagonal movements",
                "guidelines": "Include mix of basic and diagonal directions with both straight-line and diagonal movements."
            },
            "Hard": {
                "num_movements": "5-6 movements",
                "direction_types": "All directions including complex angles",
                "complexity": "Complex movements with multiple direction changes",
                "guidelines": "Use all directions including complex angles with multiple direction changes."
            }
        },
        "main_category": "Verbal & Logical Reasoning"
    },

    "Inequalities": {
        "expert_role": "You are an expert question setter for {exam_name}, specializing in Inequalities.",
        "instructions": """Generate a '{difficulty}' difficulty Inequalities question.

**DIFFICULTY GUIDELINES FOR {difficulty}:**
{difficulty_guidelines}

**QUESTION STRUCTURE:**
1. Present 3-5 variables with inequality statements
2. Provide 2-4 conclusions to evaluate
3. Ask which conclusion(s) follow from the given statements
4. Provide 5 options (A, B, C, D, E)
5. Include a detailed explanation with step-by-step verification

**CRITICAL RULES:**
1. Use standard inequality symbols (>, <, ≥, ≤, =)
2. All statements must be clear and unambiguous
3. Maintain transitivity (A > B, B > C → A > C)
4. Use clear, unambiguous language
5. Include step-by-step verification of each conclusion""",
        "difficulty_parameters": {
            "Easy": {
                "num_variables": "3-4 variables",
                "num_statements": "2-3 statements",
                "complexity": "Simple direct inequalities",
                "guidelines": "Use simple direct inequalities with clear relationships."
            },
            "Medium": {
                "num_variables": "4-5 variables",
                "num_statements": "3-4 statements",
                "complexity": "Mix of direct and indirect inequalities",
                "guidelines": "Include mix of direct and indirect inequalities requiring 2-step reasoning."
            },
            "Hard": {
                "num_variables": "5-6 variables",
                "num_statements": "4-5 statements",
                "complexity": "Complex multi-step inequalities",
                "guidelines": "Use complex multi-step inequalities requiring 3-4 step reasoning."
            }
        },
        "main_category": "Verbal & Logical Reasoning"
    },

    "Data Sufficiency": {
        "expert_role": "You are an expert question setter for {exam_name}, specializing in Data Sufficiency.",
        "instructions": """Generate a '{difficulty}' difficulty Data Sufficiency question.

**DIFFICULTY GUIDELINES FOR {difficulty}:**
{difficulty_guidelines}

**QUESTION STRUCTURE:**
1. Present a question that needs to be answered
2. Provide two statements (I and II)
3. Ask which statement(s) is/are sufficient to answer the question
4. Provide 5 options (A, B, C, D, E)
5. Include a detailed explanation with analysis of each statement

**CRITICAL RULES:**
1. Question must be clear and specific
2. Statements must be independent and clear
3. Only one answer should be correct
4. Use banking/finance/business vocabulary
5. Include detailed analysis of each statement""",
        "difficulty_parameters": {
            "Easy": {
                "question_type": "Direct numerical question (age, quantity, price, simple calculation)",
                "statement_types": "Simple direct statements",
                "complexity": "One statement sufficient",
                "guidelines": "Use simple direct statements with one statement sufficient."
            },
            "Medium": {
                "question_type": "Moderate numerical question (percentage, ratio, average)",
                "statement_types": "Mix of direct and indirect statements",
                "complexity": "Both statements together sufficient",
                "guidelines": "Include mix of direct and indirect statements requiring both together."
            },
            "Hard": {
                "question_type": "Complex numerical question (compound interest, complex calculation)",
                "statement_types": "Complex statements with multiple variables",
                "complexity": "Complex reasoning required",
                "guidelines": "Use complex statements with multiple variables requiring complex reasoning."
            }
        },
        "main_category": "Analytical & Critical Reasoning"
    },

    "Input-Output": {
        "expert_role": "You are an expert question setter for {exam_name}, specializing in Input-Output.",
        "instructions": """Generate a '{difficulty}' difficulty Input-Output question.

**DIFFICULTY GUIDELINES FOR {difficulty}:**
{difficulty_guidelines}

**QUESTION STRUCTURE:**
1. Present 2-4 examples of input-output transformations
2. Ask to find the output for a given input
3. Provide 5 options (A, B, C, D, E)
4. Include a detailed explanation with pattern identification

**CRITICAL RULES:**
1. Pattern must be consistent and logical
2. All examples must follow the same pattern
3. Use clear, unambiguous language
4. Include step-by-step pattern explanation
5. Test the pattern on all examples""",
        "difficulty_parameters": {
            "Easy": {
                "num_elements": "5-6 elements (words and/or numbers)",
                "num_examples": "2 examples",
                "complexity": "Simple one-step transformation",
                "guidelines": "Use simple one-step transformation with clear pattern."
            },
            "Medium": {
                "num_elements": "6-7 elements (words and/or numbers)",
                "num_examples": "3 examples",
                "complexity": "Two-step transformation",
                "guidelines": "Include two-step transformation requiring 2-step reasoning."
            },
            "Hard": {
                "num_elements": "7-8 elements (words and/or numbers)",
                "num_examples": "4 examples",
                "complexity": "Multi-step transformation",
                "guidelines": "Use multi-step transformation requiring 3-4 step reasoning."
            }
        },
        "main_category": "Analytical & Critical Reasoning"
    },

    "Statement & Inference": {
        "expert_role": "You are an expert question setter for {exam_name}, specializing in Statement & Inference.",
        "instructions": """Generate a '{difficulty}' difficulty Statement & Inference question.

**DIFFICULTY GUIDELINES FOR {difficulty}:**
{difficulty_guidelines}

**QUESTION STRUCTURE:**
1. Present 3-5 statements (facts/observations)
2. Provide 3-5 inferences to evaluate
3. Ask which inference(s) follow from the given statements
4. Provide 5 options (A, B, C, D, E)
5. Include a detailed explanation with analysis of each inference

**CRITICAL RULES:**
1. Statements must be clear and factual
2. Inferences must be logical and reasonable
3. Only one answer should be correct
4. Use banking/finance/business vocabulary
5. Include detailed analysis of each inference""",
        "difficulty_parameters": {
            "Easy": {
                "statement_length": "3-4 lines with clear, direct facts",
                "num_inferences": "3 inferences",
                "complexity": "Direct inference from statements",
                "guidelines": "Use clear, direct facts with direct inference."
            },
            "Medium": {
                "statement_length": "4-5 lines with mix of direct and indirect facts",
                "num_inferences": "4 inferences",
                "complexity": "Indirect inference requiring 2-step reasoning",
                "guidelines": "Include mix of direct and indirect facts requiring 2-step reasoning."
            },
            "Hard": {
                "statement_length": "5-6 lines with complex, indirect facts",
                "num_inferences": "5 inferences",
                "complexity": "Complex inference requiring 3-4 step reasoning",
                "guidelines": "Use complex, indirect facts requiring 3-4 step reasoning."
            }
        },
        "main_category": "Analytical & Critical Reasoning"
    },

    "Statement & Assumption": {
        "expert_role": "You are an expert question setter for {exam_name}, specializing in Statement & Assumption.",
        "instructions": """Generate a '{difficulty}' difficulty Statement & Assumption question.

**DIFFICULTY GUIDELINES FOR {difficulty}:**
{difficulty_guidelines}

**QUESTION STRUCTURE:**
1. Present a statement (policy/decision/announcement)
2. Provide 3-5 assumptions to evaluate
3. Ask which assumption(s) is/are implicit in the statement
4. Provide 5 options (A, B, C, D, E)
5. Include a detailed explanation with analysis of each assumption

**CRITICAL RULES:**
1. Statement must be clear and specific
2. Assumptions must be logical and reasonable
3. Only one answer should be correct
4. Use banking/finance/business vocabulary
5. Include detailed analysis of each assumption""",
        "difficulty_parameters": {
            "Easy": {
                "statement_type": "Simple policy/decision/announcement with clear intent",
                "num_assumptions": "3 assumptions",
                "complexity": "Direct assumption from statement",
                "guidelines": "Use simple policy/decision with direct assumption."
            },
            "Medium": {
                "statement_type": "Moderate policy/decision/announcement with mixed intent",
                "num_assumptions": "4 assumptions",
                "complexity": "Indirect assumption requiring 2-step reasoning",
                "guidelines": "Include moderate policy/decision requiring 2-step reasoning."
            },
            "Hard": {
                "statement_type": "Complex policy/decision/announcement with ambiguous intent",
                "num_assumptions": "5 assumptions",
                "complexity": "Complex assumption requiring 3-4 step reasoning",
                "guidelines": "Use complex policy/decision requiring 3-4 step reasoning."
            }
        },
        "main_category": "Analytical & Critical Reasoning"
    },

    "Statement & Course of Action": {
        "expert_role": "You are an expert question setter for {exam_name}, specializing in Statement & Course of Action.",
        "instructions": """Generate a '{difficulty}' difficulty Statement & Course of Action question.

**DIFFICULTY GUIDELINES FOR {difficulty}:**
{difficulty_guidelines}

**QUESTION STRUCTURE:**
1. Present a statement (problem/situation/issue)
2. Provide 3-5 courses of action to evaluate
3. Ask which course(s) of action should be taken
4. Provide 5 options (A, B, C, D, E)
5. Include a detailed explanation with evaluation of each course of action

**CRITICAL RULES:**
1. Statement must be clear and specific
2. Courses of action must be practical and reasonable
3. Only one answer should be correct
4. Use banking/finance/business vocabulary
5. Include detailed evaluation of each course of action""",
        "difficulty_parameters": {
            "Easy": {
                "statement_type": "Clear problem with obvious solution direction",
                "num_courses": "3 courses of action",
                "complexity": "Direct course of action from problem",
                "guidelines": "Use clear problem with direct course of action."
            },
            "Medium": {
                "statement_type": "Moderate problem with mixed solution directions",
                "num_courses": "4 courses of action",
                "complexity": "Indirect course of action requiring 2-step reasoning",
                "guidelines": "Include moderate problem requiring 2-step reasoning."
            },
            "Hard": {
                "statement_type": "Complex problem with ambiguous solution directions",
                "num_courses": "5 courses of action",
                "complexity": "Complex course of action requiring 3-4 step reasoning",
                "guidelines": "Use complex problem requiring 3-4 step reasoning."
            }
        },
        "main_category": "Analytical & Critical Reasoning"
    },

    "Strengthening/Weakening Arguments": {
        "expert_role": "You are an expert question setter for {exam_name}, specializing in Strengthening/Weakening Arguments.",
        "instructions": """Generate a '{difficulty}' difficulty Strengthening/Weakening Arguments question.

**DIFFICULTY GUIDELINES FOR {difficulty}:**
{difficulty_guidelines}

**QUESTION STRUCTURE:**
1. Present an argument (claim with reasoning)
2. Provide 3-5 options to evaluate
3. Ask which option strengthens/weakens the argument
4. Provide 5 options (A, B, C, D, E)
5. Include a detailed explanation with analysis of each option

**CRITICAL RULES:**
1. Argument must be clear and specific
2. Options must be logical and reasonable
3. Only one answer should be correct
4. Use banking/finance/business vocabulary
5. Include detailed analysis of each option""",
        "difficulty_parameters": {
            "Easy": {
                "argument_type": "Simple claim with clear reasoning",
                "argument_length": "2-3 lines, straightforward logic",
                "complexity": "Direct strengthening/weakening",
                "guidelines": "Use simple claim with direct strengthening/weakening."
            },
            "Medium": {
                "argument_type": "Moderate claim with mixed reasoning",
                "argument_length": "3-4 lines, moderate logic",
                "complexity": "Indirect strengthening/weakening requiring 2-step reasoning",
                "guidelines": "Include moderate claim requiring 2-step reasoning."
            },
            "Hard": {
                "argument_type": "Complex claim with ambiguous reasoning",
                "argument_length": "4-5 lines, complex logic",
                "complexity": "Complex strengthening/weakening requiring 3-4 step reasoning",
                "guidelines": "Use complex claim requiring 3-4 step reasoning."
            }
        },
        "main_category": "Analytical & Critical Reasoning"
    }
}
