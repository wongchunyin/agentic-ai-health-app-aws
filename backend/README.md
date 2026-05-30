# LiveWell Backend

Health and wellness platform backend built on AWS serverless architecture, featuring AI-powered chat, health planning, and user management.

## Architecture Overview

### Core Services
- **Lambda Functions**: Microservices handling AI chat, authentication, health planning
- **DynamoDB**: User profiles, chat history, session management (`livewell` table)
- **S3**: Profile data, plan storage, chat history
- **Cognito**: User authentication and OAuth
- **API Gateway**: RESTful API endpoints
- **OpenSearch**: Medical Q&A knowledge base with semantic search

## Prerequisites

### Installation

#### AWS CLI
```bash
# macOS
brew install awscli

# Ubuntu/Debian
sudo apt-get update && sudo apt-get install awscli

# Windows
# Download and install from: https://aws.amazon.com/cli/
```

#### SAM CLI
```bash
# macOS
brew install aws-sam-cli

# Ubuntu/Debian
wget https://github.com/aws/aws-sam-cli/releases/latest/download/aws-sam-cli-linux-x86_64.zip
unzip aws-sam-cli-linux-x86_64.zip -d sam-installation
sudo ./sam-installation/install

# Windows
# Download MSI installer from: https://github.com/aws/aws-sam-cli/releases/latest

# Verify installation
sam --version
```

#### Other Requirements
- Python 3.11+
- Docker (for layer building)
- Git

## Quick Setup

```bash
# 1. Configure AWS credentials
aws configure --profile account2
# Enter your AWS Access Key ID, Secret Access Key, region (us-east-1), and output format (json)

# 2. Set environment variables
export AWS_PROFILE=account2
export AWS_DEFAULT_REGION=us-east-1

# 3. Verify setup
aws sts get-caller-identity --profile account2
sam --version
```

## Lambda Layers

### Layer Architecture Overview
The backend uses a modular layer architecture to share common code across Lambda functions. Each layer provides specific functionality and is versioned independently.

| Layer | Current Version | Purpose | Key Components |
|-------|----------------|---------|----------------|
| **aws-layer** | v41 | AWS service integrations | S3Helper, DynamoDBHelper, CognitoHelper |
| **livewell-core-layer** | v135 | Business logic & data models | Schemas, DocumentManager, AssessmentManager |
| **message-layer** | v10 | API response formatting | MsgHelper, response utilities |
| **ai-agent-layer** | v140+ | Modular AI agent system | 23 tools, LangChain integration, GeminiSimple |
| **twilio-layer** | v1 | SMS notifications | Twilio SDK for cross-platform SMS delivery |


### Layer Components Detail

**Layer Directory Structure:**
Local development structure (layers/[layer-name]/python/) gets packaged and mounted to `/opt/python/` in AWS Lambda runtime.

#### aws-layer (Core AWS Services)
```
layers/aws/python/           # Local development path
├── s3_helper.py          # S3 operations and file management
├── dynamodb_helper.py    # DynamoDB CRUD operations with error handling
├── config.py            # Centralized configuration management
├── cognito_helper.py    # JWT validation, login tracking, auth_time extraction
└── cognito_admin_helper.py # Admin Cognito operations
```

**Key Features:**
- S3Helper: Upload/download with automatic error handling
- DynamoDBHelper: Type-safe CRUD operations with retry logic
- CognitoHelper: JWT token validation with auth_time claim extraction for engagement tracking
- Config: Environment-based configuration management

#### livewell-core-layer (Business Logic)
```
layers/livewell-core/python/
├── schemas.py                    # Pydantic data models and validation
├── document_manager.py           # Core document operations (S3 + DynamoDB)
├── assessment_manager.py         # Health assessment processing
├── assessment_utils.py           # Assessment scoring utilities
├── medical_search_manager.py     # OpenSearch medical knowledge base
├── chat_history_manager.py       # Chat conversation management
├── livewell_config.py           # Core configuration settings
├── config.py                    # Legacy configuration
├── constants.py                 # Application constants
└── utils.py                     # Common utility functions
```

