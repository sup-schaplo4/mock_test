# Deployment Guide

This guide will help you deploy the Argon Test practice platform to Vercel and configure your custom domain.

## Prerequisites

- GitHub account
- Vercel account
- Domain registrar access (for argon-test.in)
- Supabase project set up

## Step 1: Push to GitHub

1. Initialize git repository in your project:
```bash
cd practice-platform
git init
git add .
git commit -m "Initial commit"
```

2. Create a new repository on GitHub
3. Push your code:
```bash
git remote add origin https://github.com/yourusername/practice-platform.git
git branch -M main
git push -u origin main
```

## Step 2: Deploy to Vercel

1. Go to [vercel.com](https://vercel.com) and sign in
2. Click "New Project"
3. Import your GitHub repository
4. Configure project settings:
   - Framework Preset: Next.js
   - Root Directory: practice-platform
   - Build Command: `npm run build`
   - Output Directory: `.next`

## Step 3: Configure Environment Variables

In Vercel dashboard, go to Settings > Environment Variables and add:

```
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
NEXT_PUBLIC_APP_URL=https://argon-test.in
```

## Step 4: Set up Custom Domain

1. In Vercel project settings, go to "Domains"
2. Add your domain: `argon-test.in`
3. Vercel will provide DNS records to configure

## Step 5: Configure DNS

In your domain registrar's DNS settings, add these records:

```
Type: A
Name: @
Value: 76.76.19.61

Type: CNAME
Name: www
Value: cname.vercel-dns.com
```

## Step 6: Update Supabase Settings

1. Go to your Supabase project dashboard
2. Navigate to Authentication > URL Configuration
3. Add your production URLs:
   - Site URL: `https://argon-test.in`
   - Redirect URLs: `https://argon-test.in/**`

## Step 7: Deploy Database Schema

1. Go to Supabase SQL Editor
2. Run the schema from `scripts/schema.sql`
3. Run the migration script to import questions

## Step 8: Test Deployment

1. Visit `https://argon-test.in`
2. Test user registration and login
3. Test question practice functionality
4. Verify analytics are working

## Troubleshooting

### Common Issues

1. **Build Errors**: Check that all dependencies are installed and environment variables are set
2. **Database Connection**: Verify Supabase credentials and RLS policies
3. **Domain Not Working**: Check DNS propagation (can take up to 24 hours)
4. **Authentication Issues**: Verify redirect URLs in Supabase settings

### Performance Optimization

1. Enable Vercel Analytics
2. Configure CDN settings
3. Optimize images and assets
4. Monitor database performance

## Monitoring

- Use Vercel Analytics for performance monitoring
- Monitor Supabase usage and performance
- Set up error tracking (Sentry recommended)
- Monitor user engagement and question completion rates

## Security Checklist

- [ ] Environment variables are properly set
- [ ] RLS policies are enabled in Supabase
- [ ] HTTPS is enforced
- [ ] Authentication is working correctly
- [ ] No sensitive data in client-side code
- [ ] API routes are properly protected

## Backup Strategy

1. Regular database backups in Supabase
2. Code repository backups on GitHub
3. Environment variable backups
4. Regular testing of restore procedures

## Scaling Considerations

- Monitor database performance as user base grows
- Consider implementing caching strategies
- Plan for increased question volume
- Monitor API rate limits
- Consider implementing CDN for static assets
