DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM information_schema.tables
    WHERE table_schema = 'public' AND table_name = 'districts'
  ) THEN
    EXECUTE '
      CREATE TABLE "districts" (
        "id" serial PRIMARY KEY NOT NULL,
        "name" varchar(255) NOT NULL,
        "external_id" varchar(191) NOT NULL,
        "default_institution_id" integer,
        "timezone" varchar(50) DEFAULT ''UTC'',
        "active" boolean DEFAULT true,
        "created_at" timestamp with time zone DEFAULT now(),
        "updated_at" timestamp with time zone
      )';
  END IF;
END $$;
--> statement-breakpoint

INSERT INTO "districts" ("id", "name", "external_id", "timezone", "active")
SELECT 1, 'Default District', 'default', 'UTC', true
WHERE NOT EXISTS (SELECT 1 FROM "districts" WHERE "id" = 1);
--> statement-breakpoint

ALTER TABLE "institutions" ADD COLUMN IF NOT EXISTS "district_id" integer NOT NULL DEFAULT 1;--> statement-breakpoint
ALTER TABLE "students" ADD COLUMN IF NOT EXISTS "district_id" integer NOT NULL DEFAULT 1;--> statement-breakpoint
ALTER TABLE "predictions" ADD COLUMN IF NOT EXISTS "district_id" integer NOT NULL DEFAULT 1;--> statement-breakpoint
ALTER TABLE "interventions" ADD COLUMN IF NOT EXISTS "district_id" integer NOT NULL DEFAULT 1;--> statement-breakpoint
ALTER TABLE "audit_logs" ADD COLUMN IF NOT EXISTS "district_id" integer NOT NULL DEFAULT 1;--> statement-breakpoint
ALTER TABLE "model_metadata" ADD COLUMN IF NOT EXISTS "district_id" integer;--> statement-breakpoint
ALTER TABLE "users" ADD COLUMN IF NOT EXISTS "district_id" integer NOT NULL DEFAULT 1;--> statement-breakpoint
ALTER TABLE "gpt_insights" ADD COLUMN IF NOT EXISTS "district_id" integer NOT NULL DEFAULT 1;--> statement-breakpoint

DROP INDEX IF EXISTS "uq_institutions_code";--> statement-breakpoint
CREATE UNIQUE INDEX IF NOT EXISTS "uq_institutions_district_code" ON "institutions" USING btree ("district_id","code");--> statement-breakpoint
CREATE INDEX IF NOT EXISTS "ix_institutions_district" ON "institutions" USING btree ("district_id");--> statement-breakpoint
CREATE INDEX IF NOT EXISTS "ix_students_district" ON "students" USING btree ("district_id");--> statement-breakpoint
CREATE INDEX IF NOT EXISTS "ix_predictions_district" ON "predictions" USING btree ("district_id");--> statement-breakpoint
CREATE INDEX IF NOT EXISTS "ix_interventions_district" ON "interventions" USING btree ("district_id");--> statement-breakpoint
CREATE INDEX IF NOT EXISTS "ix_audit_logs_district_timestamp" ON "audit_logs" USING btree ("district_id","timestamp");--> statement-breakpoint
CREATE INDEX IF NOT EXISTS "ix_users_district" ON "users" USING btree ("district_id");--> statement-breakpoint
CREATE INDEX IF NOT EXISTS "ix_gpt_insights_district_created" ON "gpt_insights" USING btree ("district_id","created_at");--> statement-breakpoint
CREATE UNIQUE INDEX IF NOT EXISTS "uq_districts_external_id" ON "districts" USING btree ("external_id");--> statement-breakpoint
CREATE INDEX IF NOT EXISTS "ix_districts_name" ON "districts" USING btree ("name");--> statement-breakpoint
CREATE INDEX IF NOT EXISTS "ix_districts_active" ON "districts" USING btree ("active");--> statement-breakpoint

UPDATE "districts"
SET "default_institution_id" = (
  SELECT "id" FROM "institutions"
  WHERE "institutions"."district_id" = "districts"."id"
  ORDER BY "id" ASC
  LIMIT 1
)
WHERE "default_institution_id" IS NULL;
--> statement-breakpoint