**Core Schemas (schemas.py):**
- **Profile**: Complete user profile with demographics, preferences, address, permissions
- **AACTTPlan**: Structured wellness plans (Action, Actor, Context, Target, Time)
- **FrailtyAssessmentHistory**: Health assessments with scoring (FRAIL, ROCKWOOD_MITNITSKI)
- **UserPreferences**: Activity preferences across physical/mental/diet/medical categories
- **Metadata**: Audit trail with creation/update timestamps and versioning
- **Enums**: Gender, Provider, ActionType, PlanStatus, AssessmentStatus types

**Document Manager (document_manager.py):**
- **Profile Operations**: create_profile(), update_profile(), get_user_profile()
- **Plan Management**: save_plan(), get_plan(), update_plan(), delete_plan(), get_multiple_plans()
- **Assessment Handling**: save_assessment(), get_single_assessment(), get_multiple_assessments()
- **Schedule Tasks**: create_schedule_task(), update_schedule_task_status(), get_overdue_schedule_tasks()
- **Score Management**: update_score(), increment_activity_done(), batch_update_scores()
- **Preference Processing**: extract_and_save_preferences_sync() with AWS Comprehend + Gemini AI
- **Data Storage**: Dual storage (S3 for documents, DynamoDB for metadata and indexing)

**Key Features:**
- **Dual Storage Architecture**: S3 for document storage, DynamoDB for fast queries and metadata
- **Pydantic Validation**: Type-safe data models with automatic validation and serialization
- **Assessment Scoring**: Automated FRAIL (0-5) and Rockwood-Mitnitski (0.0-1.0) frailty calculations
- **AI-Powered Preferences**: AWS Comprehend + Gemini AI for intelligent activity preference extraction
- **Schedule Monitoring**: Automated task tracking with cycle completion and score updates
- **Medical Search**: OpenSearch integration for semantic medical Q&A with 3-result limiting
- **Chat History**: Persistent conversation storage with S3 and DynamoDB metadata
- **Audit Trail**: Complete metadata tracking with timestamps, versions, and source attribution

#### message-layer (API Response Handling)
```
layers/message/python/
└── msg_helper.py       # API Gateway response formatting
```

**Key Features:**
- Standardized HTTP response formatting
- CORS header management
- Error response templates

#### ai-agent-layer (AI Agent System)
```
layers/ai-agent/python/
├── agent_tools.py        # Core tool orchestration and medical search
├── ai_agent.py          # LangChain-powered conversational agent
├── login_analytics.py   # User engagement tracking and re-engagement
├── aactt_utils.py       # AACTT plan generation with personalization
├── search_engine.py     # Internet search with Serper API integration
├── gemini_simple.py     # Gemini AI text generation with temperature control
├── weather_utils.py     # Weather data processing with WMO code mapping
├── profile_tools.py     # User profile management (2 tools)
├── plan_tools.py        # AACTT plan operations (7 tools)
├── assessment_tools.py  # Health assessment management (4 tools)
├── weather_tools.py     # Weather forecast services (2 tools)
└── additional_tools.py  # Utility functions (7 tools)
```

**Core AI Agent (ai_agent.py):**
- **GeminiAIAgent Class**: LangChain-powered conversational AI with native function calling
- **Model**: Gemini-2.0-flash-001 with temperature 0.2 for consistent responses
- **Tool Integration**: Automatic validation and binding of 23 tools across 5 categories
- **Conversation Memory**: Persistent chat history with 16-message context window
- **Function Calling**: Native Gemini function calling with automatic tool execution
- **Error Handling**: Comprehensive error recovery with graceful degradation
- **Chat History**: Integration with ChatHistoryManager for conversation persistence

