-- Pronunciación: IPA + texto hablado para buscar audio real (YouGlish)
alter table items add column ipa text;
-- Lo que se pronuncia de verdad. Para gramática no es el patrón
-- ("must have + past participle") sino la parte hablada ("must have").
-- Si es null, se usa `term`.
alter table items add column spoken text;
