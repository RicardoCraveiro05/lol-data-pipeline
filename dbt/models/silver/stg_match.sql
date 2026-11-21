select
    match_id,
    payload->'info'->>'gameVersion'                      as game_version,
    split_part(payload->'info'->>'gameVersion', '.', 1)
        || '.' ||
    split_part(payload->'info'->>'gameVersion', '.', 2)  as patch,
    (payload->'info'->>'queueId')::int                   as queue_id,
    payload->'info'->>'gameMode'                         as game_mode,
    payload->'info'->>'platformId'                       as platform_id,
    to_timestamp(
        (payload->'info'->>'gameStartTimestamp')::bigint / 1000.0
    )                                                    as game_start_ts,
    (payload->'info'->>'gameDuration')::int              as game_duration_sec,
    (
        select (t->>'teamId')::int
        from jsonb_array_elements(payload->'info'->'teams') as t
        where (t->>'win')::boolean
        limit 1
    )                                                    as winning_team_id,
    ingested_at
from {{ source('bronze', 'matches_raw') }}