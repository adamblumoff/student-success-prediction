"""implement_row_level_security_policies

Revision ID: cd8752e735e5
Revises: 375b9b58f70d
Create Date: 2025-08-13 16:13:58.123456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cd8752e735e5'
down_revision: Union[str, Sequence[str], None] = '375b9b58f70d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Implement comprehensive row-level security policies for K-12 multi-tenant system"""
    
    # Check if we're using PostgreSQL (RLS only supported on PostgreSQL)
    connection = op.get_bind()
    if connection.dialect.name != 'postgresql':
        print("⚠️  Row-level security requires PostgreSQL. Skipping RLS policies for SQLite.")
        return
    
    print("🔒 Implementing PostgreSQL row-level security policies...")
    
    # Enable Row Level Security on all institution-based tables
    op.execute("ALTER TABLE students ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE predictions ENABLE ROW LEVEL SECURITY") 
    op.execute("ALTER TABLE interventions ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE model_metadata ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE institutions ENABLE ROW LEVEL SECURITY")
    
    # Create a security function to get current user's institution_id
    op.execute("""
        CREATE OR REPLACE FUNCTION get_current_user_institution_id()
        RETURNS INTEGER AS $$
        BEGIN
            -- Get institution_id from current session context
            -- This will be set by the application when user authenticates
            RETURN COALESCE(
                current_setting('app.current_institution_id', true)::INTEGER,
                0  -- Default to 0 (no access) if not set
            );
        EXCEPTION
            WHEN OTHERS THEN
                RETURN 0;  -- Deny access if any error occurs
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
    """)
    
    # Create comprehensive RLS policies for STUDENTS table
    op.execute("""
        CREATE POLICY students_institution_isolation ON students
        FOR ALL TO public
        USING (institution_id = get_current_user_institution_id())
        WITH CHECK (institution_id = get_current_user_institution_id());
    """)
    
    # Create comprehensive RLS policies for PREDICTIONS table  
    op.execute("""
        CREATE POLICY predictions_institution_isolation ON predictions
        FOR ALL TO public
        USING (institution_id = get_current_user_institution_id())
        WITH CHECK (institution_id = get_current_user_institution_id());
    """)
    
    # Create comprehensive RLS policies for INTERVENTIONS table
    op.execute("""
        CREATE POLICY interventions_institution_isolation ON interventions
        FOR ALL TO public
        USING (institution_id = get_current_user_institution_id())
        WITH CHECK (institution_id = get_current_user_institution_id());
    """)
    
    # Create comprehensive RLS policies for AUDIT_LOGS table
    op.execute("""
        CREATE POLICY audit_logs_institution_isolation ON audit_logs
        FOR ALL TO public
        USING (institution_id = get_current_user_institution_id())
        WITH CHECK (institution_id = get_current_user_institution_id());
    """)
    
    # Create comprehensive RLS policies for MODEL_METADATA table
    op.execute("""
        CREATE POLICY model_metadata_institution_isolation ON model_metadata
        FOR ALL TO public
        USING (
            institution_id = get_current_user_institution_id() 
            OR institution_id IS NULL  -- Allow global models
        )
        WITH CHECK (
            institution_id = get_current_user_institution_id()
            OR institution_id IS NULL  -- Allow global models
        );
    """)
    
    # Create comprehensive RLS policies for INSTITUTIONS table
    # Users can only see their own institution
    op.execute("""
        CREATE POLICY institutions_own_institution ON institutions
        FOR ALL TO public
        USING (id = get_current_user_institution_id())
        WITH CHECK (id = get_current_user_institution_id());
    """)
    
    # Create additional security policies for SELECT operations
    # These provide read-only access with proper institution filtering
    op.execute("""
        CREATE POLICY students_select_policy ON students
        FOR SELECT TO public
        USING (institution_id = get_current_user_institution_id());
    """)
    
    op.execute("""
        CREATE POLICY predictions_select_policy ON predictions  
        FOR SELECT TO public
        USING (institution_id = get_current_user_institution_id());
    """)
    
    op.execute("""
        CREATE POLICY interventions_select_policy ON interventions
        FOR SELECT TO public
        USING (institution_id = get_current_user_institution_id());
    """)
    
    # Create function to set user session context (called by application)
    op.execute("""
        CREATE OR REPLACE FUNCTION set_user_institution_context(inst_id INTEGER)
        RETURNS VOID AS $$
        BEGIN
            -- Set the institution_id in the current session
            PERFORM set_config('app.current_institution_id', inst_id::TEXT, false);
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
    """)
    
    # Create function to clear user session context (for security)
    op.execute("""
        CREATE OR REPLACE FUNCTION clear_user_institution_context()
        RETURNS VOID AS $$
        BEGIN
            -- Clear the institution_id from the current session
            PERFORM set_config('app.current_institution_id', '', false);
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
    """)
    
    # Create security audit trigger function
    op.execute("""
        CREATE OR REPLACE FUNCTION security_audit_trigger()
        RETURNS TRIGGER AS $$
        BEGIN
            -- Log all data access attempts for security monitoring
            INSERT INTO audit_logs (
                institution_id,
                user_id, 
                action,
                resource_type,
                resource_id,
                ip_address,
                created_at,
                compliance_data
            ) VALUES (
                get_current_user_institution_id(),
                current_setting('app.current_user_id', true),
                TG_OP,
                TG_TABLE_NAME,
                COALESCE(NEW.id::TEXT, OLD.id::TEXT),
                current_setting('app.current_ip_address', true),
                CURRENT_TIMESTAMP,
                jsonb_build_object(
                    'rls_policy', 'enforced',
                    'institution_check', 'passed',
                    'table', TG_TABLE_NAME,
                    'operation', TG_OP
                )
            );
            
            RETURN COALESCE(NEW, OLD);
        EXCEPTION
            WHEN OTHERS THEN
                -- Don't fail the main operation if audit logging fails
                RETURN COALESCE(NEW, OLD);
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
    """)
    
    # Apply security audit triggers to sensitive tables
    op.execute("""
        CREATE TRIGGER students_security_audit
        AFTER INSERT OR UPDATE OR DELETE ON students
        FOR EACH ROW EXECUTE FUNCTION security_audit_trigger();
    """)
    
    op.execute("""
        CREATE TRIGGER predictions_security_audit  
        AFTER INSERT OR UPDATE OR DELETE ON predictions
        FOR EACH ROW EXECUTE FUNCTION security_audit_trigger();
    """)
    
    op.execute("""
        CREATE TRIGGER interventions_security_audit
        AFTER INSERT OR UPDATE OR DELETE ON interventions
        FOR EACH ROW EXECUTE FUNCTION security_audit_trigger();
    """)