**AACTT Plan Generation (aactt_utils.py):**
- **Personalized Planning**: User profile, assessment data, and preference integration
- **Action-Specific Instructions**: Tailored prompts for physical/mental/diet/medical activities
- **Assessment Integration**: FRAIL and Rockwood-Mitnitski data for plan customization
- **Diversity Engine**: Anti-repetition system with timestamp and random seeds
- **Fitness Scheduling**: Preferred workout times integration for physical activities
- **JSON Parsing**: Multi-strategy JSON extraction with fallback mechanisms
- **Plan Validation**: Comprehensive data cleaning and enum serialization

**Modular Tool System (23 Tools):**

**Profile Tools (2):**
- `get_user_profile`: Retrieve complete user profile data
- `update_user_profile`: Update profile fields with validation

**Plan Tools (7):**
- `generate_aactt_plan`: AI-powered personalized plan generation
- `get_user_plans`: Retrieve all user plans with status
- `get_plan_by_id`: Get specific plan details
- `activate_plan`: Change plan status to active
- `delete_plan`: Remove plan and related schedule tasks
- `check_existing_plans`: Validate plan uniqueness
- `get_plan_questions`: Interactive plan creation guidance

**Assessment Tools (4):**
- `get_frail_assessment_questions`: FRAIL scale questionnaire
- `get_rockwood_assessment_questions`: Rockwood-Mitnitski questionnaire
- `save_assessment_data`: Store assessment results with scoring
- `get_assessment_history`: Retrieve user assessment timeline

**Weather Tools (2):**
- `get_weather_forecast`: 7-day weather forecast with WMO code mapping
- `check_outdoor_weather_conditions`: Activity suitability analysis

**Additional Tools (7):**
- `get_current_time`: Current timestamp utility
- `explain_aactt_framework`: Framework education
- `calculate_bmi`: BMI calculation with categorization
- `internet_search`: Real-time web search (Serper API, 3 results, 20s timeout)
- `get_user_login_info`: Engagement status and login analytics
- `set_reminder`: Health reminder scheduling
- `find_nearby_healthcare`: Healthcare facility locator

**Supporting Utilities:**

**Gemini Integration (gemini_simple.py):**
- **GeminiSimple Class**: Direct Gemini API integration with configurable temperature
- **JSON Parsing**: Automatic JSON extraction from AI responses
- **Temperature Control**: Default 0.1 for consistency, 0.7 for creative plan generation
- **Error Recovery**: Robust error handling with retry mechanisms

**Weather Processing (weather_utils.py):**
- **WMO Code Mapping**: Complete weather code (0-99) to human-readable descriptions
- **Open-Meteo Integration**: Direct HTTP requests for weather data
- **Location Services**: GPS coordinate resolution for weather queries

**Internet Search (search_engine.py):**
- **Serper API Integration**: Real-time Google search results
- **BeautifulSoup Processing**: Content extraction and cleaning
- **Timeout Protection**: 20-second request timeout with graceful failure
- **Result Limiting**: Top 3 results for performance optimization

**User Analytics (login_analytics.py):**
- **Engagement Tracking**: Real-time user activity monitoring using JWT auth_time
- **Re-engagement System**: Automatic messaging for inactive users (72+ hours)
- **Login Analytics**: Comprehensive user engagement pattern analysis

**Key Technical Features:**
- **LangChain Integration**: Native function calling with tool validation and binding
- **Conversation Memory**: Persistent chat history with context-aware responses
- **Modular Architecture**: 23 tools organized across 5 domain-specific categories
- **AI-Powered Personalization**: Assessment data and user preferences integration
- **Real-time Data**: Weather, internet search, and user analytics integration
- **Error Resilience**: Comprehensive error handling with graceful degradation
- **Performance Optimization**: Timeout protection, result limiting, and efficient caching
- **Health Focus**: Specialized tools for wellness planning, assessments, and health monitoring

#### twilio-layer (SMS Notifications)
```
layers/twilio/
├── Dockerfile        # Docker build for cross-platform compatibility
├── build.sh         # Automated layer build script
├── requirements.txt # Twilio SDK dependencies
└── python/          # Built layer contents (generated)
    └── twilio/      # Twilio SDK package
```

