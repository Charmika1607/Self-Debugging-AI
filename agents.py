import ollama


def debugger_agent(code):
    prompt = f"""
You are an expert Python Debugger Agent.

Analyze the Python code below carefully.

Your tasks:

1. Identify whether there is a Syntax Error.
2. Identify whether there is a Runtime Error.
3. Identify whether there is a Logical Error.
4. If there is an error, give the exact error type when possible.
5. Explain why the error occurs.
6. Suggest a clear fix.

IMPORTANT RULES:

- Do NOT call a TypeError, NameError, IndexError, or other runtime exception a SyntaxError.
- SyntaxError means Python cannot parse the code.
- Runtime errors happen while the program is executing.
- Logical errors mean the program runs but does not behave as intended.
- If there is no error in a category, clearly say "None".
- Do not rewrite the complete program.
- Give only diagnosis and a suggested fix.

Python code:

{code}
"""

    response = ollama.chat(
        model="qwen2.5-coder:7b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response["message"]["content"]


def repair_agent(code, error_report):
    prompt = f"""
You are an expert Python Repair Agent.

Your job is to repair the ORIGINAL Python code using the
DEBUGGER REPORT.

Original Python code:
{code}

Debugger report:
{error_report}

IMPORTANT RULES:

1. Fix ONLY the actual error identified by the debugger.
2. Preserve the original purpose and structure of the program.
3. Do NOT add unnecessary code.
4. Do NOT invent values unless absolutely necessary.
5. Do NOT change variables that are already correct.
6. Do NOT change the program's intended behavior.
7. If the problem is a runtime error, make the smallest reasonable fix.
8. If the problem is a syntax error, make only the syntax correction needed.
9. If the code is already correct, return the original code unchanged.
10. Return ONLY valid Python code.
11. Do NOT include explanations.
12. Do NOT use Markdown code fences such as ```python or ```.
13. Do NOT include comments explaining your repair unless the original code already had them.

Before returning the code, mentally verify that:
- The code is valid Python.
- The identified error is fixed.
- No new error has been introduced.
- The original purpose is preserved.

Return ONLY the repaired Python code.
"""

    response = ollama.chat(
        model="qwen2.5-coder:7b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    repaired_code = response["message"]["content"].strip()

    # Remove Markdown code fences if the model accidentally adds them
    if repaired_code.startswith("```"):
        lines = repaired_code.splitlines()

        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        repaired_code = "\n".join(lines).strip()

    return repaired_code


def testing_agent(code):
    import subprocess
    import sys
    import tempfile
    import os

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py",
            delete=False,
            encoding="utf-8"
        ) as file:

            file.write(code)
            file_path = file.name

        result = subprocess.run(
            [sys.executable, file_path],
            capture_output=True,
            text=True,
            timeout=5
        )

        os.remove(file_path)

        if result.returncode == 0:
            return {
                "success": True,
                "output": result.stdout,
                "error": ""
            }

        return {
            "success": False,
            "output": result.stdout,
            "error": result.stderr
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": "",
            "error": "Program timed out."
        }

    except Exception as e:
        return {
            "success": False,
            "output": "",
            "error": str(e)
        }


def critic_agent(original_code, error_report, repaired_code, test_result):
    prompt = f"""
You are a Code Verification and Critic Agent.

Your job is to determine whether the repaired Python code is a
reasonable and correct fix for the original problem.

You will receive:

1. Original Python code
2. Debugger Agent's error report
3. Repaired Python code
4. Testing Agent's result

Original code:
{original_code}

Debugger report:
{error_report}

Repaired code:
{repaired_code}

Testing result:
{test_result}

Analyze the repair carefully.

Rules:

- Check whether the reported error was actually fixed.
- Check whether the repaired code runs successfully.
- Check whether the repair preserves the likely purpose of the original code.
- Do not accept a repair just because it runs.
- Look for unnecessary or suspicious changes.
- Check whether the repaired code is valid Python.
- If the original code was already correct, do not require unnecessary changes.

If the repair is reasonable, return exactly:
APPROVED

If the repair is not reasonable, return exactly:
REJECTED

Then give a short explanation after the decision.
"""

    response = ollama.chat(
        model="qwen2.5-coder:7b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response["message"]["content"]