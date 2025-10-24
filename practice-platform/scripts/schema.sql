-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create subjects table
CREATE TABLE IF NOT EXISTS subjects (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  name VARCHAR(100) NOT NULL UNIQUE,
  description TEXT,
  icon VARCHAR(50),
  color VARCHAR(20),
  total_questions INTEGER DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create topics table
CREATE TABLE IF NOT EXISTS topics (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  subject_id UUID REFERENCES subjects(id) ON DELETE CASCADE,
  name VARCHAR(100) NOT NULL,
  description TEXT,
  total_questions INTEGER DEFAULT 0,
  difficulty_distribution JSONB DEFAULT '{"Easy": 0, "Medium": 0, "Hard": 0}',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(subject_id, name)
);

-- Create questions table
CREATE TABLE IF NOT EXISTS questions (
  id VARCHAR(100) PRIMARY KEY,
  question TEXT NOT NULL,
  options JSONB NOT NULL,
  correct_answer VARCHAR(1) NOT NULL CHECK (correct_answer IN ('A', 'B', 'C', 'D', 'E')),
  explanation TEXT NOT NULL,
  difficulty VARCHAR(10) NOT NULL CHECK (difficulty IN ('Easy', 'Medium', 'Hard')),
  topic VARCHAR(100) NOT NULL,
  sub_topic VARCHAR(100),
  subject VARCHAR(50) NOT NULL CHECK (subject IN ('Reasoning', 'Quantitative', 'English', 'General_Awareness')),
  main_category VARCHAR(100) NOT NULL,
  concept_tags TEXT[] DEFAULT '{}',
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create question_attempts table
CREATE TABLE IF NOT EXISTS question_attempts (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  question_id VARCHAR(100) NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
  selected_answer VARCHAR(1) NOT NULL CHECK (selected_answer IN ('A', 'B', 'C', 'D', 'E')),
  is_correct BOOLEAN NOT NULL,
  time_spent INTEGER NOT NULL, -- in seconds
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(user_id, question_id, created_at)
);

-- Create user_progress table
CREATE TABLE IF NOT EXISTS user_progress (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  subject VARCHAR(50) NOT NULL,
  topic VARCHAR(100) NOT NULL,
  total_questions INTEGER DEFAULT 0,
  correct_answers INTEGER DEFAULT 0,
  total_time_spent INTEGER DEFAULT 0, -- in seconds
  last_attempted_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(user_id, subject, topic)
);

-- Create user_analytics table
CREATE TABLE IF NOT EXISTS user_analytics (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  total_questions_attempted INTEGER DEFAULT 0,
  total_correct_answers INTEGER DEFAULT 0,
  total_time_spent INTEGER DEFAULT 0, -- in seconds
  average_time_per_question DECIMAL(10,2) DEFAULT 0,
  accuracy_percentage DECIMAL(5,2) DEFAULT 0,
  current_streak INTEGER DEFAULT 0,
  longest_streak INTEGER DEFAULT 0,
  last_activity_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(user_id)
);

-- Create practice_sessions table
CREATE TABLE IF NOT EXISTS practice_sessions (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  subject VARCHAR(50) NOT NULL,
  topic VARCHAR(100) NOT NULL,
  questions TEXT[] NOT NULL, -- array of question IDs
  current_question_index INTEGER DEFAULT 0,
  start_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  end_time TIMESTAMP WITH TIME ZONE,
  is_completed BOOLEAN DEFAULT FALSE,
  total_score INTEGER DEFAULT 0,
  total_time_spent INTEGER DEFAULT 0, -- in seconds
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_questions_subject ON questions(subject);
CREATE INDEX IF NOT EXISTS idx_questions_topic ON questions(topic);
CREATE INDEX IF NOT EXISTS idx_questions_difficulty ON questions(difficulty);
CREATE INDEX IF NOT EXISTS idx_question_attempts_user_id ON question_attempts(user_id);
CREATE INDEX IF NOT EXISTS idx_question_attempts_question_id ON question_attempts(question_id);
CREATE INDEX IF NOT EXISTS idx_question_attempts_created_at ON question_attempts(created_at);
CREATE INDEX IF NOT EXISTS idx_user_progress_user_id ON user_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_user_progress_subject ON user_progress(subject);
CREATE INDEX IF NOT EXISTS idx_user_analytics_user_id ON user_analytics(user_id);
CREATE INDEX IF NOT EXISTS idx_practice_sessions_user_id ON practice_sessions(user_id);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_subjects_updated_at BEFORE UPDATE ON subjects FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_topics_updated_at BEFORE UPDATE ON topics FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_questions_updated_at BEFORE UPDATE ON questions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_question_attempts_updated_at BEFORE UPDATE ON question_attempts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_progress_updated_at BEFORE UPDATE ON user_progress FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_analytics_updated_at BEFORE UPDATE ON user_analytics FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_practice_sessions_updated_at BEFORE UPDATE ON practice_sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default subjects
INSERT INTO subjects (name, description, icon, color) VALUES
('Reasoning', 'Logical reasoning, syllogisms, puzzles, and analytical thinking', 'Brain', 'bg-blue-500'),
('Quantitative', 'Mathematics, arithmetic, algebra, and data interpretation', 'Calculator', 'bg-green-500'),
('English', 'Reading comprehension, grammar, and vocabulary', 'BookOpen', 'bg-purple-500'),
('General_Awareness', 'Current affairs, banking, economics, and general knowledge', 'Globe', 'bg-orange-500')
ON CONFLICT (name) DO NOTHING;

-- Enable Row Level Security (RLS)
ALTER TABLE questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE question_attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_analytics ENABLE ROW LEVEL SECURITY;
ALTER TABLE practice_sessions ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
-- Questions are readable by all authenticated users
CREATE POLICY "Questions are viewable by authenticated users" ON questions
  FOR SELECT USING (auth.role() = 'authenticated');

-- Question attempts are only accessible by the user who made them
CREATE POLICY "Users can view their own question attempts" ON question_attempts
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own question attempts" ON question_attempts
  FOR INSERT WITH CHECK (auth.uid() = user_id);

-- User progress is only accessible by the user
CREATE POLICY "Users can view their own progress" ON user_progress
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own progress" ON user_progress
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own progress" ON user_progress
  FOR UPDATE USING (auth.uid() = user_id);

-- User analytics is only accessible by the user
CREATE POLICY "Users can view their own analytics" ON user_analytics
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own analytics" ON user_analytics
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own analytics" ON user_analytics
  FOR UPDATE USING (auth.uid() = user_id);

-- Practice sessions are only accessible by the user
CREATE POLICY "Users can view their own practice sessions" ON practice_sessions
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own practice sessions" ON practice_sessions
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own practice sessions" ON practice_sessions
  FOR UPDATE USING (auth.uid() = user_id);