**Key Features:**
- Cross-platform Twilio SDK (Docker-built for Linux Lambda runtime)
- SMS delivery with branded template support
- Automated build system for macOS development
- Template ID: HX978ad8c3cdea0479b3702721e3f36979 ("Livewell Assistant: {{1}}")

### Layer Management & Versioning

#### Current Architecture
- **Decentralized Management**: Each function manages its own layer versions in individual `sam.yaml` files
- **Manual Versioning**: Layer versions are hardcoded and must be updated manually
- **No Shared Configuration**: No centralized layer version management exists

#### Layer Version Updates
```bash
# 1. Build and deploy new layer version
cd AWS/lambda/layers/[layer-name]
sam build
sam deploy

# 2. Update version in each function's sam.yaml
# Example locations:
# - ai_agent_v2/sam.yaml
# - generate_aactt_plan/sam.yaml
# - get_profile/sam.yaml
# etc.

# 3. Deploy functions with new layer versions
cd ../functions/[function-name]
sam build
sam deploy
```

#### Layer Dependencies
```
Function Dependencies:
├── AI Functions (ai_agent_v2, chatbox_handler)
│   ├── aws-layer (v41)
│   ├── livewell-core-layer (v135)
│   ├── message-layer (v10)
│   └── ai-agent-layer (v140)
│
├── Legacy AI Function (ai_agent_v1) - uses archived toolkit-layer (v29)
│   └── ai-agent-layer (v140)
│
├── Profile Functions (get_profile, save_profile)
│   ├── aws-layer (v41)
│   ├── livewell-core-layer (v135)
│   └── message-layer (v10)
│
├── Planning Functions (generate_aactt_plan, save-plan)
│   ├── aws-layer (v41)
│   ├── message-layer (v10)
│   └── ai-agent-layer (v140)
│
└── Assessment Functions (get_assessment, save_assessment)
    ├── aws-layer (v41)
    ├── livewell-core-layer (v135)
    └── message-layer (v10)
```

#### Best Practices
- **Version Consistency**: Ensure all functions use compatible layer versions
- **Testing**: Test layer changes with dependent functions before deployment
- **Documentation**: Update version numbers in this README when layers are updated
- **Rollback Plan**: Keep previous layer versions available for quick rollbacks

## Lambda Functions

### AI & Chat Functions
- **ai_agent_v1**: Basic Gemini chatbot with conversation history
- **ai_agent_v2**: Advanced AI agent with function calling and JWT login tracking
- **chatbox_handler**: Simple Gemini API wrapper
- **get_chat_history**: Retrieve chat conversation history
- **remove_chat_history**: Delete chat conversation history

### User Management
- **get_profile**: Retrieve user profile data
- **save_profile**: Save user profile data
- **get_session**: Session management
- **preference_extraction_handler**: User preference processing

### Health Planning (AACTT)
- **generate_aactt_plan**: AI-powered AACTT plan generation with personalization
- **save-plan**: Save AACTT plans
- **get-plan**: Retrieve saved plans
- **update-plan**: Update existing plans
- **delete-plan**: Delete plans

### Health Assessments
- **get_assessment**: Retrieve user assessments
- **save_assessment**: Save user assessment data (FRAIL, ROCKWOOD_MITNITSKI)
- **get_assessment_ques**: Get assessment questions

### Weather & Environment
- **get_weather_forecast**: Weather data for outdoor activities
- **outdoor_weather_check**: Weather suitability analysis

### Medical Knowledge
- **medical-search**: Medical Q&A search using OpenSearch

### Authentication & Security
- **refresh_token**: Token refresh handling
- **create_oauth_user**: OAuth user creation
- **refresh_oauth_token**: OAuth token refresh

