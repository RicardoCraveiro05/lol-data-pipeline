select
    queue_id,
    queue_name,
    queue_group
from {{ ref('seed_queue') }}