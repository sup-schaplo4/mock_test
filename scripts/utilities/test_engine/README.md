Perfect! Let me summarize **ALL your requirements** before coding:

---

## **📋 COMPLETE REQUIREMENTS SUMMARY**

---

### **1. Difficulty Distribution within Topics** ✅
- **Method:** Apply section's overall difficulty ratio proportionally to each topic
- **Example:** 
  - Section needs: 60 questions (25% Easy, 50% Medium, 25% Hard)
  - Topic "Linear Seating" needs: 8 questions
  - Engine picks: 2 Easy, 4 Medium, 2 Hard from Linear Seating

---

### **2. Data Interpretation (DI) Sets - Special Handling** ✅

#### **A. Atomic Units:**
- Treat entire DI set as one unit (all 5 questions together)
- Cannot split a set

#### **B. Difficulty Footprint Matching (Smart Selection):**

**Algorithm:**
1. **Get Candidate Sets:** Find all DI sets available
2. **Calculate Footprint:** For each set, count difficulty of individual questions:
   - Set A: {Easy: 2, Medium: 2, Hard: 1} = 5 questions
   - Set B: {Easy: 1, Medium: 1, Hard: 3} = 5 questions
   - Set C: {Easy: 0, Medium: 0, Hard: 5} = 5 questions

3. **Check Current Needs:** Section needs: {Easy: 10, Medium: 15, Hard: 5}

4. **Filter Valid Sets:** Keep only sets where footprint ≤ needs for ALL difficulties:
   - Set A (1 Hard) ✅ Valid (1 ≤ 5)
   - Set B (3 Hard) ✅ Valid (3 ≤ 5)
   - Set C (5 Hard) ✅ Valid (5 ≤ 5)
   - Set D (6 Hard) ❌ Invalid (6 > 5) - REMOVED

5. **Random Selection:** Pick one valid set randomly (e.g., Set B)

6. **Update Quotas:** Subtract Set B's footprint:
   - New needs: {Easy: 9, Medium: 14, Hard: 2}

7. **Repeat:** Continue for next DI set or fill remaining with standalone questions

#### **C. Difficulty Source:**
- Use **question-level difficulty** (not set-level) to calculate footprint
- Ignore set-level difficulty field

---

### **3. Topic Count Validation** ✅
- Validate: `sum(topic_distribution.values()) == total_questions`
- Hard fail with clear error if mismatch

---

### **4. Seeded Random Selection** ✅
- Use `test_id` as seed for random number generator
- Same test_id always generates same questions
- Different test_ids generate different questions
- Ensures fairness and reproducibility

---

### **5. No Duplicate Tracking (Phase 1)** ✅
- Don't track user history across tests
- Each test is independent
- Same user can see same questions in different tests (acceptable)

---

### **6. Source Files - Different JSON Structures** ✅

You have **5 different master file structures:**

#### **A. English Master** (`english_master.json`):
```json
{
  "metadata": {...},
  "questions": [
    {
      "question_id": "ENG_0001",
      "question": "...",
      "options": {...},
      "correct_answer": "D",
      "difficulty": "Medium",
      "topic": "Reading_Comprehension",
      "subject": "English"
    }
  ]
}
```
- **Key Fields:** `topic`, `difficulty`, `question_id`
- **Total Questions:** 290
- **Topics:** Reading_Comprehension, Fill_in_the_Blanks, Vocabulary, Error_Spotting, Sentence_Correction, Para_Jumbles

---

#### **B. General Awareness Master** (`general_awareness_master.json`):
```json
{
  "metadata": {...},
  "questions": [
    {
      "question_id": "GA_00001",
      "question": "...",
      "options": {...},
      "correct_answer": "B",
      "difficulty": "Easy",
      "topic": "Appointments",
      "category": "Current_Affairs",
      "subject": "General_Awareness"
    }
  ]
}
```
- **Key Fields:** `topic`, `category`, `difficulty`, `question_id`
- **Total Questions:** 803
- **Topics:** 38 different topics (Fiscal_Policy, Economic_Updates, Government_Schemes, etc.)

---

#### **C. Reasoning Master** (`reasoning_master.json`):
```json
{
  "metadata": {...},
  "questions": [
    {
      "question_id": "BR_001",
      "question": "...",
      "options": {...},
      "correct_answer": "B",
      "difficulty": "Easy",
      "topic": "Blood Relations",
      "reasoning_topic": "Blood Relations",
      "main_category": "Verbal & Logical Reasoning",
      "subject": "Reasoning"
    }
  ]
}
```
- **Key Fields:** `topic` or `reasoning_topic`, `difficulty`, `question_id`
- **Total Questions:** 604
- **Topics:** 18 different topics (Blood Relations, Linear Seating, Syllogisms, etc.)

