-- Example Athena DDL and mapping to NormalizedEvent
-- Adjust S3 location and serde settings for your environment

CREATE EXTERNAL TABLE IF NOT EXISTS telemetry_raw (
  ts bigint,
  event_type string,
  device_id string,
  session_id string,
  payload string
)
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
LOCATION 's3://my-telemetry-bucket/path/to/events/';

-- Example query to map raw records to NormalizedEvent fields
SELECT
  ts as t_event_ms,
  event_type as kind,
  session_id as session_key,
  device_id as device_key,
  CAST(json_parse(payload) AS MAP<VARCHAR, VARCHAR>) as metadata
FROM telemetry_raw
WHERE ts BETWEEN 0 AND 999999999999;

-- Aggregation example: events per minute
SELECT
  floor(ts / 60000) as minute_bucket,
  event_type,
  count(*) as cnt
FROM telemetry_raw
GROUP BY floor(ts / 60000), event_type
ORDER BY minute_bucket DESC;
