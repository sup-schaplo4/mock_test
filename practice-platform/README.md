# Argon Test - Practice Platform

A modern web application for practicing competitive exam questions with a Brilliant-inspired UI/UX. Built with Next.js 14, Supabase, and TypeScript.

## Features

- **Comprehensive Question Bank**: Thousands of questions across Reasoning, Quantitative, English, and General Awareness
- **Real-time Analytics**: Track time spent per question, accuracy, and performance trends
- **Progress Tracking**: Monitor your progress across different subjects and topics
- **Modern UI/UX**: Clean, responsive design inspired by Brilliant
- **Authentication**: Secure user accounts with Supabase Auth
- **Practice Sessions**: Timed practice sessions with detailed explanations

## Tech Stack

- **Frontend**: Next.js 14, React, TypeScript, Tailwind CSS
- **Backend**: Supabase (PostgreSQL, Auth, Real-time)
- **UI Components**: Shadcn/ui, Lucide React icons
- **State Management**: React Context + Zustand
- **Deployment**: Vercel

## Prerequisites

- Node.js 18+ 
- npm or yarn
- Supabase account

## Setup Instructions

### 1. Install Dependencies

```bash
npm install
```

### 2. Set up Supabase

1. Create a new project at [supabase.com](https://supabase.com)
2. Go to Settings > API to get your project URL and anon key
3. Copy `env.example` to `.env.local` and fill in your Supabase credentials:

```bash
cp env.example .env.local
```

Update `.env.local` with your Supabase credentials:
```env
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

### 3. Set up Database

1. Go to your Supabase project dashboard
2. Navigate to SQL Editor
3. Run the SQL schema from `scripts/schema.sql` to create all necessary tables

### 4. Import Questions

Run the migration script to import questions from your existing JSON files:

```bash
npm run migrate-questions
```

This will:
- Parse all JSON question files from the `data/` directory
- Organize questions by subject and topic
- Upload them to your Supabase database

### 5. Start Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Project Structure

```
src/
├── app/                    # Next.js app directory
│   ├── (auth)/            # Authentication pages
│   ├── (dashboard)/       # Protected dashboard pages
│   └── globals.css        # Global styles
├── components/            # React components
│   ├── auth/              # Authentication components
│   ├── question/          # Question-related components
│   └── ui/                # Reusable UI components
├── lib/                   # Utility functions
│   ├── supabase.ts        # Supabase client
│   └── utils.ts           # Helper functions
├── types/                 # TypeScript type definitions
└── hooks/                 # Custom React hooks
```

## Database Schema

### Tables

- **questions**: Stores all practice questions with metadata
- **question_attempts**: Records user attempts with timing data
- **user_progress**: Tracks user progress by subject/topic
- **user_analytics**: Aggregated user performance data
- **practice_sessions**: Active practice session data

### Key Features

- Row Level Security (RLS) for data protection
- Automatic timestamps with triggers
- Optimized indexes for performance
- JSON fields for flexible question options and metadata

## Deployment

### Deploy to Vercel

1. Push your code to GitHub
2. Connect your repository to Vercel
3. Add environment variables in Vercel dashboard
4. Deploy

### Custom Domain Setup

1. Add your domain in Vercel project settings
2. Update DNS records to point to Vercel
3. Update `NEXT_PUBLIC_APP_URL` in environment variables
4. Update Supabase redirect URLs for production

## Features in Detail

### Question Practice

- **Timer Tracking**: Precise timing for each question
- **Immediate Feedback**: Instant correct/incorrect feedback
- **Detailed Explanations**: Comprehensive explanations for each answer
- **Progress Indicators**: Visual progress through question sets
- **Navigation**: Easy navigation between questions

### Analytics Dashboard

- **Performance Metrics**: Accuracy, time spent, streaks
- **Subject Breakdown**: Performance by subject and topic
- **Trend Analysis**: Performance over time
- **Weak Area Identification**: Topics needing more practice

### User Experience

- **Responsive Design**: Works on all device sizes
- **Dark Mode**: Toggle between light and dark themes
- **Smooth Animations**: Framer Motion for polished interactions
- **Accessibility**: Keyboard navigation and screen reader support

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For questions or issues, please open a GitHub issue or contact the development team.
