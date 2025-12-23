CREATE INDEX IF NOT EXISTS "ix_predictions_district_institution_student_date" ON "predictions" USING btree ("district_id","institution_id","student_id","prediction_date");--> statement-breakpoint
CREATE INDEX IF NOT EXISTS "ix_interventions_district_institution_student_status" ON "interventions" USING btree ("district_id","institution_id","student_id","status");--> statement-breakpoint
CREATE INDEX IF NOT EXISTS "ix_gpt_insights_district_institution_student_created" ON "gpt_insights" USING btree ("district_id","institution_id","student_database_id","created_at");
