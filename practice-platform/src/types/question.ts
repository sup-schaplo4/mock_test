export interface Question {
  id: string;
  question: string;
  options: {
    A: string;
    B: string;
    C: string;
    D: string;
    E: string;
  };
  correct_answer: string;
  explanation: string;
  difficulty: 'Easy' | 'Medium' | 'Hard';
  topic: string;
  sub_topic?: string;
  subject: 'Reasoning' | 'Quantitative' | 'English' | 'General_Awareness';
  main_category: string;
  concept_tags?: string[];
  metadata?: {
    generated_by?: string;
    generation_date?: string;
    reviewed?: boolean;
    estimated_time?: string;
    batch_number?: number;
    api_cost?: number;
    question_number?: number;
  };
}

export interface QuestionAttempt {
  id: string;
  user_id: string;
  question_id: string;
  selected_answer: string;
  is_correct: boolean;
  time_spent: number; // in seconds
  created_at: string;
  updated_at: string;
}

export interface UserProgress {
  id: string;
  user_id: string;
  subject: string;
  topic: string;
  total_questions: number;
  correct_answers: number;
  total_time_spent: number;
  last_attempted_at: string;
  created_at: string;
  updated_at: string;
}

export interface Subject {
  id: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  total_questions: number;
}

export interface Topic {
  id: string;
  subject_id: string;
  name: string;
  description: string;
  total_questions: number;
  difficulty_distribution: {
    Easy: number;
    Medium: number;
    Hard: number;
  };
}
