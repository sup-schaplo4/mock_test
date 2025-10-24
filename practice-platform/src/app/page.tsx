import Link from 'next/link'
import { BookOpen, Calculator, Brain, Globe } from 'lucide-react'

const subjects = [
  {
    id: 'reasoning',
    name: 'Reasoning',
    description: 'Logical reasoning, syllogisms, puzzles, and analytical thinking',
    icon: Brain,
    color: 'bg-blue-500',
    totalQuestions: 1200,
  },
  {
    id: 'quantitative',
    name: 'Quantitative Aptitude',
    description: 'Mathematics, arithmetic, algebra, and data interpretation',
    icon: Calculator,
    color: 'bg-green-500',
    totalQuestions: 800,
  },
  {
    id: 'english',
    name: 'English Language',
    description: 'Reading comprehension, grammar, and vocabulary',
    icon: BookOpen,
    color: 'bg-purple-500',
    totalQuestions: 600,
  },
  {
    id: 'general-awareness',
    name: 'General Awareness',
    description: 'Current affairs, banking, economics, and general knowledge',
    icon: Globe,
    color: 'bg-orange-500',
    totalQuestions: 1000,
  },
]

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      <div className="container mx-auto px-4 py-16">
        {/* Header */}
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold text-gray-900 dark:text-white mb-4">
            Argon Test
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
            Master competitive exams with our comprehensive question bank. 
            Practice, track progress, and excel in your preparation.
          </p>
        </div>

        {/* Subjects Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 max-w-6xl mx-auto">
          {subjects.map((subject) => {
            const Icon = subject.icon
            return (
              <Link
                key={subject.id}
                href={`/subjects/${subject.id}`}
                className="group"
              >
                <div className="subject-card">
                  <div className={`w-16 h-16 ${subject.color} rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300`}>
                    <Icon className="w-8 h-8 text-white" />
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                    {subject.name}
                  </h3>
                  <p className="text-gray-600 dark:text-gray-300 text-sm mb-4">
                    {subject.description}
                  </p>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500 dark:text-gray-400">
                      {subject.totalQuestions.toLocaleString()} questions
                    </span>
                    <div className="w-2 h-2 bg-blue-500 rounded-full group-hover:scale-150 transition-transform duration-300"></div>
                  </div>
                </div>
              </Link>
            )
          })}
        </div>

        {/* Features Section */}
        <div className="mt-24 max-w-4xl mx-auto">
          <h2 className="text-3xl font-bold text-center text-gray-900 dark:text-white mb-12">
            Why Choose Argon Test?
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center mx-auto mb-4">
                <BookOpen className="w-8 h-8 text-blue-600 dark:text-blue-400" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                Comprehensive Coverage
              </h3>
              <p className="text-gray-600 dark:text-gray-300">
                Thousands of questions covering all topics and difficulty levels
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center mx-auto mb-4">
                <Calculator className="w-8 h-8 text-green-600 dark:text-green-400" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                Detailed Analytics
              </h3>
              <p className="text-gray-600 dark:text-gray-300">
                Track your progress with detailed performance analytics
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-purple-100 dark:bg-purple-900 rounded-full flex items-center justify-center mx-auto mb-4">
                <Brain className="w-8 h-8 text-purple-600 dark:text-purple-400" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                Smart Practice
              </h3>
              <p className="text-gray-600 dark:text-gray-300">
                Adaptive learning with personalized recommendations
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
