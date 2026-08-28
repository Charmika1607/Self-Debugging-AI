# 🤖 Self-Debugging AI

A local AI-powered Python debugging system that can automatically analyze,
repair, test, and verify Python programs using a multi-agent architecture.

The system combines deterministic Python analysis with a local Large
Language Model (LLM) running through Ollama.

---

## 📌 Problem Statement

Debugging programming errors manually can be time-consuming, especially
when error messages are difficult to understand or when a generated repair
introduces a new problem.

This project aims to build an intelligent Python debugging system that can:

- Detect programming errors
- Explain detected errors
- Generate possible repairs
- Validate generated repairs
- Execute and test repaired code
- Verify whether the repair preserves the original intent
- Reject unsafe repairs
- Retry failed repairs when appropriate

A key design goal is **safe code repair**. The system should not invent
unknown values simply to make a program execute successfully.

---

## 🎯 Objectives

The main objectives of this project are:

- Detect Syntax Errors, Runtime Errors, and Logical Errors.
- Identify common Runtime Errors such as `NameError`, `TypeError`,
  `IndexError`, `KeyError`, `ZeroDivisionError`, and `AttributeError`.
- Explain why an error occurs.
- Automatically generate corrected Python code.
- Validate repaired code before execution.
- Execute repaired code in an isolated temporary file.
- Verify the repair using a Critic Agent.
- Detect potentially unsafe or unjustified repairs.
- Retry rejected repairs when another attempt may be useful.
- Avoid inventing unknown values.
- Run the AI locally using Ollama and Qwen2.5-Coder.

---

## 🧠 Multi-Agent Architecture

The system uses multiple intelligent components working together.

### 1. 🔍 Debugger Agent

The Debugger Agent analyzes the original Python code and identifies:

- Syntax Errors
- Runtime Errors
- Logical Errors
- Exact error types
- Possible causes
- Suggested repairs

For common cases such as undefined variables and missing function
arguments, deterministic Python analysis is performed before relying on
the LLM.

---

### 2. 🔧 Repair Agent

The Repair Agent generates corrected Python code based on the debugging
information.

It is instructed to:

- Fix only the actual problem.
- Preserve the original purpose.
- Preserve correct code.
- Make minimal changes.
- Avoid unrelated modifications.
- Avoid inventing values.
- Return valid Python code.

For some error classes, deterministic repair logic is used instead of
allowing the LLM to freely modify the code.

---

### 3. 🛡️ Repair Validator

The Repair Validator performs static validation of the generated repair.

It checks:

- Whether the repaired code is valid Python.
- Whether undefined variables remain.
- Whether suspicious values were introduced.
- Whether unsafe repairs were generated.
- Whether missing information was incorrectly guessed.

This layer prevents the system from accepting a repair merely because
the code happens to run.

---

### 4. 🧪 Testing Agent

The Testing Agent executes the repaired Python program in a temporary file.

It checks:

- Successful execution
- Program output
- Runtime errors
- Syntax errors during execution
- Timeouts

The temporary file is removed after testing.

---

### 5. 🧠 Critic Agent

The Critic Agent performs the final verification of a repair.

It checks:

- Whether the original error was actually fixed.
- Whether the repaired code is valid Python.
- Whether the repaired code runs successfully.
- Whether the original purpose is preserved.
- Whether the meaning of operators is preserved.
- Whether unnecessary changes were introduced.
- Whether arbitrary values were invented.
- Whether the repaired program is semantically reasonable.

The Critic returns:

```text
APPROVED