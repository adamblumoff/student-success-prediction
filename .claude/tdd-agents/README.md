# K-12 Educational TDD Agent Suite

This directory contains specialized Test-Driven Development (TDD) agents designed specifically for K-12 educational software development, with emphasis on FERPA compliance, educational appropriateness, and student success outcomes.

## Agent Directory Structure

```
tdd-agents/
├── educational/          # Educational appropriateness and content validation
│   └── educational-appropriateness-agent.md
├── security/            # FERPA compliance and student data protection
│   └── ferpa-security-audit-agent.md  
├── quality/             # Code quality, AI validation, and optimization
│   ├── gpt-ai-validation-agent.md
│   ├── code-reviewer.md
│   ├── code-bloat-eliminator.md
│   ├── code-production-refactor.md
│   └── technical-debt-preventer.md
├── testing/             # Test coverage and TDD orchestration
│   ├── test-coverage-quality-agent.md
│   └── tdd-orchestrator-agent.md
└── README.md            # This file
```

## TDD Agent Workflow for K-12 Educational Software

### 1. **Educational Appropriateness Agent** (First)
**Use when**: Adding any feature that affects student or educator interfaces
- Validates grade-level appropriateness (K-5, 6-8, 9-12)
- Ensures educational vocabulary and concepts
- Checks for age-appropriate cognitive complexity
- Validates intervention recommendations are school-appropriate

### 2. **FERPA Security Audit Agent** (Second)  
**Use when**: Implementing any student data feature or before deployment
- Ensures student PII protection and encryption
- Validates role-based access controls for educators
- Checks audit logging for compliance requirements
- Identifies potential data privacy violations

### 3. **Test Coverage Quality Agent** (Third)
**Use when**: Any code changes or pull requests
- Implements K-12 specific test patterns
- Validates educational domain testing coverage
- Ensures FERPA compliance test validation
- Checks performance testing for classroom scale

### 4. **GPT AI Validation Agent** (Fourth)
**Use when**: Modifying GPT integration or AI features
- Validates Emma Johnson format compliance
- Ensures educational content appropriateness
- Optimizes token usage and costs
- Protects student data privacy in AI processing

### 5. **TDD Orchestrator Agent** (Continuous)
**Use when**: Coordinating comprehensive TDD workflow
- Sequences all agents in optimal order
- Ensures Red-Green-Refactor cycle maintains educational standards
- Coordinates agent findings and recommendations
- Validates overall K-12 software compliance

## Usage Examples

### New Feature Development
```bash
# 1. Start with educational requirements
Use educational-appropriateness-agent to define K-12 requirements

# 2. Validate security implications
Use ferpa-security-audit-agent for student data protection

# 3. Implement TDD with educational patterns
Use test-coverage-quality-agent for proper test implementation

# 4. Validate AI components (if applicable)
Use gpt-ai-validation-agent for AI feature compliance

# 5. Coordinate overall compliance
Use tdd-orchestrator-agent for comprehensive validation
```

### Pull Request Review
```bash
# Use agents in sequence for comprehensive review
1. educational-appropriateness-agent  # Check educational suitability
2. ferpa-security-audit-agent        # Verify data protection
3. test-coverage-quality-agent       # Validate test coverage
4. gpt-ai-validation-agent          # Check AI components (if modified)
```

### Pre-Deployment Validation
```bash
# Use tdd-orchestrator-agent to coordinate full validation
# It will automatically sequence all relevant agents
Use tdd-orchestrator-agent for comprehensive deployment readiness
```

## Educational TDD Principles

1. **Student-First Design**: Every feature must benefit student success outcomes
2. **FERPA-by-Design**: Student data protection built into every component
3. **Grade-Level Awareness**: All features must be developmentally appropriate
4. **Educational Professional Standards**: Meet K-12 educator workflow requirements
5. **Evidence-Based Practice**: All interventions based on educational research

## Integration with Git Hooks

These agents integrate with the existing Git hook system:

- **Pre-commit**: Runs educational-appropriateness and ferpa-security-audit agents
- **Pre-push**: Runs comprehensive tdd-orchestrator-agent validation
- **CI/CD**: Can be integrated for automated educational software validation

## Reference Documentation

- **TDD Standards**: `docs/TDD_STANDARDS_AND_PATTERNS.md` - Comprehensive TDD patterns for educational software
- **Testing Guide**: `docs/TESTING_QUICK_REFERENCE.md` - Quick reference for educational testing
- **Security Checklist**: `docs/SECURITY_CHECKLIST.md` - FERPA compliance requirements
- **Main Documentation**: `CLAUDE.md` - Complete development guidelines

## Agent Configuration Notes

Each agent is configured with:
- **Educational Domain Expertise**: Understanding of K-12 requirements, FERPA compliance, and student development
- **Actionable Output Format**: Structured findings that can be directly addressed by development teams  
- **TDD Integration**: Alignment with Red-Green-Refactor cycle and educational testing patterns
- **Stakeholder Awareness**: Consideration for teachers, students, parents, and administrators

This agent suite transforms generic software development into specialized K-12 educational platform development with comprehensive validation of student success outcomes, data protection, and educational appropriateness.