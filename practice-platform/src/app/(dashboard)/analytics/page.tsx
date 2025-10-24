'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/components/auth/auth-provider'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ArrowLeft, TrendingUp, Clock, Target, BarChart3 } from 'lucide-react'

interface AnalyticsData {
  totalQuestions: number
  correctAnswers: number
  totalTimeSpent: number
  accuracy: number
  averageTimePerQuestion: number
  currentStreak: number
  longestStreak: number
  subjectBreakdown: {
    subject: string
    questions: number
    accuracy: number
    timeSpent: number
  }[]
  recentActivity: {
    date: string
    subject: string
    topic: string
    questions: number
    accuracy: number
  }[]
}

export default function AnalyticsPage() {
  const { user, loading } = useAuth()
  const router = useRouter()
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null)
  const [loadingAnalytics, setLoadingAnalytics] = useState(true)

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login')
    }
  }, [user, loading, router])

  useEffect(() => {
    if (user) {
      fetchAnalytics()
    }
  }, [user])

  const fetchAnalytics = async () => {
    try {
      setLoadingAnalytics(true)
      
      // Mock data for now - in real app, fetch from Supabase
      const mockAnalytics: AnalyticsData = {
        totalQuestions: 156,
        correctAnswers: 132,
        totalTimeSpent: 7200, // 2 hours
        accuracy: 85,
        averageTimePerQuestion: 46,
        currentStreak: 8,
        longestStreak: 15,
        subjectBreakdown: [
          { subject: 'Reasoning', questions: 45, accuracy: 89, timeSpent: 1800 },
          { subject: 'Quantitative', questions: 38, accuracy: 82, timeSpent: 2280 },
          { subject: 'English', questions: 35, accuracy: 86, timeSpent: 1750 },
          { subject: 'General Awareness', questions: 38, accuracy: 84, timeSpent: 1370 }
        ],
        recentActivity: [
          { date: '2024-01-15', subject: 'Reasoning', topic: 'Syllogism', questions: 10, accuracy: 90 },
          { date: '2024-01-14', subject: 'Quantitative', topic: 'Ratios', questions: 8, accuracy: 75 },
          { date: '2024-01-13', subject: 'English', topic: 'Reading Comprehension', questions: 12, accuracy: 83 },
          { date: '2024-01-12', subject: 'General Awareness', topic: 'Current Affairs', questions: 15, accuracy: 87 }
        ]
      }
      
      setAnalytics(mockAnalytics)
    } catch (error) {
      console.error('Error fetching analytics:', error)
    } finally {
      setLoadingAnalytics(false)
    }
  }

  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    if (hours > 0) {
      return `${hours}h ${minutes}m`
    }
    return `${minutes}m`
  }

  if (loading || loadingAnalytics) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    )
  }

  if (!user || !analytics) {
    return null
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-6">
            <div className="flex items-center space-x-4">
              <Button
                onClick={() => router.push('/dashboard')}
                variant="outline"
                className="flex items-center space-x-2"
              >
                <ArrowLeft className="w-4 h-4" />
                <span>Back to Dashboard</span>
              </Button>
              
              <div className="w-12 h-12 bg-purple-500 rounded-lg flex items-center justify-center">
                <BarChart3 className="w-6 h-6 text-white" />
              </div>
              
              <div>
                <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                  Analytics
                </h1>
                <p className="text-gray-600 dark:text-gray-300">
                  Track your progress and performance
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Overview Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Questions</CardTitle>
              <Target className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{analytics.totalQuestions}</div>
              <p className="text-xs text-muted-foreground">
                Questions attempted
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Accuracy</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{analytics.accuracy}%</div>
              <p className="text-xs text-muted-foreground">
                {analytics.correctAnswers} correct answers
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Time Spent</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatTime(analytics.totalTimeSpent)}</div>
              <p className="text-xs text-muted-foreground">
                Total practice time
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Current Streak</CardTitle>
              <Target className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{analytics.currentStreak}</div>
              <p className="text-xs text-muted-foreground">
                Best: {analytics.longestStreak} consecutive
              </p>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Subject Breakdown */}
          <Card>
            <CardHeader>
              <CardTitle>Performance by Subject</CardTitle>
              <CardDescription>
                Your accuracy and time spent across different subjects
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {analytics.subjectBreakdown.map((subject, index) => (
                  <div key={subject.subject} className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className={`w-3 h-3 rounded-full ${
                        index === 0 ? 'bg-blue-500' :
                        index === 1 ? 'bg-green-500' :
                        index === 2 ? 'bg-purple-500' : 'bg-orange-500'
                      }`}></div>
                      <span className="font-medium">{subject.subject}</span>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold">{subject.accuracy}%</div>
                      <div className="text-sm text-gray-500">{subject.questions} questions</div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Recent Activity */}
          <Card>
            <CardHeader>
              <CardTitle>Recent Activity</CardTitle>
              <CardDescription>
                Your latest practice sessions
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {analytics.recentActivity.map((activity, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <div>
                      <div className="font-medium">{activity.subject} - {activity.topic}</div>
                      <div className="text-sm text-gray-500">{activity.date}</div>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold">{activity.accuracy}%</div>
                      <div className="text-sm text-gray-500">{activity.questions} questions</div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Performance Insights */}
        <Card className="mt-8">
          <CardHeader>
            <CardTitle>Performance Insights</CardTitle>
            <CardDescription>
              AI-powered insights to help you improve
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                <div className="text-2xl font-bold text-green-600 dark:text-green-400 mb-2">
                  Strong Areas
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-300">
                  Reasoning (89% accuracy)
                </div>
              </div>
              
              <div className="text-center p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
                <div className="text-2xl font-bold text-yellow-600 dark:text-yellow-400 mb-2">
                  Focus Areas
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-300">
                  Quantitative (82% accuracy)
                </div>
              </div>
              
              <div className="text-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <div className="text-2xl font-bold text-blue-600 dark:text-blue-400 mb-2">
                  Avg. Time
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-300">
                  {analytics.averageTimePerQuestion}s per question
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
