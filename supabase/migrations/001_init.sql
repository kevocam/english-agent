-- =========================================================
-- english-agent · 001_init
-- Esquema base: contenido del curso, repaso SM-2, sesiones,
-- intentos y configuración. Diseñado para un solo usuario.
-- =========================================================

-- ---------- Tipos ----------
create type item_type      as enum ('vocab', 'phrasal', 'idiom', 'grammar');
create type srs_status     as enum ('new', 'learning', 'mastered');
create type session_status as enum ('sent', 'answered', 'done');

-- ---------- Contenido del curso ----------
create table items (
  id          uuid primary key default gen_random_uuid(),
  type        item_type   not null,
  term        text        not null,
  definition  text        not null,
  example     text,
  category    text,                          -- ej. leadership_verbs, deduction_past, connectors_contrast
  lesson      text        not null default 'lesson-1',
  created_at  timestamptz not null default now(),
  unique (term, type)
);

-- Escenarios que usa el LLM para contextualizar ejercicios
create table contexts (
  id          smallint generated always as identity primary key,
  name        text not null unique,
  description text not null,
  keywords    text[] not null default '{}'
);

-- ---------- Repaso espaciado (SM-2) ----------
create table srs_state (
  item_id          uuid primary key references items(id) on delete cascade,
  ease_factor      numeric(4,2) not null default 2.50,
  interval_days    int          not null default 0,
  repetitions      int          not null default 0,
  due_date         date         not null default current_date,
  last_reviewed_at timestamptz,
  status           srs_status   not null default 'new'
);
create index srs_state_due_idx on srs_state (due_date);

-- Cada item nuevo nace con su estado SM-2
create function init_srs_state() returns trigger
language plpgsql as $$
begin
  insert into srs_state (item_id) values (new.id)
  on conflict (item_id) do nothing;
  return new;
end;
$$;

create trigger items_init_srs
after insert on items
for each row execute function init_srs_state();

-- ---------- Sesiones diarias ----------
create table daily_sessions (
  id                 uuid primary key default gen_random_uuid(),
  session_date       date           not null unique,
  item_ids           uuid[]         not null,
  status             session_status not null default 'sent',
  sent_at            timestamptz    not null default now(),
  last_user_reply_at timestamptz,
  last_nudge_at      timestamptz,
  nudge_count        int            not null default 0
);

-- ---------- Respuestas del usuario ----------
create table attempts (
  id          uuid primary key default gen_random_uuid(),
  session_id  uuid references daily_sessions(id) on delete set null,
  item_id     uuid not null references items(id) on delete cascade,
  exercise    text not null,
  user_answer text,
  score       smallint check (score between 0 and 5),   -- calidad SM-2
  feedback    text,
  created_at  timestamptz not null default now()
);
create index attempts_item_idx on attempts (item_id);

-- ---------- Configuración (una sola fila) ----------
create table settings (
  id                  smallint primary key default 1 check (id = 1),
  telegram_chat_id    bigint,
  timezone            text     not null default 'America/Lima',
  morning_time        time     not null default '06:00',
  sleep_start         time     not null default '23:30',
  sleep_end           time     not null default '05:50',
  -- bloques donde el bot se pausa (clases)
  class_schedule      jsonb    not null default
    '[{"day":"tue","start":"16:00","end":"17:00"},
      {"day":"thu","start":"16:00","end":"17:00"}]',
  -- insistencia escalonada; el último valor se repite
  nudge_intervals_min int[]    not null default '{10,20,40}',
  items_per_day       smallint not null default 3 check (items_per_day between 1 and 10),
  paused_until        timestamptz,
  updated_at          timestamptz not null default now()
);
insert into settings default values;

-- ---------- Seguridad ----------
-- RLS activo sin políticas: solo la secret/service_role key (el bot) accede.
-- Cuando llegue el front se agregan políticas de lectura.
alter table items          enable row level security;
alter table contexts       enable row level security;
alter table srs_state      enable row level security;
alter table daily_sessions enable row level security;
alter table attempts       enable row level security;
alter table settings       enable row level security;
