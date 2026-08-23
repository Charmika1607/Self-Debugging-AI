# 🤖 Self-Debugging AI

A local AI-powered Python debugging system that automatically detects errors,
repairs the code, tests the repaired code, and verifies the repair using
multiple AI agents.

## 📌 Problem Statement

Debugging programming errors manually can take time, especially when the
error message is difficult to understand.

This project aims to build an AI-based system that can automatically analyze
Python code, identify errors, generate a repair, test the repaired code, and
verify whether the repair is reasonable.

## 🎯 Objective

The main objectives of this project are:

- Detect errors in Python programs.
- Explain the detected errors.
- Automatically generate corrected code.
- Test the repaired code.
- Verify the repair using a Critic Agent.
- Retry the repair when the Critic Agent rejects it.
- Run the AI locally without depending on paid API credits.

## 🧠 Multi-Agent Architecture

The project uses four agents:

### 1. 🔍 Debugger Agent

Analyzes the Python code and identifies:

- Syntax errors
- Runtime errors
- Logical errors
- Error types
- Possible fixes

### 2. 🔧 Repair Agent

Uses the debugging report to generate corrected Python code.

The Repair Agent is instructed to:

- Fix only the actual error.
- Preserve the original purpose.
- Avoid unnecessary changes.
- Return valid Python code.

### 3. 🧪 Testing Agent

Runs the repaired Python code in a temporary file.

It checks:

- Whether the program runs successfully.
- Program output.
- Runtime errors.
- Timeouts.

### 4. 🧠 Critic Agent

Reviews the repaired code and decides whether the repair is reasonable.

The Critic Agent checks:

- Whether the original error was fixed.
- Whether the repaired code runs successfully.
- Whether the original purpose was preserved.
- Whether unnecessary changes were introduced.

The Critic returns:

- `APPROVED`
- `REJECTED`

If the repair is rejected, the system attempts another repair.

## 🔄 System Workflow

```text
              Python Code
                   │
                   ▼
          🔍 Debugger Agent
                   │
                   ▼
             Error Report
                   │
                   ▼
           🔧 Repair Agent
                   │
                   ▼
            Repaired Code
                   │
                   ▼
          🧪 Testing Agent
                   │
                   ▼
             Test Result
                   │
                   ▼
           🧠 Critic Agent
              │       │
          APPROVED   REJECTED
              │       │
              ▼       ▼
           SUCCESS   RETRY
🛠️ Technologies Used
Python
Ollama
Qwen2.5-Coder 7B
VS Code
Python Virtual Environment
Subprocess
Temporary files
💻 Requirements

Before running the project, make sure you have:

Python installed
Ollama installed
Qwen2.5-Coder 7B model downloaded
VS Code (recommended)
📦 Ollama Model

This project uses:

qwen2.5-coder:7b

The model runs locally through Ollama.

▶️ How to Run

Activate the virtual environment:

.\venv\Scripts\Activate.ps1

Then run:

python main.py

Enter your Python code and type:

END
on a new line when finished.

🧪 Example
Input
name = "Charmika"
age = 19

result = name + age
print(result)
Detected Error
TypeError

The Debugger Agent identifies that a string and integer cannot be directly
concatenated using +.

Repaired Code
name = "Charmika"
age = 19

result = name + str(age)
print(result)
Testing Result
✅ Status: PASSED

Program Output:
Charmika19
Critic Result
APPROVED
Final Result
🎉 SELF-DEBUGGING SUCCESSFUL
🧪 Tested Error Types

The system has been tested with:
| Error Type  | Result   |
| ----------- | -------- |
| NameError   | ✅ Passed |
| TypeError   | ✅ Passed |
| SyntaxError | ✅ Passed |
| IndexError  | ✅ Passed |
📁 Project Structure
Self_Debugging_AI/
│
├── main.py
├── agents.py
├── README.md
├── .gitignore
│
└── venv/
The virtual environment should not be uploaded to GitHub.

🔐 Security

Sensitive information such as API keys should not be stored directly in
the source code.

The .env file should remain in .gitignore.

🚀 Future Improvements

Possible future improvements include:

Graphical User Interface (GUI)
Support for more programming languages
Better error classification
Code quality analysis
Automatic test-case generation
Code explanation
Repair history
Web-based interface
Performance optimization
More advanced local coding models
👩‍💻 Project Status

Current status:

Working Prototype ✅

The current system can analyze, repair, test, and verify Python code using
a local multi-agent AI pipeline.



