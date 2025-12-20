CREATE TABLE "audit_logs" (
	"id" serial PRIMARY KEY NOT NULL,
	"institution_id" integer NOT NULL,
	"user_id" integer,
	"user_email" varchar(255),
	"user_role" varchar(50),
	"action" varchar(100) NOT NULL,
	"resource_type" varchar(50),
	"resource_id" varchar(100),
	"ip_address" varchar(45),
	"user_agent" text,
	"session_id" varchar(100),
	"request_method" varchar(10),
	"request_path" varchar(500),
	"request_params" text,
	"response_status" integer,
	"processing_time_ms" integer,
	"timestamp" timestamp with time zone DEFAULT now()
);
--> statement-breakpoint
CREATE TABLE "gpt_insights" (
	"id" serial PRIMARY KEY NOT NULL,
	"institution_id" integer NOT NULL,
	"student_id" varchar(100) NOT NULL,
	"student_database_id" integer,
	"risk_level" varchar(20) NOT NULL,
	"data_hash" varchar(64) NOT NULL,
	"raw_response" text NOT NULL,
	"formatted_html" text NOT NULL,
	"gpt_model" varchar(50) DEFAULT 'gpt-4o-mini',
	"tokens_used" integer,
	"generation_time_ms" integer,
	"session_id" varchar(100),
	"user_id" integer,
	"is_cached" boolean DEFAULT false,
	"cache_hits" integer DEFAULT 0,
	"last_accessed" timestamp with time zone DEFAULT now(),
	"created_at" timestamp with time zone DEFAULT now(),
	"updated_at" timestamp with time zone
);
--> statement-breakpoint
CREATE TABLE "institutions" (
	"id" serial PRIMARY KEY NOT NULL,
	"name" varchar(255) NOT NULL,
	"code" varchar(50) NOT NULL,
	"type" varchar(50) NOT NULL,
	"timezone" varchar(50) DEFAULT 'UTC',
	"active" boolean DEFAULT true,
	"created_at" timestamp with time zone DEFAULT now(),
	"updated_at" timestamp with time zone
);
--> statement-breakpoint
CREATE TABLE "interventions" (
	"id" serial PRIMARY KEY NOT NULL,
	"institution_id" integer NOT NULL,
	"student_id" integer NOT NULL,
	"prediction_id" integer,
	"intervention_type" varchar(100) NOT NULL,
	"title" varchar(255) NOT NULL,
	"description" text,
	"priority" varchar(20),
	"status" varchar(20) DEFAULT 'planned',
	"assigned_to" varchar(255),
	"scheduled_date" timestamp with time zone,
	"completed_date" timestamp with time zone,
	"due_date" timestamp with time zone,
	"outcome" varchar(50),
	"outcome_notes" text,
	"follow_up_needed" boolean DEFAULT false,
	"estimated_cost" real,
	"actual_cost" real,
	"time_spent_minutes" integer,
	"created_at" timestamp with time zone DEFAULT now(),
	"updated_at" timestamp with time zone
);
--> statement-breakpoint
CREATE TABLE "model_metadata" (
	"id" serial PRIMARY KEY NOT NULL,
	"institution_id" integer,
	"model_name" varchar(100) NOT NULL,
	"model_version" varchar(50) NOT NULL,
	"model_type" varchar(50),
	"accuracy" real,
	"auc_score" real,
	"f1_score" real,
	"precision_score" real,
	"recall_score" real,
	"training_data_size" integer,
	"training_features" text,
	"training_date" timestamp with time zone,
	"hyperparameters" text,
	"feature_engineering_version" varchar(50),
	"deployed_date" timestamp with time zone,
	"is_active" boolean DEFAULT true,
	"created_at" timestamp with time zone DEFAULT now()
);
--> statement-breakpoint
CREATE TABLE "predictions" (
	"id" serial PRIMARY KEY NOT NULL,
	"institution_id" integer NOT NULL,
	"student_id" integer NOT NULL,
	"risk_score" real NOT NULL,
	"risk_category" varchar(20) NOT NULL,
	"success_probability" real,
	"confidence_score" real,
	"model_version" varchar(50),
	"model_type" varchar(50),
	"prediction_date" timestamp with time zone DEFAULT now(),
	"features_used" text,
	"feature_importance" text,
	"session_id" varchar(100),
	"data_source" varchar(50),
	"explanation" text,
	"risk_factors" text,
	"protective_factors" text,
	"created_at" timestamp with time zone DEFAULT now()
);
--> statement-breakpoint
CREATE TABLE "students" (
	"id" serial PRIMARY KEY NOT NULL,
	"institution_id" integer NOT NULL,
	"student_id" varchar(100) NOT NULL,
	"sis_id" varchar(100),
	"name" varchar(255),
	"grade_level" varchar(10),
	"birth_date" timestamp with time zone,
	"gender" varchar(10),
	"ethnicity" varchar(50),
	"current_gpa" real,
	"previous_gpa" real,
	"attendance_rate" real,
	"study_hours_week" integer,
	"extracurricular" integer,
	"parent_education" integer,
	"socioeconomic_status" integer,
	"enrollment_status" varchar(20) DEFAULT 'active',
	"assigned_counselor" varchar(255),
	"enrollment_date" timestamp with time zone,
	"graduation_date" timestamp with time zone,
	"is_ell" boolean DEFAULT false,
	"has_iep" boolean DEFAULT false,
	"has_504" boolean DEFAULT false,
	"is_economically_disadvantaged" boolean DEFAULT false,
	"email" varchar(255),
	"phone" varchar(20),
	"parent_email" varchar(255),
	"parent_phone" varchar(20),
	"created_at" timestamp with time zone DEFAULT now(),
	"updated_at" timestamp with time zone,
	"last_activity" timestamp with time zone
);
--> statement-breakpoint
CREATE TABLE "user_sessions" (
	"id" serial PRIMARY KEY NOT NULL,
	"user_id" integer NOT NULL,
	"session_token" varchar(255) NOT NULL,
	"ip_address" varchar(45),
	"user_agent" text,
	"created_at" timestamp with time zone DEFAULT now(),
	"expires_at" timestamp with time zone NOT NULL,
	"last_activity" timestamp with time zone DEFAULT now(),
	"is_active" boolean DEFAULT true,
	"revoked_at" timestamp with time zone,
	"revoked_reason" varchar(100)
);
--> statement-breakpoint
CREATE TABLE "users" (
	"id" serial PRIMARY KEY NOT NULL,
	"institution_id" integer NOT NULL,
	"username" varchar(100) NOT NULL,
	"email" varchar(255) NOT NULL,
	"password_hash" varchar(255) NOT NULL,
	"first_name" varchar(100) NOT NULL,
	"last_name" varchar(100) NOT NULL,
	"role" varchar(50) NOT NULL,
	"is_active" boolean DEFAULT true,
	"is_verified" boolean DEFAULT false,
	"last_login" timestamp with time zone,
	"created_at" timestamp with time zone DEFAULT now(),
	"updated_at" timestamp with time zone
);
--> statement-breakpoint
CREATE INDEX "ix_audit_logs_user_action" ON "audit_logs" USING btree ("user_id","action");--> statement-breakpoint
CREATE INDEX "ix_audit_logs_institution_timestamp" ON "audit_logs" USING btree ("institution_id","timestamp");--> statement-breakpoint
CREATE INDEX "ix_audit_logs_resource" ON "audit_logs" USING btree ("resource_type","resource_id");--> statement-breakpoint
CREATE INDEX "ix_gpt_insights_student_hash" ON "gpt_insights" USING btree ("student_id","data_hash");--> statement-breakpoint
CREATE INDEX "ix_gpt_insights_session_risk" ON "gpt_insights" USING btree ("session_id","risk_level");--> statement-breakpoint
CREATE INDEX "ix_gpt_insights_institution_created" ON "gpt_insights" USING btree ("institution_id","created_at");--> statement-breakpoint
CREATE UNIQUE INDEX "uq_institutions_code" ON "institutions" USING btree ("code");--> statement-breakpoint
CREATE INDEX "ix_institutions_name" ON "institutions" USING btree ("name");--> statement-breakpoint
CREATE INDEX "ix_institutions_active" ON "institutions" USING btree ("active");--> statement-breakpoint
CREATE INDEX "ix_interventions_student_status" ON "interventions" USING btree ("student_id","status");--> statement-breakpoint
CREATE INDEX "ix_interventions_institution_type" ON "interventions" USING btree ("institution_id","intervention_type");--> statement-breakpoint
CREATE INDEX "ix_interventions_assigned_status" ON "interventions" USING btree ("assigned_to","status");--> statement-breakpoint
CREATE INDEX "ix_model_active" ON "model_metadata" USING btree ("institution_id","model_type","is_active");--> statement-breakpoint
CREATE INDEX "ix_predictions_student_date" ON "predictions" USING btree ("student_id","prediction_date");--> statement-breakpoint
CREATE INDEX "ix_predictions_institution_risk" ON "predictions" USING btree ("institution_id","risk_category");--> statement-breakpoint
CREATE INDEX "ix_predictions_institution_date" ON "predictions" USING btree ("institution_id","prediction_date");--> statement-breakpoint
CREATE UNIQUE INDEX "uq_students_institution_student_id" ON "students" USING btree ("institution_id","student_id");--> statement-breakpoint
CREATE INDEX "ix_students_institution_student_id" ON "students" USING btree ("institution_id","student_id");--> statement-breakpoint
CREATE INDEX "ix_students_institution_grade" ON "students" USING btree ("institution_id","grade_level");--> statement-breakpoint
CREATE INDEX "ix_students_institution_status" ON "students" USING btree ("institution_id","enrollment_status");--> statement-breakpoint
CREATE UNIQUE INDEX "uq_user_sessions_token" ON "user_sessions" USING btree ("session_token");--> statement-breakpoint
CREATE INDEX "ix_user_sessions_user" ON "user_sessions" USING btree ("user_id");--> statement-breakpoint
CREATE INDEX "ix_user_sessions_active" ON "user_sessions" USING btree ("is_active");--> statement-breakpoint
CREATE UNIQUE INDEX "uq_users_username" ON "users" USING btree ("username");--> statement-breakpoint
CREATE UNIQUE INDEX "uq_users_email" ON "users" USING btree ("email");--> statement-breakpoint
CREATE INDEX "ix_users_role" ON "users" USING btree ("role");--> statement-breakpoint
CREATE INDEX "ix_users_active" ON "users" USING btree ("is_active");