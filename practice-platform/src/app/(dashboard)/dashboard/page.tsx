'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/components/auth/auth-provider'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { BookOpen, Calculator, Brain, Globe, TrendingUp, Clock, Target } from 'lucide-react'
import Link from 'next/link'

interface UserStats {
  totalQuestions: number
  correctAnswers: number
  totalTimeSpent: number
  accuracy: number
  currentStreak: number
}

const subjects = [
  {
    id: 'reasoning',
    name: 'Reasoning',
    description: 'Logical reasoning, syllogisms, puzzles, and analytical thinking',
    icon: Brain,
    color: 'bg-blue-500',
    href: '/subjects/reasoning'
  },
  {
    id: 'quantitative',
    name: 'Quantitative Aptitude',
    description: 'Mathematics, arithmetic, algebra, and data interpretation',
    icon: Calculator,
    color: 'bg-green-500',
    href: '/subjects/quantitative'
  },
  {
    id: 'english',
    name: 'English Language',
    description: 'Reading comprehension, grammar, and vocabulary',
    icon: BookOpen,
    color: 'bg-purple-500',
    href: '/subjects/english'
  },
  {
    id: 'general-awareness',
    name: 'General Awareness',
    description: 'Current affairs, banking, economics, and general knowledge',
    icon: Globe,
    color: 'bg-orange-500',
    href: '/subjects/general-awareness'
  },
]

export default function DashboardPage() {
  const { user, loading } = useAuth()
  const router = useRouter()
  const [stats, setStats] = useState<UserStats>({
    totalQuestions: 0,
    correctAnswers: 0,
    totalTimeSpent: 0,
    accuracy: 0,
    currentStreak: 0
  })

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login')
    }
  }, [user, loading, router])

  // TODO: Fetch user stats from Supabase
  useEffect(() => {
    // Mock data for now
    setStats({
      totalQuestions: 45,
      correctAnswers: 38,
      totalTimeSpent: 1800, // 30 minutes
      accuracy: 84,
      currentStreak: 7
    })
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    )
  }

  if (!user) {
    return null
  }

  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    if (hours > 0) {
      return `${hours}h ${minutes}m`
    }
    return `${minutes}m`
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                Welcome back, {user.email?.split('@')[0]}!
              </h1>
              <p className="text-gray-600 dark:text-gray-300">
                Ready to continue your practice?
              </p>
            </div>
            <Button
              onClick={() => router.push('/login')}
              variant="outline"
            >
              Sign Out
            </Button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Questions Attempted</CardTitle>
              <Target className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.totalQuestions}</div>
              <p className="text-xs text-muted-foreground">
                +12 from last week
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Accuracy</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.accuracy}%</div>
              <p className="text-xs text-muted-foreground">
                {stats.correctAnswers} correct out of {stats.totalQuestions}
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Time Spent</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatTime(stats.totalTimeSpent)}</div>
              <p className="text-xs text-muted-foreground">
                Average: {Math.round(stats.totalTimeSpent / stats.totalQuestions)}s per question
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Current Streak</CardTitle>
              <Target className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.currentStreak}</div>
              <p className="text-xs text-muted-foreground">
                consecutive correct answers
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Subjects Grid */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
            Choose a Subject
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {subjects.map((subject) => {
              const Icon = subject.icon
              return (
                <Link key={subject.id} href={subject.href}>
                  <Card className="hover:shadow-lg transition-shadow duration-200 cursor-pointer">
                    <CardHeader>
                      <div className={`w-12 h-12 ${subject.color} rounded-lg flex items-center justify-center mb-4`}>
                        <Icon className="w-6 h-6 text-white" />
                      </div>
                      <CardTitle className="text-lg">{subject.name}</CardTitle>
                      <CardDescription>{subject.description}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-500 dark:text-gray-400">
                          Start practicing
                        </span>
                        <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              )
            })}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Recent Activity</CardTitle>
              <CardDescription>Your latest practice sessions</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-sm">Reasoning - Syllogism</span>
                  </div>
                  <span className="text-xs text-gray-500">2 hours ago</span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                    <span className="text-sm">Quantitative - Ratios</span>
                  </div>
                  <span className="text-xs text-gray-500">1 day ago</span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                    <span className="text-sm">English - Reading Comprehension</span>
                  </div>
                  <span className="text-xs text-gray-500">2 days ago</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
              <CardDescription>Jump back into your practice</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <Button className="w-full justify-start" variant="outline">
                  <BookOpen className="w-4 h-4 mr-2" />
                  Continue Last Session
                </Button>
                <Button className="w-full justify-start" variant="outline">
                  <Target className="w-4 h-4 mr-2" />
                  Practice Weak Areas
                </Button>
                <Button className="w-full justify-start" variant="outline">
                  <TrendingUp className="w-4 h-4 mr-2" />
                  View Analytics
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
