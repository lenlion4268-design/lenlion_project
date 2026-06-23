-- 创建应用用户（幂等）
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'novel') THEN
    CREATE USER novel WITH PASSWORD 'novel_password';
  END IF;
END
$$;
