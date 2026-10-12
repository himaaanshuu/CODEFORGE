-- CodeForge AI — Supabase schema
-- ===============================
-- Run persistence: agent runs, event timelines, usage records.
--
-- Security model: RLS is ENABLED on every table with intentionally NO
-- policies → anon/authenticated roles are denied all access. The FastAPI
-- backend reads/writes with the service-role key (bypasses RLS). The web
-- app never talks to this database directly; it only calls the backend API.
--
-- Run in: Dashboard → SQL Editor → New query → paste → Run.

create table if not exists agent_runs (
  id text primary key,
  owner_uid text not null,
  task text not null,
  workspace_id text not null,
  status text not null check (status in ('RUNNING', 'COMPLETED', 'FAILED')),
  summary text not null default '',
  error text,
  metrics jsonb not null default '{}'::jsonb,
  plan jsonb not null default '[]'::jsonb,
  files_inspected jsonb not null default '[]'::jsonb,
  files_changed jsonb not null default '[]'::jsonb,
  diff_summary text not null default '',
  observation_count integer not null default 0,
  created_at double precision not null,
  updated_at double precision not null,
  completed_at double precision
);

create index if not exists agent_runs_owner_created_idx
  on agent_runs (owner_uid, created_at desc);

create table if not exists agent_run_events (
  id text primary key,
  owner_uid text not null,
  run_id text not null references agent_runs (id) on delete cascade,
  seq double precision not null,
  type text not null,
  "timestamp" double precision not null default 0,
  data jsonb not null default '{}'::jsonb,
  created_at double precision not null
);

create index if not exists agent_run_events_run_seq_idx
  on agent_run_events (run_id, seq);

create table if not exists usage_records (
  id text primary key,
  owner_uid text not null,
  run_id text not null references agent_runs (id) on delete cascade,
  tokens_used integer not null default 0,
  duration_seconds double precision not null default 0,
  model text not null default '',
  iterations integer not null default 0,
  repair_attempts integer not null default 0,
  created_at double precision not null
);

create index if not exists usage_records_owner_created_idx
  on usage_records (owner_uid, created_at desc);

-- Row Level Security: enabled with NO policies (deny-all for every role
-- that is not the service role). Do not add client-facing policies —
-- persistence is server-owned, mirroring the previous write: if false model.
alter table agent_runs enable row level security;
alter table agent_run_events enable row level security;
alter table usage_records enable row level security;
