export interface User {
  id: string;
  email: string;
  full_name?: string;
  avatar_url?: string;
  created_at: string;
  updated_at: string;
}

export interface UserAnalytics {
  id: string;
  user_id: string;
  total_questions_attempted: number;
  total_correct_answers: number;
  total_time_spent: number; // in seconds
  average_time_per_question: number;
  accuracy_percentage: number;
  current_streak: number;
  longest_streak: number;
  last_activity_at: string;
  created_at: string;
  updated_at: string;
}

export interface PracticeSession {
  id: string;
  user_id: string;
  subject: string;
  topic: string;
  questions: string[]; // question IDs
  current_question_index: number;
  start_time: string;
  end_time?: string;
  is_completed: boolean;
  total_score: number;
  total_time_spent: number;
}