### Gamification & Engagement
- **get-leaderboard**: User leaderboard and rankings
- **increment-activity**: Track user activity increments
- **update-score**: Update user scores

### Task Scheduling
- **get-schedule-tasks**: Retrieve scheduled tasks
- **update-schedule-task-status**: Update task completion status
- **schedule-processor**: Process scheduled activities

### SMS Notifications
- **send-sms-notification**: Send SMS notifications using Twilio API with branded templates

### System Operations
- **connection_test**: System health checks and connectivity testing

## Key Features

### Key System Features
- **AI Chat System**: LangChain-powered conversational AI with 23 tools across 5 categories
- **Health Planning**: AACTT framework with personalized recommendations and weather integration
- **Health Assessments**: FRAIL and Rockwood-Mitnitski assessments with automated scoring
- **Medical Knowledge**: OpenSearch-powered Q&A with semantic search
- **Authentication**: Cognito user pools with JWT validation and OAuth integration
- **Real-time Analytics**: User engagement tracking with automated re-engagement messaging

## API Endpoints

For comprehensive API documentation including request/response schemas, authentication requirements, and example usage, please refer to our complete Postman documentation:

**📚 [LiveWell API Documentation](https://documenter.getpostman.com/view/8139210/2sB3BBqsFV)**

The documentation includes detailed information for all endpoints across the following categories:

### **Core API Categories:**
- **User Management**: Profile operations, session management, preference extraction
- **AI & Chat**: Conversational AI, chat history, function calling capabilities
- **Health Planning**: AACTT plan generation, management, and activation
- **Health Assessments**: FRAIL and Rockwood assessments with scoring
- **Medical Knowledge**: OpenSearch-powered medical Q&A
- **Weather & Environment**: Forecast and outdoor activity suitability
- **Authentication**: Token management and OAuth integration
- **Gamification**: Leaderboards, activity tracking, and scoring
- **Task Scheduling**: Automated task processing and status updates
- **SMS Notifications**: Twilio-powered messaging with templates
- **System Operations**: Health checks and connectivity testing

### **Key Features:**
- **Interactive Examples**: Test endpoints directly from the documentation
- **Request/Response Schemas**: Complete data models and validation rules
- **Authentication Guide**: JWT token usage and Cognito integration
- **Error Handling**: Comprehensive error codes and troubleshooting
- **Code Samples**: Multiple programming language examples
- **Environment Variables**: Configuration for different deployment stages

## Deployment

### Deploy Lambda Functions & Layers
```bash
cd backend/AWS
./yaml_lambda_deploy.sh <function_name/layer_name>

# Or use SAM directly
cd AWS/lambda/functions/<function-name>
sam build && sam deploy --guided
```

### Configuration
```bash
cd backend/AWS/shared
# Edit config.py with your settings
```

## Configuration

### Environment Variables
```bash
AWS_REGION=us-east-1
AWS_PROFILE=account2
GEMINI_API_KEY=your_key_here
```

### DynamoDB Schema
- PK: `USER#{user_id}`, `CHAT_HISTORY#{session_id}`, `SCHEDULE#{user_id}`
- SK: Various entity types (PROFILE, PLAN#{id}, ASSESSMENT#{id}, TASK#{id}, etc.)
- GSI for efficient querying

## Required AWS Resources

### Core Services
- **API Gateway**: RESTful API endpoints for all functions
- **Lambda**: 25+ serverless functions for business logic
- **DynamoDB**: NoSQL database for data storage
- **S3**: Object storage for files and documents
- **Cognito**: User authentication and authorization
- **OpenSearch**: Medical knowledge base with semantic search

### Specific Resources
- **DynamoDB Table**: `livewell` - User profiles, plans, chat history, sessions, assessments
- **S3 Buckets**: 
  - `livewell-profiles` - User profile data
  - `livewell-plans` - AACTT plan data
  - `livewell-chathistory` - Chat conversation history
  - `livewell-audio-bucket` - Audio files for speech processing
- **Cognito User Pool**: User authentication with JWT tokens
- **Lambda Layers**: 5 shared layers for common functionality
- **OpenSearch Domain**: Medical Q&A knowledge base

### External Integrations
- **Gemini AI API**: AI chat and plan generation
- **Open-Meteo API**: Weather data services
- **Google Geocoding API**: Location services
- **Serper API**: Real-time internet search with Google results
- **Twilio API**: SMS notifications with branded templates
- **OAuth Providers**: Third-party authentication

## Directory Structure
```
backend/
├── AWS/
│   ├── lambda/
│   │   ├── functions/
│   │   │   ├── ai_agent_v1/              # Legacy AI chatbot
│   │   │   ├── ai_agent_v2/              # Main AI chatbot with JWT tracking
│   │   │   ├── chatbox_handler/          # Simple Gemini wrapper
│   │   │   ├── get_profile/              # Profile retrieval
│   │   │   ├── save_profile/             # Profile saving
│   │   │   ├── get_session/              # Session management
│   │   │   ├── get_chat_history/         # Chat history retrieval
│   │   │   ├── remove_chat_history/      # Chat history deletion
│   │   │   ├── generate_aactt_plan/      # AACTT generation
│   │   │   ├── plans/
│   │   │   │   ├── save-plan/            # Plan saving
│   │   │   │   ├── get-plan/             # Plan retrieval
│   │   │   │   ├── update-plan/          # Plan updates
│   │   │   │   └── delete-plan/          # Plan deletion
│   │   │   ├── get_assessment/           # Assessment retrieval
│   │   │   ├── save_assessment/          # Assessment saving
│   │   │   ├── get_assessment_ques/      # Assessment questions
│   │   │   ├── get_weather_forecast/     # Weather API
│   │   │   ├── outdoor_weather_check/    # Weather suitability
│   │   │   ├── medical-search/           # Medical Q&A search
│   │   │   ├── refresh_token/            # Token refresh
│   │   │   ├── create_oauth_user/        # OAuth user creation
│   │   │   ├── refresh_oauth_token/      # OAuth token refresh
│   │   │   ├── get-leaderboard/          # User rankings
│   │   │   ├── increment-activity/       # Activity tracking
│   │   │   ├── update-score/             # Score updates
│   │   │   ├── get-schedule-tasks/       # Scheduled tasks
│   │   │   ├── update-schedule-task-status/ # Task status updates
│   │   │   ├── schedule-processor/       # Schedule processing
│   │   │   ├── preference_extraction_handler/ # Preference processing
│   │   │   ├── send-sms-notification/    # SMS notifications
│   │   │   └── connection_test/          # Health checks
│   │   ├── layers/
│   │   │   ├── aws/python/               # AWS helpers
│   │   │   ├── livewell-core/python/     # Core schemas & managers
│   │   │   ├── message/python/           # Response formatting
│   │   │   ├── toolkit/python/           # Utilities
│   │   │   ├── ai-agent/python/          # AI agent tools
│   │   │   └── twilio/                   # SMS notifications layer
│   │   ├── deploy_layers.py              # Layer deployment script
│   │   └── yaml_lambda_deploy.sh         # Deployment script
│   ├── cognito/                          # User pool setup
│   ├── dynamodb/                         # Database setup
│   ├── iam/                              # IAM roles and policies
│   ├── opensearch/                       # Search domain setup
│   ├── S3/                               # Bucket setup
│   ├── ses/                              # Email service
│   ├── shared/
│   │   └── config.py                     # Configuration settings
│   └── auto_update_versions.py           # Version management
└── README.md
```

## Troubleshooting

```bash
# Check CloudFormation events
aws cloudformation describe-stack-events --stack-name <stack-name>

# Delete failed stack
aws cloudformation delete-stack --stack-name <stack-name>

# View function logs
aws logs tail /aws/lambda/[function-name] --follow

# Cleanup deployments
cd backend/AWS/lambda
python undo_deploy_lambda.py
```

