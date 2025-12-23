ALTER TABLE "students" ADD COLUMN IF NOT EXISTS "latest_risk_score" real;--> statement-breakpoint
ALTER TABLE "students" ADD COLUMN IF NOT EXISTS "latest_risk_category" varchar(20);--> statement-breakpoint
ALTER TABLE "students" ADD COLUMN IF NOT EXISTS "latest_confidence_score" real;--> statement-breakpoint
ALTER TABLE "students" ADD COLUMN IF NOT EXISTS "latest_prediction_date" timestamp with time zone;--> statement-breakpoint
CREATE INDEX IF NOT EXISTS "ix_students_institution_latest_prediction" ON "students" USING btree ("institution_id","latest_prediction_date");--> statement-breakpoint
WITH latest AS (
  SELECT DISTINCT ON (p.student_id)
    p.student_id,
    p.risk_score,
    p.risk_category,
    p.confidence_score,
    p.prediction_date
  FROM "predictions" p
  ORDER BY p.student_id, p.prediction_date DESC
)
UPDATE "students" s
SET
  latest_risk_score = latest.risk_score,
  latest_risk_category = latest.risk_category,
  latest_confidence_score = latest.confidence_score,
  latest_prediction_date = latest.prediction_date
FROM latest
WHERE s.id = latest.student_id;
