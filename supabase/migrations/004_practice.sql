-- Sprint 2: estado de la práctica en cadena dentro de la sesión del día
alter table daily_sessions
  add column current_index    smallint not null default 0,      -- qué item se está practicando
  add column current_exercise text,                             -- ejercicio pendiente (null = nada pendiente)
  add column exercise_type    text,
  add column exercise_sent_at timestamptz,                      -- base para la insistencia
  add column retry_used       boolean  not null default false;  -- ya se usó el reintento de este item

alter table attempts
  add column attempt smallint not null default 1;               -- 1 = primer intento, 2 = reintento
