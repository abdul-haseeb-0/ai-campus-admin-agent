# AI Campus Admin Agent

An intelligent campus administration assistant powered by OpenAI Agent SDK with function tools for student management, analytics, and campus information.

## 🚀 Features

### 📌 Student Management
- **add_student(name, student_id, department, email)** - Add new students to the database
- **get_student(student_id)** - Retrieve student information by ID
- **update_student(student_id, field, new_value)** - Update student details
- **delete_student(student_id)** - Remove students from the system
- **list_students()** - Get all students

### 📊 Campus Analytics
- **get_total_students()** - Get total student counts with active/inactive breakdown
- **get_students_by_department()** - View student distribution by department
- **get_recent_onboarded_students(limit=5)** - Find recently onboarded students
- **get_active_students_last_7_days()** - Track students active in the last 7 days

### 🏫 Campus FAQ
- **get_cafeteria_timings()** - Get cafeteria operating hours
- **get_library_hours()** - Get library hours and study room access

## 🛠️ Setup

### Prerequisites
- Python 3.13+
- PostgreSQL database
- Gemini API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd campus-admin-agent
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -e .
   ```

4. **Environment setup**
   Create a `.env` file in the root directory:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   DATABASE_URL=postgresql://username:password@localhost:5432/campus_db
   ```

5. **Database setup**
   ```bash
   python backend/db.py  # Creates tables
   ```

## 🎯 Usage

### Interactive Agent
```bash
python backend/agent.py
```

### Test Function Tools
```bash
python test_agent.py
```

### Example Queries
- "Add a new student named John Doe with ID 12345 in Computer Science department"
- "Get information about student 12345"
- "Show me the total number of students"
- "What are the cafeteria hours?"
- "List all students in the Engineering department"

## 🏗️ Architecture

### Function Tools with OpenAI Agent SDK
The agent uses the `@function_tool` decorator to automatically:
- **Discover tools**: Agent automatically finds all decorated functions
- **Call tools**: Agent decides when and how to use each tool
- **Handle errors**: Built-in error handling and retry logic
- **Manage context**: Maintains conversation history across interactions

### Database Models
- **Student**: Core student information with activity tracking
- **ActivityLog**: Audit trail for all student-related actions

### Agent Loop
1. **LLM Invocation**: Agent calls Gemini model with conversation history
2. **Tool Selection**: Agent determines which tools to use based on user query
3. **Tool Execution**: Functions are called with proper parameters
4. **Response Generation**: Agent formats results into natural language
5. **Context Update**: Conversation history is maintained for follow-up questions

## 🔧 Development

### Adding New Function Tools
1. Create a new function in `backend/tools.py`
2. Add the `@function_tool` decorator
3. Include proper docstring with Args and Returns
4. Import the function in `backend/agent.py`
5. The agent will automatically discover and use the new tool

### Example New Tool
```python
@function_tool
def get_student_gpa(student_id: str) -> Dict[str, Any]:
    """Get student's GPA
    
    Args:
        student_id: Unique student identifier
        
    Returns:
        Dictionary with success status and GPA information
    """
    # Implementation here
    pass
```

## 📝 API Reference

All function tools follow the same pattern:
- **Input**: Type-hinted parameters with clear names
- **Output**: Dictionary with `success` boolean and relevant data
- **Error Handling**: Graceful error handling with meaningful messages
- **Logging**: Activity logging for audit trails

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add your function tools with proper documentation
4. Test with the interactive agent
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.
