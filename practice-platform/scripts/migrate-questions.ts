import { createClient } from '@supabase/supabase-js'
import fs from 'fs'
import path from 'path'

// Supabase configuration
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY!

const supabase = createClient(supabaseUrl, supabaseServiceKey)

interface QuestionData {
  question_id: string
  question: string
  options: {
    A: string
    B: string
    C: string
    D: string
    E: string
  }
  correct_answer: string
  explanation: string
  difficulty: 'Easy' | 'Medium' | 'Hard'
  topic: string
  sub_topic?: string
  main_category: string
  subject: 'Reasoning' | 'Quantitative' | 'English' | 'General_Awareness'
  concept_tags?: string[]
  metadata?: any
}

// Subject mapping
const subjectMapping: { [key: string]: 'Reasoning' | 'Quantitative' | 'English' | 'General_Awareness' } = {
  'Reasoning': 'Reasoning',
  'Quantitative Aptitude': 'Quantitative',
  'Arithmetic': 'Quantitative',
  'English': 'English',
  'General Awareness': 'General_Awareness',
  'General_Awareness': 'General_Awareness'
}

// Topic mapping for better organization
const topicMapping: { [key: string]: string } = {
  'Ratio & Proportion': 'Ratios',
  'Syllogisms': 'Syllogism',
  'Reading_Comprehension': 'Reading Comprehension',
  'Current_Affairs': 'Current Affairs',
  'PIB_Press_Release': 'PIB Press Releases',
  'Fiscal_Policy': 'Fiscal Policy',
  'Economic_Updates': 'Economic Updates',
  'Government_Schemes': 'Government Schemes',
  'Economic_Indicators': 'Economic Indicators',
  'Banking_Sector': 'Banking Sector',
  'Monetary_Policy': 'Monetary Policy'
}

