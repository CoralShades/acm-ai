---
paths:
  - "supabase/**/*"
  - "**/supabase*.sql"
---

# Supabase Rules

## Database Schema
- Use snake_case for table and column names
- Always define primary keys
- Use RLS (Row Level Security) for all tables

## Migrations
- Create migrations for all schema changes
- Use descriptive migration names
- Never modify existing migrations

## Functions
```sql
-- Use SECURITY DEFINER carefully
CREATE OR REPLACE FUNCTION function_name()
RETURNS type
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  -- function body
END;
$$;
```

## RLS Policies
```sql
-- Enable RLS
ALTER TABLE table_name ENABLE ROW LEVEL SECURITY;

-- Create policy
CREATE POLICY "policy_name" ON table_name
  FOR SELECT
  USING (auth.uid() = user_id);
```

## Environment Variables
- `SUPABASE_URL` - Supabase API URL
- `SUPABASE_ANON_KEY` - Anonymous key for client-side
- `SUPABASE_SERVICE_ROLE_KEY` - Service role key (server-side only)
