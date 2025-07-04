import sqlite3
import logging
from datetime import datetime, timedelta
from langchain_community.llms import Ollama
from langchain.agents import initialize_agent, Tool
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate

# Set up logging for error handling
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize SQLite database
def init_db():
    """Initialize SQLite database and create tasks table if it doesn't exist."""
    try:
        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT NOT NULL,
                due_date TEXT,
                status TEXT DEFAULT 'Pending'
            )
        ''')
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        logger.error(f"Database initialization error: {e}")

# Custom tools for task management
def add_task(task_description, due_date=None):
    """Add a task to the SQLite database."""
    try:
        # Parse due_date (e.g., 'tomorrow' or 'next week')
        if due_date and due_date.lower() in ['tomorrow', 'next week']:
            if due_date.lower() == 'tomorrow':
                due_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            elif due_date.lower() == 'next week':
                due_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        
        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO tasks (task, due_date, status) VALUES (?, ?, ?)",
                      (task_description, due_date, 'Pending'))
        conn.commit()
        conn.close()
        return f"Task '{task_description}' added with due date {due_date or 'None'}."
    except sqlite3.Error as e:
        logger.error(f"Error adding task: {e}")
        return "Error adding task to database."

def query_tasks(status='Pending'):
    """Query tasks from the SQLite database by status."""
    try:
        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, task, due_date, status FROM tasks WHERE status = ?", (status,))
        tasks = cursor.fetchall()
        conn.close()
        if not tasks:
            return "No tasks found."
        return [{"id": t[0], "task": t[1], "due_date": t[2], "status": t[3]} for t in tasks]
    except sqlite3.Error as e:
        logger.error(f"Error querying tasks: {e}")
        return "Error querying tasks."

def delete_task(task_id):
    """Delete a task from the SQLite database by ID."""
    try:
        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()
        return f"Task with ID {task_id} deleted." if cursor.rowcount > 0 else f"Task with ID {task_id} not found."
    except sqlite3.Error as e:
        logger.error(f"Error deleting task: {e}")
        return "Error deleting task."

def reschedule_task(task_id, new_due_date):
    """Reschedule a task by updating its due date."""
    try:
        # Parse new_due_date (e.g., 'tomorrow' or 'next week')
        if new_due_date.lower() in ['tomorrow', 'next week']:
            if new_due_date.lower() == 'tomorrow':
                new_due_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            elif new_due_date.lower() == 'next week':
                new_due_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        
        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE tasks SET due_date = ? WHERE id = ?", (new_due_date, task_id))
        conn.commit()
        conn.close()
        return f"Task with ID {task_id} rescheduled to {new_due_date}." if cursor.rowcount > 0 else f"Task with ID {task_id} not found."
    except sqlite3.Error as e:
        logger.error(f"Error rescheduling task: {e}")
        return "Error rescheduling task."
    

# Initialize Ollama model
llm = Ollama(model="mistral")

# Define tools for the agent - These are custom agents..!
tools = [
    Tool(
        name="AddTask",
        func=lambda x: add_task(x.split('|')[0], x.split('|')[1] if len(x.split('|')) > 1 else None),
        description="Add a task to the to-do list. Input format: 'task_description|due_date' (due_date is optional, e.g., 'tomorrow' or 'next week')."
    ),
    Tool(
        name="QueryTasks",
        func=lambda x: query_tasks(x if x else 'Pending'),
        description="Query tasks by status (e.g., 'Pending', 'Completed'). Defaults to 'Pending' if no status provided."
    ),
    Tool(
        name="DeleteTask",
        func=delete_task,
        description="Delete a task by its ID."
    ),
    Tool(
        name="RescheduleTask",
        func=lambda x: reschedule_task(int(x.split('|')[0]), x.split('|')[1]),
        description="Reschedule a task by ID and new due date. Input format: 'task_id|new_due_date' (e.g., '1|tomorrow')."
    )
]

# Set up memory to retain conversation context
memory = ConversationBufferMemory(memory_key="chat_history")

# Define prompt template for the agent
prompt_template = PromptTemplate(
    input_variables=["input", "chat_history"],
    template="""
    You are a To-Do List Agent that manages tasks by parsing natural language inputs.
    User input: {input}
    Chat history: {chat_history}
    
    Use the provided tools to add, query, delete, or reschedule tasks in an SQLite database.
    Parse inputs like 'Add a meeting tomorrow at 3 PM' or 'Reschedule my meeting to next week'.
    For ambiguous inputs, ask clarifying questions.
    Format the output as a markdown table listing tasks (ID, Task, Due Date, Status).
    """
)

# Initialize the agent
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent="zero-shot-react-description",
    memory=memory,
    verbose=True,
    handle_parsing_errors=True,
)


# Function to process user input
def process_task_input(user_input):
    """Process user input and return a formatted task list or response."""
    try:
        if not user_input:
            return "Please provide a task-related command."
        
        # Run the agent with the input
        response = agent.run(prompt_template.format(input=user_input, chat_history=memory.buffer))
        
        # Fetch current tasks for output
        tasks = query_tasks('Pending')
        if isinstance(tasks, str):  # Error case
            return tasks
        
        # Format tasks as markdown table
        table = """
## To-Do List

| ID | Task | Due Date | Status |
|----|------|----------|--------|
"""
        for task in tasks:
            table += f"| {task['id']} | {task['task']} | {task['due_date'] or 'None'} | {task['status']} |\n"
        
        return f"{response}\n{table}"
    except Exception as e:
        logger.error(f"Error processing input: {e}")
        return f"An error occurred: {str(e)}"

# Example usage
if __name__ == "__main__":
    init_db()  # Initialize database
    while True:
        user_input = input("Enter your task command (e.g., 'Add a meeting tomorrow at 3 PM' or 'quit' to exit): ")
        if user_input.lower() == 'quit':
            break
        result = process_task_input(user_input)
        print(result)