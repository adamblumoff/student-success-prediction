import {
  pgTable,
  serial,
  integer,
  varchar,
  text,
  timestamp,
  boolean,
  real,
  index,
  uniqueIndex
} from 'drizzle-orm/pg-core';

export const institutions = pgTable(
  'institutions',
  {
    id: serial('id').primaryKey(),
    name: varchar('name', { length: 255 }).notNull(),
    code: varchar('code', { length: 50 }).notNull(),
    type: varchar('type', { length: 50 }).notNull(),
    timezone: varchar('timezone', { length: 50 }).default('UTC'),
    active: boolean('active').default(true),
    createdAt: timestamp('created_at', { withTimezone: true }).defaultNow(),
    updatedAt: timestamp('updated_at', { withTimezone: true })
  },
  (table) => ({
    codeIdx: uniqueIndex('uq_institutions_code').on(table.code),
    nameIdx: index('ix_institutions_name').on(table.name),
    activeIdx: index('ix_institutions_active').on(table.active)
  })
);

export const students = pgTable(
  'students',
  {
    id: serial('id').primaryKey(),
    institutionId: integer('institution_id').notNull(),
    studentId: varchar('student_id', { length: 100 }).notNull(),
    sisId: varchar('sis_id', { length: 100 }),
    name: varchar('name', { length: 255 }),
    gradeLevel: varchar('grade_level', { length: 10 }),
    birthDate: timestamp('birth_date', { withTimezone: true }),
    gender: varchar('gender', { length: 10 }),
    ethnicity: varchar('ethnicity', { length: 50 }),
    currentGpa: real('current_gpa'),
    previousGpa: real('previous_gpa'),
    attendanceRate: real('attendance_rate'),
    studyHoursWeek: integer('study_hours_week'),
    extracurricular: integer('extracurricular'),
    parentEducation: integer('parent_education'),
    socioeconomicStatus: integer('socioeconomic_status'),
    enrollmentStatus: varchar('enrollment_status', { length: 20 }).default('active'),
    enrollmentDate: timestamp('enrollment_date', { withTimezone: true }),
    graduationDate: timestamp('graduation_date', { withTimezone: true }),
    isEll: boolean('is_ell').default(false),
    hasIep: boolean('has_iep').default(false),
    has504: boolean('has_504').default(false),
    isEconomicallyDisadvantaged: boolean('is_economically_disadvantaged').default(false),
    email: varchar('email', { length: 255 }),
    phone: varchar('phone', { length: 20 }),
    parentEmail: varchar('parent_email', { length: 255 }),
    parentPhone: varchar('parent_phone', { length: 20 }),
    createdAt: timestamp('created_at', { withTimezone: true }).defaultNow(),
    updatedAt: timestamp('updated_at', { withTimezone: true }),
    lastActivity: timestamp('last_activity', { withTimezone: true })
  },
  (table) => ({
    institutionStudentIdx: uniqueIndex('uq_students_institution_student_id').on(
      table.institutionId,
      table.studentId
    ),
    institutionStudentIndex: index('ix_students_institution_student_id').on(
      table.institutionId,
      table.studentId
    ),
    institutionGradeIdx: index('ix_students_institution_grade').on(
      table.institutionId,
      table.gradeLevel
    ),
    institutionStatusIdx: index('ix_students_institution_status').on(
      table.institutionId,
      table.enrollmentStatus
    )
  })
);

export const predictions = pgTable(
  'predictions',
  {
    id: serial('id').primaryKey(),
    institutionId: integer('institution_id').notNull(),
    studentId: integer('student_id').notNull(),
    riskScore: real('risk_score').notNull(),
    riskCategory: varchar('risk_category', { length: 20 }).notNull(),
    successProbability: real('success_probability'),
    confidenceScore: real('confidence_score'),
    modelVersion: varchar('model_version', { length: 50 }),
    modelType: varchar('model_type', { length: 50 }),
    predictionDate: timestamp('prediction_date', { withTimezone: true }).defaultNow(),
    featuresUsed: text('features_used'),
    featureImportance: text('feature_importance'),
    sessionId: varchar('session_id', { length: 100 }),
    dataSource: varchar('data_source', { length: 50 }),
    explanation: text('explanation'),
    riskFactors: text('risk_factors'),
    protectiveFactors: text('protective_factors'),
    createdAt: timestamp('created_at', { withTimezone: true }).defaultNow()
  },
  (table) => ({
    studentDateIdx: index('ix_predictions_student_date').on(table.studentId, table.predictionDate),
    institutionRiskIdx: index('ix_predictions_institution_risk').on(
      table.institutionId,
      table.riskCategory
    ),
    institutionDateIdx: index('ix_predictions_institution_date').on(
      table.institutionId,
      table.predictionDate
    )
  })
);

