'use client'

import { useState, useEffect } from 'react'
import { Question } from '@/types/question'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { formatTime, getDifficultyColor } from '@/lib/utils'
import { CheckCircle, XCircle, Clock, ArrowLeft, ArrowRight } from 'lucide-react'

interface QuestionCardProps {
  question: Question
  questionNumber: number
  totalQuestions: number
  onAnswer: (selectedAnswer: string, timeSpent: number) => void
  onNext: () => void
  onPrevious: () => void
  canGoNext: boolean
  canGoPrevious: boolean
}

export function QuestionCard({
  question,
  questionNumber,
  totalQuestions,
  onAnswer,
  onNext,
  onPrevious,
  canGoNext,
  canGoPrevious
}: QuestionCardProps) {
  const [selectedAnswer, setSelectedAnswer] = useState<string>('')
  const [timeSpent, setTimeSpent] = useState(0)
  const [isAnswered, setIsAnswered] = useState(false)
  const [showExplanation, setShowExplanation] = useState(false)
  const [startTime, setStartTime] = useState<number>(Date.now())

  // Timer effect
  useEffect(() => {
    const interval = setInterval(() => {
      setTimeSpent(Math.floor((Date.now() - startTime) / 1000))
    }, 1000)

    return () => clearInterval(interval)
  }, [startTime])

  // Reset when question changes
  useEffect(() => {
    setSelectedAnswer('')
    setIsAnswered(false)
    setShowExplanation(false)
    setTimeSpent(0)
    setStartTime(Date.now())
  }, [question.id])

  const handleAnswerSelect = (answer: string) => {
    if (isAnswered) return
    setSelectedAnswer(answer)
  }

  const handleSubmit = () => {
    if (!selectedAnswer || isAnswered) return
    
    setIsAnswered(true)
    setShowExplanation(true)
    onAnswer(selectedAnswer, timeSpent)
  }

  const handleNext = () => {
    if (canGoNext) {
      onNext()
    }
  }

  const handlePrevious = () => {
    if (canGoPrevious) {
      onPrevious()
    }
  }

  const isCorrect = selectedAnswer === question.correct_answer
  const progress = (questionNumber / totalQuestions) * 100

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Progress Bar */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Question {questionNumber} of {totalQuestions}
          </span>
          <div className="flex items-center space-x-2 text-sm text-gray-500 dark:text-gray-400">
            <Clock className="w-4 h-4" />
            <span>{formatTime(timeSpent)}</span>
          </div>
        </div>
        <Progress value={progress} className="h-2" />
      </div>

      {/* Question Card */}
      <Card className="question-card">
        <CardHeader>
          <div className="flex items-center justify-between mb-4">
            <div className={`px-3 py-1 rounded-full text-sm font-medium ${getDifficultyColor(question.difficulty)}`}>
              {question.difficulty}
            </div>
            <div className="text-sm text-gray-500 dark:text-gray-400">
              {question.topic}
            </div>
          </div>
          <CardTitle className="text-xl leading-relaxed">
            {question.question}
          </CardTitle>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* Options */}
          <div className="space-y-3">
            {Object.entries(question.options).map(([key, value]) => {
              let optionClass = 'option-button'
              
              if (isAnswered) {
                if (key === question.correct_answer) {
                  optionClass += ' correct'
                } else if (key === selectedAnswer && key !== question.correct_answer) {
                  optionClass += ' incorrect'
                }
              } else if (selectedAnswer === key) {
                optionClass += ' selected'
              }

              return (
                <button
                  key={key}
                  onClick={() => handleAnswerSelect(key)}
                  className={optionClass}
                  disabled={isAnswered}
                >
                  <div className="flex items-center space-x-3">
                    <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center ${
                      selectedAnswer === key 
                        ? 'border-blue-500 bg-blue-500 text-white' 
                        : 'border-gray-300 dark:border-gray-600'
                    }`}>
                      {isAnswered && key === question.correct_answer && (
                        <CheckCircle className="w-4 h-4 text-green-500" />
                      )}
                      {isAnswered && key === selectedAnswer && key !== question.correct_answer && (
                        <XCircle className="w-4 h-4 text-red-500" />
                      )}
                      {!isAnswered && selectedAnswer === key && (
                        <div className="w-2 h-2 bg-white rounded-full"></div>
                      )}
                    </div>
                    <span className="font-medium">{key}.</span>
                    <span className="flex-1">{value}</span>
                  </div>
                </button>
              )
            })}
          </div>

          {/* Submit Button */}
          {!isAnswered && (
            <div className="pt-4">
              <Button
                onClick={handleSubmit}
                disabled={!selectedAnswer}
                className="w-full"
                size="lg"
              >
                Submit Answer
              </Button>
            </div>
          )}

          {/* Explanation */}
          {showExplanation && (
            <div className="mt-6 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                Explanation:
              </h4>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                {question.explanation}
              </p>
            </div>
          )}

          {/* Navigation */}
          {isAnswered && (
            <div className="flex items-center justify-between pt-6 border-t dark:border-gray-700">
              <Button
                onClick={handlePrevious}
                disabled={!canGoPrevious}
                variant="outline"
                className="flex items-center space-x-2"
              >
                <ArrowLeft className="w-4 h-4" />
                <span>Previous</span>
              </Button>

              <div className="text-center">
                <div className={`text-lg font-semibold ${
                  isCorrect ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                }`}>
                  {isCorrect ? 'Correct!' : 'Incorrect'}
                </div>
                <div className="text-sm text-gray-500 dark:text-gray-400">
                  Time: {formatTime(timeSpent)}
                </div>
              </div>

              <Button
                onClick={handleNext}
                disabled={!canGoNext}
                className="flex items-center space-x-2"
              >
                <span>Next</span>
                <ArrowRight className="w-4 h-4" />
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
