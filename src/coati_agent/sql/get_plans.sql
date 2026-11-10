-- The plans table and the get_plans function the agent calls (spec, Task 8).
-- coati_agent.plans renders {catalog}, {schema} and {volume_dir} after
-- checking each is a plain identifier or a /Volumes path.

CREATE OR REPLACE TABLE {catalog}.{schema}.plans
COMMENT 'Latitude 10 plans, from the site''s plans.ts (prices only for launched plans).'
AS SELECT * FROM read_files('{volume_dir}/plans.jsonl',
  format => 'json',
  schema => 'id STRING, name STRING, audience STRING, launched BOOLEAN, builds STRING, price STRING, annual_price STRING, apis INT, seats INT, sdk_endpoints INT, included ARRAY<STRING>, planned ARRAY<STRING>');

CREATE OR REPLACE FUNCTION {catalog}.{schema}.get_plans(
  plan STRING DEFAULT NULL COMMENT 'A plan id or name (Free, Pro, Business, Enterprise); NULL for every plan.'
)
RETURNS TABLE (
  id STRING, name STRING, audience STRING, launched BOOLEAN, builds STRING,
  price STRING, annual_price STRING, apis INT, seats INT, sdk_endpoints INT,
  included ARRAY<STRING>, planned ARRAY<STRING>
)
COMMENT 'Latitude 10 plans: price, annual price, limits, what is included and what is planned.'
RETURN SELECT id, name, audience, launched, builds, price, annual_price, apis, seats,
              sdk_endpoints, included, planned
       FROM {catalog}.{schema}.plans
       WHERE plan IS NULL OR lower(id) = lower(trim(plan)) OR lower(name) = lower(trim(plan));