export const interventions = pgTable(
  'interventions',
  {
    id: serial('id').primaryKey(),
    institutionId: integer('institution_id').notNull(),
    studentId: integer('student_id').notNull(),
    predictionId: integer('prediction_id'),
    interventionType: varchar('intervention_type', { length: 100 }).notNull(),
    title: varchar('title', { length: 255 }).notNull(),
    description: text('description'),
    priority: varchar('priority', { length: 20 }),
    status: varchar('status', { length: 20 }).default('planned'),
    assignedTo: varchar('assigned_to', { length: 255 }),
    scheduledDate: timestamp('scheduled_date', { withTimezone: true }),
    completedDate: timestamp('completed_date', { withTimezone: true }),
    dueDate: timestamp('due_date', { withTimezone: true }),
    outcome: varchar('outcome', { length: 50 }),
    outcomeNotes: text('outcome_notes'),
    followUpNeeded: boolean('follow_up_needed').default(false),
    estimatedCost: real('estimated_cost'),
    actualCost: real('actual_cost'),
    timeSpentMinutes: integer('time_spent_minutes'),
    createdAt: timestamp('created_at', { withTimezone: true }).defaultNow(),
    updatedAt: timestamp('updated_at', { withTimezone: true })
  },
  (table) => ({
    studentStatusIdx: index('ix_interventions_student_status').on(table.studentId, table.status),
    institutionTypeIdx: index('ix_interventions_institution_type').on(
      table.institutionId,
      table.interventionType
    ),
    assignedStatusIdx: index('ix_interventions_assigned_status').on(
      table.assignedTo,
      table.status
    )
  })
);

export const auditLogs = pgTable(
  'audit_logs',
  {
    id: serial('id').primaryKey(),
    institutionId: integer('institution_id').notNull(),
    userId: integer('user_id'),
    userEmail: varchar('user_email', { length: 255 }),
    userRole: varchar('user_role', { length: 50 }),
    action: varchar('action', { length: 100 }).notNull(),
    resourceType: varchar('resource_type', { length: 50 }),
    resourceId: varchar('resource_id', { length: 100 }),
    ipAddress: varchar('ip_address', { length: 45 }),
    userAgent: text('user_agent'),
    sessionId: varchar('session_id', { length: 100 }),
    requestMethod: varchar('request_method', { length: 10 }),
    requestPath: varchar('request_path', { length: 500 }),
    requestParams: text('request_params'),
    responseStatus: integer('response_status'),
    processingTimeMs: integer('processing_time_ms'),
    timestamp: timestamp('timestamp', { withTimezone: true }).defaultNow()
  },
  (table) => ({
    userActionIdx: index('ix_audit_logs_user_action').on(table.userId, table.action),
    institutionTimestampIdx: index('ix_audit_logs_institution_timestamp').on(
      table.institutionId,
      table.timestamp
    ),
    resourceIdx: index('ix_audit_logs_resource').on(table.resourceType, table.resourceId)
  })
);

export const modelMetadata = pgTable(
  'model_metadata',
  {
    id: serial('id').primaryKey(),
    institutionId: integer('institution_id'),
    modelName: varchar('model_name', { length: 100 }).notNull(),
    modelVersion: varchar('model_version', { length: 50 }).notNull(),
    modelType: varchar('model_type', { length: 50 }),
    accuracy: real('accuracy'),
    aucScore: real('auc_score'),
    f1Score: real('f1_score'),
    precisionScore: real('precision_score'),
    recallScore: real('recall_score'),
    trainingDataSize: integer('training_data_size'),
    trainingFeatures: text('training_features'),
    trainingDate: timestamp('training_date', { withTimezone: true }),
    hyperparameters: text('hyperparameters'),
    featureEngineeringVersion: varchar('feature_engineering_version', { length: 50 }),
    deployedDate: timestamp('deployed_date', { withTimezone: true }),
    isActive: boolean('is_active').default(true),
    createdAt: timestamp('created_at', { withTimezone: true }).defaultNow()
  },
  (table) => ({
    activeIdx: index('ix_model_active').on(table.institutionId, table.modelType, table.isActive)
  })
);

