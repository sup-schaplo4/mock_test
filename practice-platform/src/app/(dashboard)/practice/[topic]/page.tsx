'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useAuth } from '@/components/auth/auth-provider'
import { QuestionCard } from '@/components/question/question-card'
import { Question } from '@/types/question'
import { supabase } from '@/lib/supabase'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ArrowLeft, RotateCcw } from 'lucide-react'

export default function PracticePage() {
  const params = useParams()
  const router = useRouter()
  const { user, loading } = useAuth()
  const [questions, setQuestions] = useState<Question[]>([])
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [loadingQuestions, setLoadingQuestions] = useState(true)
  const [sessionComplete, setSessionComplete] = useState(false)
  const [sessionStats, setSessionStats] = useState({
    totalQuestions: 0,
    correctAnswers: 0,
    totalTimeSpent: 0,
    accuracy: 0
  })

  const topic = params.topic as string

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login')
    }
  }, [user, loading, router])

  useEffect(() => {
    if (user) {
      fetchQuestions()
    }
  }, [user, topic])

  const fetchQuestions = async () => {
    try {
      setLoadingQuestions(true)
      
      // Map topic to subject
      const subjectMapping: { [key: string]: string } = {
        'syllogism': 'Reasoning',
        'ratios': 'Quantitative',
        'reading-comprehension': 'English',
        'current-affairs': 'General_Awareness'
      }

      const subject = subjectMapping[topic] || 'Reasoning'
      
      const { data, error } = await supabase
        .from('questions')
        .select('*')
        .eq('subject', subject)
        .eq('topic', topic)
        .limit(10) // Limit to 10 questions for practice session

      if (error) {
        console.error('Error fetching questions:', error)
        return
      }

      setQuestions(data || [])
    } catch (error) {
      console.error('Error fetching questions:', error)
    } finally {
      setLoadingQuestions(false)
    }
  }

  const handleAnswer = async (selectedAnswer: string, timeSpent: number) => {
    if (!user) return

    const currentQuestion = questions[currentQuestionIndex]
    const isCorrect = selectedAnswer === currentQuestion.correct_answer

    // Record the attempt
    try {
      const { error } = await supabase
        .from('question_attempts')
        .insert({
          user_id: user.id,
          question_id: currentQuestion.id,
          selected_answer: selectedAnswer,
          is_correct: isCorrect,
          time_spent: timeSpent
        })

      if (error) {
        console.error('Error recording attempt:', error)
      }
    } catch (error) {
      console.error('Error recording attempt:', error)
    }

    // Update session stats
    setSessionStats(prev => ({
      totalQuestions: prev.totalQuestions + 1,
      correctAnswers: prev.correctAnswers + (isCorrect ? 1 : 0),
      totalTimeSpent: prev.totalTimeSpent + timeSpent,
      accuracy: Math.round(((prev.correctAnswers + (isCorrect ? 1 : 0)) / (prev.totalQuestions + 1)) * 100)
    }))
  }

  const handleNext = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1)
    } else {
      setSessionComplete(true)
    }
  }

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(prev => prev - 1)
    }
  }

  const handleRestart = () => {
    setCurrentQuestionIndex(0)
    setSessionComplete(false)
    setSessionStats({
      totalQuestions: 0,
      correctAnswers: 0,
      totalTimeSpent: 0,
      accuracy: 0
    })
  }

  const handleBackToDashboard = () => {
    router.push('/dashboard')
  }

  if (loading || loadingQuestions) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    )
  }

  if (!user) {
    return null
  }

  if (questions.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6 text-center">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
              No Questions Available
            </h2>
            <p className="text-gray-600 dark:text-gray-300 mb-4">
              No questions found for this topic. Please try another topic.
            </p>
            <Button onClick={handleBackToDashboard}>
              Back to Dashboard
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (sessionComplete) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl font-bold">Session Complete!</CardTitle>
            <CardDescription>
              Great job on completing the practice session
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">
                  {sessionStats.accuracy}%
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Accuracy</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-green-600 dark:text-green-400">
                  {sessionStats.correctAnswers}/{sessionStats.totalQuestions}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Correct</div>
              </div>
            </div>
            
            <div className="text-center">
              <div className="text-lg font-semibold text-gray-900 dark:text-white">
                {Math.floor(sessionStats.totalTimeSpent / 60)}m {sessionStats.totalTimeSpent % 60}s
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Total Time</div>
            </div>

            <div className="space-y-3">
              <Button onClick={handleRestart} className="w-full">
                <RotateCcw className="w-4 h-4 mr-2" />
                Practice Again
              </Button>
              <Button onClick={handleBackToDashboard} variant="outline" className="w-full">
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Dashboard
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  const currentQuestion = questions[currentQuestionIndex]

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="bg-white dark:bg-gray-800 shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-4">
            <Button
              onClick={handleBackToDashboard}
              variant="outline"
              className="flex items-center space-x-2"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Dashboard</span>
            </Button>
            
            <div className="text-sm text-gray-600 dark:text-gray-400">
              {topic.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </div>
          </div>
        </div>
      </div>

      <QuestionCard
        question={currentQuestion}
        questionNumber={currentQuestionIndex + 1}
        totalQuestions={questions.length}
        onAnswer={handleAnswer}
        onNext={handleNext}
        onPrevious={handlePrevious}
        canGoNext={currentQuestionIndex < questions.length - 1}
        canGoPrevious={currentQuestionIndex > 0}
      />
    </div>
  )
}
