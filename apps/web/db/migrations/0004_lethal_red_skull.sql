ALTER TABLE "students" ADD COLUMN "latest_risk_score" real;--> statement-breakpoint
ALTER TABLE "students" ADD COLUMN "latest_risk_category" varchar(20);--> statement-breakpoint
ALTER TABLE "students" ADD COLUMN "latest_confidence_score" real;--> statement-breakpoint
ALTER TABLE "students" ADD COLUMN "latest_prediction_date" timestamp with time zone;--> statement-breakpoint
CREATE INDEX "ix_students_institution_latest_prediction" ON "students" USING btree ("institution_id","latest_prediction_date");