def downgrade() -> None:
    """Remove row-level security policies and related functions"""
    
    # Drop security audit triggers
    op.execute("DROP TRIGGER IF EXISTS students_security_audit ON students")
    op.execute("DROP TRIGGER IF EXISTS predictions_security_audit ON predictions") 
    op.execute("DROP TRIGGER IF EXISTS interventions_security_audit ON interventions")
    
    # Drop security audit trigger function
    op.execute("DROP FUNCTION IF EXISTS security_audit_trigger()")
    
    # Drop session context functions
    op.execute("DROP FUNCTION IF EXISTS set_user_institution_context(INTEGER)")
    op.execute("DROP FUNCTION IF EXISTS clear_user_institution_context()")
    
    # Drop all RLS policies
    op.execute("DROP POLICY IF EXISTS students_institution_isolation ON students")
    op.execute("DROP POLICY IF EXISTS students_select_policy ON students") 
    op.execute("DROP POLICY IF EXISTS predictions_institution_isolation ON predictions")
    op.execute("DROP POLICY IF EXISTS predictions_select_policy ON predictions")
    op.execute("DROP POLICY IF EXISTS interventions_institution_isolation ON interventions")
    op.execute("DROP POLICY IF EXISTS interventions_select_policy ON interventions")
    op.execute("DROP POLICY IF EXISTS audit_logs_institution_isolation ON audit_logs")
    op.execute("DROP POLICY IF EXISTS model_metadata_institution_isolation ON model_metadata")
    op.execute("DROP POLICY IF EXISTS institutions_own_institution ON institutions")
    
    # Drop security function
    op.execute("DROP FUNCTION IF EXISTS get_current_user_institution_id()")
    
    # Disable Row Level Security on all tables
    op.execute("ALTER TABLE students DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE predictions DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE interventions DISABLE ROW LEVEL SECURITY") 
    op.execute("ALTER TABLE audit_logs DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE model_metadata DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE institutions DISABLE ROW LEVEL SECURITY")