async function migrateQuestions() {
  console.log('Starting question migration...')

  // Read all question files
  const dataDir = path.join(__dirname, '../../data')
  
  // Quant questions
  const quantDir = path.join(dataDir, 'generated/quant_questions')
  const quantFiles = fs.readdirSync(quantDir).filter(file => file.endsWith('.json'))
  
  // Reasoning questions
  const reasoningDir = path.join(dataDir, 'generated/reasoning_questions')
  const reasoningFiles = fs.readdirSync(reasoningDir).filter(file => file.endsWith('.json'))
  
  // English questions
  const englishDir = path.join(dataDir, 'reference_questions/english')
  const englishFiles = fs.readdirSync(englishDir).filter(file => file.endsWith('.json'))
  
  // GA questions
  const gaFile = path.join(dataDir, 'reference_questions/general_awareness_master_question_bank.json')

  let totalQuestions = 0
  let successCount = 0
  let errorCount = 0

  // Process Quant questions
  for (const file of quantFiles) {
    try {
      const filePath = path.join(quantDir, file)
      const fileContent = fs.readFileSync(filePath, 'utf-8')
      const questions: QuestionData[] = JSON.parse(fileContent)
      
      console.log(`Processing ${file}: ${questions.length} questions`)
      
      for (const question of questions) {
        const processedQuestion = {
          id: question.question_id,
          question: question.question,
          options: question.options,
          correct_answer: question.correct_answer,
          explanation: question.explanation,
          difficulty: question.difficulty,
          topic: topicMapping[question.topic] || question.topic,
          sub_topic: question.sub_topic,
          subject: 'Quantitative' as const,
          main_category: question.main_category,
          concept_tags: question.concept_tags || [],
          metadata: question.metadata || {}
        }
        
        const { error } = await supabase
          .from('questions')
          .upsert(processedQuestion, { onConflict: 'id' })
        
        if (error) {
          console.error(`Error inserting question ${question.question_id}:`, error)
          errorCount++
        } else {
          successCount++
        }
        totalQuestions++
      }
    } catch (error) {
      console.error(`Error processing file ${file}:`, error)
      errorCount++
    }
  }

  // Process Reasoning questions
  for (const file of reasoningFiles) {
    try {
      const filePath = path.join(reasoningDir, file)
      const fileContent = fs.readFileSync(filePath, 'utf-8')
      const questions: QuestionData[] = JSON.parse(fileContent)
      
      console.log(`Processing ${file}: ${questions.length} questions`)
      
      for (const question of questions) {
        const processedQuestion = {
          id: question.question_id,
          question: question.question,
          options: question.options,
          correct_answer: question.correct_answer,
          explanation: question.explanation,
          difficulty: question.difficulty,
          topic: topicMapping[question.topic] || question.topic,
          sub_topic: question.sub_topic,
          subject: 'Reasoning' as const,
          main_category: question.main_category,
          concept_tags: question.concept_tags || [],
          metadata: question.metadata || {}
        }
        
        const { error } = await supabase
          .from('questions')
          .upsert(processedQuestion, { onConflict: 'id' })
        
        if (error) {
          console.error(`Error inserting question ${question.question_id}:`, error)
          errorCount++
        } else {
          successCount++
        }
        totalQuestions++
      }
    } catch (error) {
      console.error(`Error processing file ${file}:`, error)
      errorCount++
    }
  }

  // Process English questions
  for (const file of englishFiles) {
    try {
      const filePath = path.join(englishDir, file)
      const fileContent = fs.readFileSync(filePath, 'utf-8')
      const data = JSON.parse(fileContent)
      
      // Handle different English question formats
      const questions = data.questions || data
      const questionArray = Array.isArray(questions) ? questions : [questions]
      
      console.log(`Processing ${file}: ${questionArray.length} questions`)
      
      for (const question of questionArray) {
        if (!question.question_id) continue
        
        const processedQuestion = {
          id: question.question_id || question.id,
          question: question.questions || question.question,
          options: question.options,
          correct_answer: question.correct_answer,
          explanation: question.explanation,
          difficulty: question.difficulty || 'Medium',
          topic: topicMapping[question.topic] || question.topic || 'Reading Comprehension',
          sub_topic: question.sub_topic,
          subject: 'English' as const,
          main_category: question.main_category || 'English Language',
          concept_tags: question.concept_tags || [],
          metadata: question.metadata || {}
        }
        
        const { error } = await supabase
          .from('questions')
          .upsert(processedQuestion, { onConflict: 'id' })
        
        if (error) {
          console.error(`Error inserting question ${question.question_id}:`, error)
          errorCount++
        } else {
          successCount++
        }
        totalQuestions++
      }
    } catch (error) {
      console.error(`Error processing file ${file}:`, error)
      errorCount++
    }
  }

  // Process GA questions
  try {
    const fileContent = fs.readFileSync(gaFile, 'utf-8')
    const data = JSON.parse(fileContent)
    const questions = data.questions || []
    
    console.log(`Processing GA questions: ${questions.length} questions`)
    
    for (const question of questions) {
      if (!question.id) continue
      
      const processedQuestion = {
        id: question.id,
        question: question.questions || question.question,
        options: question.options,
        correct_answer: question.correct_answer,
        explanation: question.explanation,
        difficulty: question.difficulty || 'Medium',
        topic: topicMapping[question.topic] || question.topic || 'Current Affairs',
        sub_topic: question.sub_topic,
        subject: 'General_Awareness' as const,
        main_category: question.main_category || 'General Awareness',
        concept_tags: question.concept_tags || [],
        metadata: question.metadata || {}
      }
      
      const { error } = await supabase
        .from('questions')
        .upsert(processedQuestion, { onConflict: 'id' })
      
      if (error) {
        console.error(`Error inserting question ${question.id}:`, error)
        errorCount++
      } else {
        successCount++
      }
      totalQuestions++
    }
  } catch (error) {
    console.error(`Error processing GA file:`, error)
    errorCount++
  }

  console.log('\nMigration Summary:')
  console.log(`Total questions processed: ${totalQuestions}`)
  console.log(`Successfully migrated: ${successCount}`)
  console.log(`Errors: ${errorCount}`)
}

// Run migration
migrateQuestions().catch(console.error)
