# To-Do List Agent

A smart To-Do List Agent built with Python, SQLite, and LangChain, powered by the Mistral model via Ollama. This project enables task management through natural language inputs, such as "Add a meeting tomorrow at 3 PM" or "Reschedule my meeting to next week." The agent stores tasks in an SQLite database, supports operations like adding, querying, deleting, and rescheduling tasks, and retains conversation context for seamless interaction.

## Features

- Natural Language Processing: Parse commands like "Add a task" or "Show pending tasks" using LangChain and Mistral.
- SQLite Database: Store tasks with ID, description, due date, and status.
- Custom Tools: Add, query, delete, and reschedule tasks with support for relative due dates (e.g., "tomorrow", "next week").
- Conversational Memory: Retains context for follow-up interactions.
- Error Handling: Robust logging for database and processing errors.

Markdown Output: Displays task lists in a formatted table.

## To-Do List

| ID | Task                     | Due Date   | Status  |
|----|--------------------------|------------|---------|
| 1  | Meeting tomorrow at 3 PM | 2025-07-05 | Pending |

Blog Post: 

Learn more about the implementation in my Medium blog post.

