-- Marca si el mensaje de la mañana ya se envió hoy
-- (la sesión puede existir antes si usaste /hoy de madrugada).
alter table daily_sessions add column morning_sent_at timestamptz;
