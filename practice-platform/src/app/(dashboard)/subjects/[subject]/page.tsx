'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useAuth } from '@/components/auth/auth-provider'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { ArrowLeft, Play, Target, Clock, CheckCircle } from 'lucide-react'
import Link from 'next/link'

interface Topic {
  id: string
  name: string
  description: string
  totalQuestions: number
  completedQuestions: number
  accuracy: number
  averageTime: number
}

const subjectInfo = {
  reasoning: {
    name: 'Reasoning',
    description: 'Logical reasoning, syllogisms, puzzles, and analytical thinking',
    color: 'bg-blue-500',
    topics: [
      { id: 'syllogism', name: 'Syllogism', description: 'Logical reasoning with premises and conclusions' },
      { id: 'blood-relations', name: 'Blood Relations', description: 'Family relationship puzzles' },
      { id: 'direction-sense', name: 'Direction Sense', description: 'Spatial reasoning and directions' },
      { id: 'seating-arrangement', name: 'Seating Arrangement', description: 'Linear and circular seating puzzles' },
      { id: 'puzzles', name: 'Puzzles', description: 'Various logical puzzles and brain teasers' },
      { id: 'coding-decoding', name: 'Coding Decoding', description: 'Pattern recognition and code breaking' }
    ]
  },
  quantitative: {
    name: 'Quantitative Aptitude',
    description: 'Mathematics, arithmetic, algebra, and data interpretation',
    color: 'bg-green-500',
    topics: [
      { id: 'ratios', name: 'Ratios & Proportions', description: 'Ratio calculations and proportional relationships' },
      { id: 'percentages', name: 'Percentages', description: 'Percentage calculations and applications' },
      { id: 'profit-loss', name: 'Profit & Loss', description: 'Business mathematics and financial calculations' },
      { id: 'time-speed', name: 'Time, Speed & Distance', description: 'Motion and velocity problems' },
      { id: 'time-work', name: 'Time & Work', description: 'Work efficiency and time management' },
      { id: 'data-interpretation', name: 'Data Interpretation', description: 'Charts, graphs, and statistical analysis' }
    ]
  },
  english: {
    name: 'English Language',
    description: 'Reading comprehension, grammar, and vocabulary',
    color: 'bg-purple-500',
    topics: [
      { id: 'reading-comprehension', name: 'Reading Comprehension', description: 'Passage analysis and inference' },
      { id: 'grammar', name: 'Grammar', description: 'Sentence structure and grammatical rules' },
      { id: 'vocabulary', name: 'Vocabulary', description: 'Word meanings and usage' },
      { id: 'sentence-completion', name: 'Sentence Completion', description: 'Filling in the blanks' },
      { id: 'para-jumbles', name: 'Para Jumbles', description: 'Sentence rearrangement' }
    ]
  },
  'general-awareness': {
    name: 'General Awareness',
    description: 'Current affairs, banking, economics, and general knowledge',
    color: 'bg-orange-500',
    topics: [
      { id: 'current-affairs', name: 'Current Affairs', description: 'Recent events and news' },
      { id: 'banking', name: 'Banking & Finance', description: 'Banking sector and financial systems' },
      { id: 'economics', name: 'Economics', description: 'Economic concepts and indicators' },
      { id: 'government-schemes', name: 'Government Schemes', description: 'Government policies and programs' },
      { id: 'history', name: 'History & Culture', description: 'Indian history and cultural heritage' },
      { id: 'geography', name: 'Geography', description: 'Physical and human geography' }
    ]
  }
}

export default function SubjectPage() {
  const params = useParams()
  const router = useRouter()
  const { user, loading } = useAuth()
  const [topics, setTopics] = useState<Topic[]>([])
  const [loadingTopics, setLoadingTopics] = useState(true)

  const subject = params.subject as string
  const subjectData = subjectInfo[subject as keyof typeof subjectInfo]

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login')
    }
  }, [user, loading, router])

  useEffect(() => {
    if (user && subjectData) {
      fetchTopics()
    }
  }, [user, subject])

  const fetchTopics = async () => {
    try {
      setLoadingTopics(true)
      
      // Mock data for now - in real app, fetch from Supabase
      const mockTopics: Topic[] = subjectData.topics.map(topic => ({
        id: topic.id,
        name: topic.name,
        description: topic.description,
        totalQuestions: Math.floor(Math.random() * 50) + 20,
        completedQuestions: Math.floor(Math.random() * 20),
        accuracy: Math.floor(Math.random() * 40) + 60,
        averageTime: Math.floor(Math.random() * 60) + 30
      }))
      
      setTopics(mockTopics)
    } catch (error) {
      console.error('Error fetching topics:', error)
    } finally {
      setLoadingTopics(false)
    }
  }

  if (loading || loadingTopics) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    )
  }

  if (!user || !subjectData) {
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
                <span>Back</span>
              </Button>
              
              <div className={`w-12 h-12 ${subjectData.color} rounded-lg flex items-center justify-center`}>
                <Target className="w-6 h-6 text-white" />
              </div>
              
              <div>
                <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                  {subjectData.name}
                </h1>
                <p className="text-gray-600 dark:text-gray-300">
                  {subjectData.description}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Overview Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Questions</CardTitle>
              <Target className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {topics.reduce((sum, topic) => sum + topic.totalQuestions, 0)}
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Completed</CardTitle>
              <CheckCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {topics.reduce((sum, topic) => sum + topic.completedQuestions, 0)}
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Average Accuracy</CardTitle>
              <Target className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {topics.length > 0 
                  ? Math.round(topics.reduce((sum, topic) => sum + topic.accuracy, 0) / topics.length)
                  : 0}%
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Avg. Time</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {topics.length > 0 
                  ? Math.round(topics.reduce((sum, topic) => sum + topic.averageTime, 0) / topics.length)
                  : 0}s
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Topics Grid */}
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
            Choose a Topic
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {topics.map((topic) => {
              const progress = topic.totalQuestions > 0 
                ? (topic.completedQuestions / topic.totalQuestions) * 100 
                : 0

              return (
                <Card key={topic.id} className="hover:shadow-lg transition-shadow duration-200">
                  <CardHeader>
                    <CardTitle className="text-lg">{topic.name}</CardTitle>
                    <CardDescription>{topic.description}</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Progress */}
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                          Progress
                        </span>
                        <span className="text-sm text-gray-500 dark:text-gray-400">
                          {topic.completedQuestions}/{topic.totalQuestions}
                        </span>
                      </div>
                      <Progress value={progress} className="h-2" />
                    </div>

                    {/* Stats */}
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <div className="text-gray-500 dark:text-gray-400">Accuracy</div>
                        <div className="font-semibold">{topic.accuracy}%</div>
                      </div>
                      <div>
                        <div className="text-gray-500 dark:text-gray-400">Avg. Time</div>
                        <div className="font-semibold">{topic.averageTime}s</div>
                      </div>
                    </div>

                    {/* Action Button */}
                    <Link href={`/practice/${topic.id}`}>
                      <Button className="w-full">
                        <Play className="w-4 h-4 mr-2" />
                        {topic.completedQuestions > 0 ? 'Continue' : 'Start Practice'}
                      </Button>
                    </Link>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
