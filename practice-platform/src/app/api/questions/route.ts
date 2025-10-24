import { NextRequest, NextResponse } from 'next/server'
import { supabase } from '@/lib/supabase'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const subject = searchParams.get('subject')
    const topic = searchParams.get('topic')
    const limit = searchParams.get('limit') || '10'

    let query = supabase
      .from('questions')
      .select('*')
      .limit(parseInt(limit))

    if (subject) {
      query = query.eq('subject', subject)
    }

    if (topic) {
      query = query.eq('topic', topic)
    }

    const { data, error } = await query

    if (error) {
      return NextResponse.json({ error: error.message }, { status: 500 })
    }

    return NextResponse.json({ questions: data })
  } catch (error) {
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