---

#### **D. Arithmetic Master** (`arithmetic_master.json`):
```json
{
  "category": "Arithmetic",
  "statistics": {...},
  "questions": [
    {
      "question_id": "ARIT_0001",
      "question": "...",
      "options": {...},
      "correct_answer": "A",
      "difficulty": "Medium",
      "topic": "Averages",
      "sub_topic": "Effect of adding/removing values",
      "subject": "Arithmetic"
    }
  ]
}
```
- **Key Fields:** `topic`, `sub_topic`, `difficulty`, `question_id`
- **Total Questions:** 100
- **Topics:** 8 topics (Averages, Simple & Compound Interest, Percentage, etc.)

---

#### **E. Data Interpretation Master** (`di_master.json`):
```json
{
  "category": "Data Interpretation",
  "statistics": {...},
  "questions": [
    {
      "di_set_id": "DI_BAR_CHART_001",
      "topic": "Bar Chart - Sales Revenue Analysis",
      "difficulty": "Easy",  // ← SET LEVEL (IGNORE THIS)
      "data_source": {...},
      "questions": [
        {
          "question_id": "DI_BAR_001_Q1",
          "question": "...",
          "options": {...},
          "correct_answer": "A",
          "difficulty": "Easy",  // ← QUESTION LEVEL (USE THIS)
          "explanation": "..."
        },
        {
          "question_id": "DI_BAR_001_Q2",
          "difficulty": "Easy"  // ← QUESTION LEVEL (USE THIS)
        }
        // ... 3 more questions (total 5 per set)
      ]
    }
  ]
}
```
- **Key Fields:** `di_set_id`, `topic` (at set level), `difficulty` (at question level)
- **Total Questions:** 25 sets × 5 questions = 125 questions
- **Topics:** 25 different topics (all variations of Bar Chart, Pie Chart, Line Chart, Table, Caselet)
- **Special:** Each set is atomic (all 5 questions together)

---

### **7. DI Topic Selection** ✅
- **Option C Selected:** Use generic "Data Interpretation" tag
- All DI sets are treated equally regardless of specific chart type
- Engine randomly picks any valid DI sets that fit the difficulty footprint
- **Alternative (if needed later):** Can specify exact types in blueprint like:
  ```json
  "Bar Chart": 1,
  "Pie Chart": 1
  ```

---

### **8. Blueprint Storage** ✅
- **Location:** `data/blueprints/`
- **Naming:** `RBI_P1_MOCK_01.json`, `RBI_P1_MOCK_02.json`, etc.
- One JSON file per test blueprint

---

### **9. Blueprint Topic Distribution Format** ✅
- **Option A Selected:** Simple count format
```json
"topic_distribution": {
  "Linear Seating Arrangement": 8,
  "Syllogisms": 5,
  "Data Interpretation": 2  // 2 sets = 10 questions
}
```
- Engine automatically applies section's difficulty ratio to each topic
- Simpler and less error-prone

---

### **10. Output Format - Grouped by Section** ✅
```json
{
  "test_id": "RBI_P1_MOCK_01",
  "test_name": "RBI Grade B - Phase 1 Mock Test #1",
  "description": "Full-length mock test as per latest pattern",
  "total_questions": 200,
  "total_marks": 200,
  "duration_minutes": 120,
  "negative_marking": 0.25,
  "generation_date": "2025-10-07T...",
  "sections": [
    {
      "section_id": "GA",
      "section_name": "General Awareness",
      "total_questions": 80,
      "questions": [/* 80 question objects */]
    },
    {
      "section_id": "LR",
      "section_name": "Logical Reasoning",
      "total_questions": 60,
      "questions": [/* 60 question objects */]
    },
    {
      "section_id": "ENG",
      "section_name": "English Language",
      "total_questions": 30,
      "questions": [/* 30 question objects */]
    },
    {
      "section_id": "QUANT",
      "section_name": "Quantitative Aptitude",
      "total_questions": 30,
      "questions": [/* 30 questions including 2 DI sets */]
    }
  ]
}
```

---

### **11. Question Metadata in Output** ✅
- **Include ALL metadata** in output JSON:
  - `correct_answer` ✅
  - `explanation` ✅
  - `difficulty` ✅
  - `topic` ✅
  - All other fields from master files ✅

- **Frontend Responsibility:**
  - Hide sensitive fields during test (correct_answer, explanation, difficulty)
  - Reveal everything after submission for review

---

