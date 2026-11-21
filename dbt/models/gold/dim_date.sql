with bounds as (
    select
        min((game_start_ts at time zone 'America/Sao_Paulo')::date) as min_day,
        max((game_start_ts at time zone 'America/Sao_Paulo')::date) as max_day
    from {{ ref('stg_match') }}
),

days as (
    select generate_series(
        date_trunc('year', min_day)::date,
        (date_trunc('year', max_day) + interval '1 year' - interval '1 day')::date,
        interval '1 day'
    )::date as date_day
    from bounds
)

select
    to_char(date_day, 'YYYYMMDD')::int                      as date_key,
    date_day,
    extract(year from date_day)::int                        as year_number,
    extract(quarter from date_day)::int                     as quarter_number,
    extract(month from date_day)::int                       as month_number,
    (array['Janeiro','Fevereiro','Março','Abril','Maio','Junho',
           'Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']
    )[extract(month from date_day)::int]                    as month_name,
    extract(isodow from date_day)::int                      as day_of_week,
    (array['Segunda','Terça','Quarta','Quinta','Sexta','Sábado','Domingo']
    )[extract(isodow from date_day)::int]                   as day_name,
    extract(isodow from date_day) in (6, 7)                 as is_weekend
from days