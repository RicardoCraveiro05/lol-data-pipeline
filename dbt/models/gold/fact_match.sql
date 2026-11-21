select
    match_id,
    to_char((game_start_ts at time zone 'America/Sao_Paulo')::date, 'YYYYMMDD')::int as date_key,
    patch,
    queue_id,
    game_mode,
    game_start_ts,
    game_duration_sec,
    winning_team_id
from {{ ref('stg_match') }}