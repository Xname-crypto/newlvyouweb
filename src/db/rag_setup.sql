-- Clean up previous attempts (optional, but good for a fresh start)
drop function if exists match_knowledge_base;
drop table if exists knowledge_base cascade;

-- Enable extensions
create extension if not exists vector;
-- Enable PGroonga for advanced Chinese full-text search
-- If this fails, your Supabase project might not have PGroonga enabled.
-- You can fallback to using 'simple' config, but PGroonga is much better for Chinese.
create extension if not exists pgroonga;

-- Create table
create table knowledge_base (
  id bigint primary key generated always as identity,
  content text,
  metadata jsonb,
  embedding vector(1024),
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Create Indices
-- 1. Vector Index
create index knowledge_base_embedding_idx on knowledge_base using hnsw (embedding vector_cosine_ops);

-- 2. Full Text Search Index (using PGroonga for Chinese support)
create index knowledge_base_content_pgroonga_idx on knowledge_base using pgroonga (content);

-- Hybrid Search Function (Vector + Keyword) using RRF (Reciprocal Rank Fusion)
create or replace function match_knowledge_base (
  query_embedding vector(1024),
  query_text text,
  match_threshold float,
  match_count int,
  w_vector float default 1.0,
  w_keyword float default 1.0
)
returns table (
  id bigint,
  content text,
  metadata jsonb,
  similarity float,
  combined_score float
)
language plpgsql
as $$
begin
  return query
  with v_docs as (
    select 
      id, 
      1 - (embedding <=> query_embedding) as similarity,
      row_number() over (order by 1 - (embedding <=> query_embedding) desc) as rank
    from knowledge_base
    where 1 - (embedding <=> query_embedding) > match_threshold
    limit match_count * 2
  ),
  k_docs as (
    select 
      id, 
      pgroonga_score(tableoid, ctid)::float as score,
      row_number() over (order by pgroonga_score(tableoid, ctid) desc) as rank
    from knowledge_base
    where content &@~ query_text -- PGroonga search operator
    limit match_count * 2
  ),
  combined as (
    select 
      coalesce(v.id, k.id) as id,
      coalesce(v.similarity, 0) as similarity,
      -- RRF Score Calculation: 1 / (k + rank)
      (
        coalesce(1.0 / (60 + v.rank), 0.0) * w_vector +
        coalesce(1.0 / (60 + k.rank), 0.0) * w_keyword
      ) as rrf_score
    from v_docs v
    full outer join k_docs k on v.id = k.id
  )
  select 
    kb.id,
    kb.content,
    kb.metadata,
    c.similarity,
    c.rrf_score as combined_score
  from combined c
  join knowledge_base kb on kb.id = c.id
  order by c.rrf_score desc
  limit match_count;
end;
$$;