export const users = pgTable(
  'users',
  {
    id: serial('id').primaryKey(),
    institutionId: integer('institution_id').notNull(),
    username: varchar('username', { length: 100 }).notNull(),
    email: varchar('email', { length: 255 }).notNull(),
    passwordHash: varchar('password_hash', { length: 255 }).notNull(),
    firstName: varchar('first_name', { length: 100 }).notNull(),
    lastName: varchar('last_name', { length: 100 }).notNull(),
    role: varchar('role', { length: 50 }).notNull(),
    isActive: boolean('is_active').default(true),
    isVerified: boolean('is_verified').default(false),
    lastLogin: timestamp('last_login', { withTimezone: true }),
    createdAt: timestamp('created_at', { withTimezone: true }).defaultNow(),
    updatedAt: timestamp('updated_at', { withTimezone: true })
  },
  (table) => ({
    usernameIdx: uniqueIndex('uq_users_username').on(table.username),
    emailIdx: uniqueIndex('uq_users_email').on(table.email),
    roleIdx: index('ix_users_role').on(table.role),
    activeIdx: index('ix_users_active').on(table.isActive)
  })
);

export const userSessions = pgTable(
  'user_sessions',
  {
    id: serial('id').primaryKey(),
    userId: integer('user_id').notNull(),
    sessionToken: varchar('session_token', { length: 255 }).notNull(),
    ipAddress: varchar('ip_address', { length: 45 }),
    userAgent: text('user_agent'),
    createdAt: timestamp('created_at', { withTimezone: true }).defaultNow(),
    expiresAt: timestamp('expires_at', { withTimezone: true }).notNull(),
    lastActivity: timestamp('last_activity', { withTimezone: true }).defaultNow(),
    isActive: boolean('is_active').default(true),
    revokedAt: timestamp('revoked_at', { withTimezone: true }),
    revokedReason: varchar('revoked_reason', { length: 100 })
  },
  (table) => ({
    sessionTokenIdx: uniqueIndex('uq_user_sessions_token').on(table.sessionToken),
    userIdx: index('ix_user_sessions_user').on(table.userId),
    activeIdx: index('ix_user_sessions_active').on(table.isActive)
  })
);

export const gptInsights = pgTable(
  'gpt_insights',
  {
    id: serial('id').primaryKey(),
    institutionId: integer('institution_id').notNull(),
    studentId: varchar('student_id', { length: 100 }).notNull(),
    studentDatabaseId: integer('student_database_id'),
    riskLevel: varchar('risk_level', { length: 20 }).notNull(),
    dataHash: varchar('data_hash', { length: 64 }).notNull(),
    rawResponse: text('raw_response').notNull(),
    formattedHtml: text('formatted_html').notNull(),
    gptModel: varchar('gpt_model', { length: 50 }).default('gpt-4o-mini'),
    tokensUsed: integer('tokens_used'),
    generationTimeMs: integer('generation_time_ms'),
    sessionId: varchar('session_id', { length: 100 }),
    userId: integer('user_id'),
    isCached: boolean('is_cached').default(false),
    cacheHits: integer('cache_hits').default(0),
    lastAccessed: timestamp('last_accessed', { withTimezone: true }).defaultNow(),
    createdAt: timestamp('created_at', { withTimezone: true }).defaultNow(),
    updatedAt: timestamp('updated_at', { withTimezone: true })
  },
  (table) => ({
    studentHashIdx: index('ix_gpt_insights_student_hash').on(table.studentId, table.dataHash),
    sessionRiskIdx: index('ix_gpt_insights_session_risk').on(table.sessionId, table.riskLevel),
    institutionCreatedIdx: index('ix_gpt_insights_institution_created').on(
      table.institutionId,
      table.createdAt
    )
  })
);

export type Institution = typeof institutions.$inferSelect;
export type Student = typeof students.$inferSelect;
export type Prediction = typeof predictions.$inferSelect;
export type Intervention = typeof interventions.$inferSelect;
export type GPTInsight = typeof gptInsights.$inferSelect;
export type User = typeof users.$inferSelect;
