-- CatalogMuse job store for the Go backend.
-- The agent service on :8790 remains the runner. Go writes this database
-- from the job JSON and from each decision it posts.
-- Image bytes stay on the agent service. output.url points at
-- GET /v1/jobs/{id}/files/{name}.

create schema if not exists catalogmuse;

create type catalogmuse.job_status as enum (
  'running',
  'waiting',
  'approved',
  'failed'
);

create type catalogmuse.agent_name as enum (
  'segment',
  'art_director',
  'scene',
  'copy',
  'rules'
);

create type catalogmuse.agent_state as enum (
  'pending',
  'running',
  'waiting',
  'approved',
  'changes_requested',
  'failed'
);

create type catalogmuse.decision_action as enum (
  'approve',
  'changes'
);

create table catalogmuse.jobs (
  id text primary key,
  status catalogmuse.job_status not null,
  error text not null default '',
  pending_agent catalogmuse.agent_name,
  approve_allowed boolean not null default false,
  spec text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint jobs_id_shape check (id ~ '^job_[0-9a-f]{12}$'),
  constraint jobs_waiting_has_agent check (
    status <> 'waiting' or pending_agent is not null
  ),
  constraint jobs_pending_only_while_waiting check (
    pending_agent is null or status = 'waiting'
  )
);

create table catalogmuse.job_agents (
  job_id text not null references catalogmuse.jobs (id) on delete cascade,
  name catalogmuse.agent_name not null,
  position smallint not null,
  state catalogmuse.agent_state not null,
  detail text not null default '',
  output jsonb,
  primary key (job_id, name),
  constraint job_agents_position check (position between 0 and 4),
  constraint job_agents_position_unique unique (job_id, position)
);

create table catalogmuse.decisions (
  id bigint generated always as identity primary key,
  job_id text not null references catalogmuse.jobs (id) on delete cascade,
  agent catalogmuse.agent_name not null,
  action catalogmuse.decision_action not null,
  note text not null default '',
  prompt text not null default '',
  styles jsonb not null default '[]'::jsonb,
  variations smallint,
  images jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(),
  constraint decisions_note_when_changes check (
    action <> 'changes' or length(btrim(note)) > 0
  ),
  constraint decisions_scene_is_choice check (
    agent <> 'scene' or action = 'approve'
  ),
  constraint decisions_styles_array check (jsonb_typeof(styles) = 'array'),
  constraint decisions_images_array check (jsonb_typeof(images) = 'array'),
  constraint decisions_style_count check (jsonb_array_length(styles) <= 8),
  constraint decisions_variations_range check (
    variations is null or variations between 1 and 4
  )
);

create index jobs_status_created_idx
  on catalogmuse.jobs (status, created_at desc);

create index decisions_job_created_idx
  on catalogmuse.decisions (job_id, created_at);

create or replace function catalogmuse.touch_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger jobs_touch_updated_at
  before update on catalogmuse.jobs
  for each row
  execute function catalogmuse.touch_updated_at();

-- Same shape as GET /v1/jobs/{id}, plus the spec Go accepted.
create view catalogmuse.job_document as
select
  j.id,
  j.spec,
  j.created_at,
  j.updated_at,
  jsonb_build_object(
    'id', j.id,
    'status', j.status,
    'error', j.error,
    'pending_agent', j.pending_agent,
    'approve_allowed', j.approve_allowed,
    'agents', coalesce(
      (
        select jsonb_agg(
          jsonb_build_object(
            'name', a.name,
            'state', a.state,
            'detail', a.detail,
            'output', a.output
          )
          order by a.position
        )
        from catalogmuse.job_agents as a
        where a.job_id = j.id
      ),
      '[]'::jsonb
    )
  ) as body
from catalogmuse.jobs as j;