### **12. Validation & Error Handling** ✅
- **Hard fail** with clear error messages if:
  - Master file doesn't exist
  - Not enough questions for a topic
  - Not enough questions for a difficulty level
  - Topic counts don't sum to total_questions
  - DI set doesn't have exactly 5 questions
  - Invalid blueprint structure

- **Error Message Format:**
  ```
  ❌ ERROR: Insufficient questions for section "Reasoning"
     Topic: "Linear Seating Arrangement"
     Required: 8 Easy questions
     Available: 5 Easy questions
     Missing: 3 Easy questions
  ```

---

### **13. Master File Locations** ✅
```
data/generated/master_questions/
├── english_master.json          (290 questions)
├── general_awareness_master.json (803 questions)
├── reasoning_master.json         (604 questions)
├── arithmetic_master.json        (100 questions)
└── di_master.json                (25 sets = 125 questions)
```

---

### **14. Special DI Handling in Quant Section** ✅
- Quant section uses **2 source files:**
  - `arithmetic_master.json` (standalone questions)
  - `di_master.json` (DI sets)

- **Blueprint Example:**
```json
{
  "section_name": "Quantitative Aptitude",
  "total_questions": 30,
  "source_files": ["arithmetic_master.json", "di_master.json"],
  "topic_distribution": {
    "Data Interpretation": 2,  // 2 sets = 10 questions
    "Averages": 5,
    "Percentage": 5,
    "Profit & Loss": 5,
    "Ratio & Proportion": 5
  },
  "difficulty_distribution": {
    "Easy": 10,
    "Medium": 15,
    "Hard": 5
  }
}
```

- **Engine Logic:**
  1. First, pick 2 DI sets (10 questions) using footprint matching
  2. Update difficulty quotas after DI sets
  3. Fill remaining 20 questions from arithmetic topics

---

## **🎯 What You Need Me to Code:**

### **Phase 1: Core Engine**
1. ✅ **Blueprint Validator** - Validates blueprint JSON structure
2. ✅ **Master File Loader** - Loads and parses all 5 master file formats
3. ✅ **Question Selector** - Selects questions based on topic/difficulty
4. ✅ **DI Set Selector** - Implements footprint matching algorithm
5. ✅ **Test Assembler** - Combines everything into final test JSON
6. ✅ **Main Engine** - Orchestrates the entire process

### **Phase 2: Sample Blueprints**
1. ✅ `RBI_P1_MOCK_01.json` - First mock test blueprint
2. ✅ `RBI_P1_MOCK_02.json` - Second mock test blueprint
3. ✅ `RBI_P1_MOCK_03.json` - Third mock test blueprint

### **Phase 3: Output**
1. ✅ Generated test JSON files in `data/generated/tests/`
2. ✅ Validation reports
3. ✅ Statistics (questions used, difficulty distribution, etc.)

---

File Strucutre 
rbi-test-generator/
│
├── data/
│   ├── generated/
│   │   ├── master_questions/
│   │   │   ├── english_master_question_bank.json              (290 questions - your existing file)
│   │   │   ├── general_awareness_master_question_bank.json    (803 questions - your existing file)
│   │   │   ├── reasoning_master_question_bank.json            (604 questions - your existing file)
│   │   │   ├── arithmetic_master._question_bankjson           (100 questions - your existing file)
│   │   │   └── di_master_question_bank.json                   (25 sets = 125 questions - your existing file)
│   │   │
│   │   └── tests/                               (Generated tests will be saved here)
│   │       ├── RBI_P1_MOCK_01.json              (Generated by engine)
│   │       ├── RBI_P1_MOCK_02.json              (Generated by engine)
│   │       └── RBI_P1_MOCK_03.json              (Generated by engine)
│   │
│   └── blueprints/                              (Test blueprints/configurations)
│       ├── RBI_P1_MOCK_01.json                  (Blueprint for Mock 1)
│       ├── RBI_P1_MOCK_02.json                  (Blueprint for Mock 2)
│       └── RBI_P1_MOCK_03.json                  (Blueprint for Mock 3)
│
├── src/
│   └── test_engine/
│       ├── __init__.py
│       ├── blueprint_validator.py               (Validates blueprint structure)
│       ├── master_loader.py                     (Loads all master files)
│       ├── question_selector.py                 (Selects questions by topic/difficulty)
│       ├── di_selector.py                       (DI set footprint matching)
│       ├── test_assembler.py                    (Assembles final test)
│       └── main_engine.py                       (Main orchestrator)
│
├── scripts/
│   └── generate_mocks.py                        (Script to generate all 3 mocks)
│
├── logs/
│   ├── mock_01_generation.log                   (Generation logs)
│   ├── mock_02_generation.log
│   └── mock_03_generation.log
│
└── requirements.txt                             (Python dependencies)
