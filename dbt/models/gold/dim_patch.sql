with parsed as (
    select
        patch,
        case when split_part(patch, '.', 1) ~ '^[0-9]+$'
             then split_part(patch, '.', 1)::int end as patch_major,
        case when split_part(patch, '.', 2) ~ '^[0-9]+$'
             then split_part(patch, '.', 2)::int end as patch_minor,
        (game_start_ts at time zone 'America/Sao_Paulo')::date as game_date
    from {{ ref('stg_match') }}
    where patch is not null
)

select
    patch,
    patch_major,
    patch_minor,
    patch_major * 100 + patch_minor as patch_sort,
    min(game_date)                  as first_game_date
from parsed
group by patch, patch_major, patch_minor