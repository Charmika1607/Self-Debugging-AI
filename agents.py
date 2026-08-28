import ast
import builtins
import difflib
import os
import re
import subprocess
import sys
import tempfile
import ollama

MODEL_NAME = "qwen2.5-coder:7b"

BUILTIN_NAMES = set(dir(builtins))


# ============================================================
# HELPER
# ============================================================

def clean_code(code):
    if not isinstance(code, str):
        return ""

    code = code.strip()

    if code.startswith("```"):
        lines = code.splitlines()

        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        code = "\n".join(lines).strip()

    return code


# ============================================================
# GET DEFINED NAMES
# ============================================================

def get_defined_names(code):
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return set()

    defined = set()

    for node in ast.walk(tree):

        if isinstance(node, ast.Assign):

            for target in node.targets:

                if isinstance(target, ast.Name):
                    defined.add(target.id)

                elif isinstance(target, (ast.Tuple, ast.List)):

                    for element in target.elts:

                        if isinstance(element, ast.Name):
                            defined.add(element.id)

        elif isinstance(node, ast.AnnAssign):

            if isinstance(node.target, ast.Name):
                defined.add(node.target.id)

        elif isinstance(node, ast.AugAssign):

            if isinstance(node.target, ast.Name):
                defined.add(node.target.id)

        elif isinstance(node, ast.NamedExpr):

            if isinstance(node.target, ast.Name):
                defined.add(node.target.id)

        elif isinstance(node, (ast.For, ast.AsyncFor)):

            if isinstance(node.target, ast.Name):
                defined.add(node.target.id)

            elif isinstance(node.target, (ast.Tuple, ast.List)):

                for element in node.target.elts:

                    if isinstance(element, ast.Name):
                        defined.add(element.id)

        elif isinstance(node, (ast.With, ast.AsyncWith)):

            for item in node.items:

                if (
                    item.optional_vars
                    and isinstance(item.optional_vars, ast.Name)
                ):
                    defined.add(item.optional_vars.id)

        elif isinstance(node, ast.ExceptHandler):

            if node.name:
                defined.add(node.name)

        elif isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef)
        ):

            defined.add(node.name)

            for arg in node.args.posonlyargs:
                defined.add(arg.arg)

            for arg in node.args.args:
                defined.add(arg.arg)

            for arg in node.args.kwonlyargs:
                defined.add(arg.arg)

            if node.args.vararg:
                defined.add(node.args.vararg.arg)

            if node.args.kwarg:
                defined.add(node.args.kwarg.arg)

        elif isinstance(node, ast.ClassDef):

            defined.add(node.name)

        elif isinstance(node, ast.Import):

            for alias in node.names:

                defined.add(
                    alias.asname or alias.name.split(".")[0]
                )

        elif isinstance(node, ast.ImportFrom):

            for alias in node.names:

                if alias.name != "*":

                    defined.add(
                        alias.asname or alias.name
                    )

    return defined


# ============================================================
# FIND UNDEFINED NAMES
# ============================================================

def find_undefined_names(code):
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    defined = get_defined_names(code)
    undefined = set()

    for node in ast.walk(tree):

        if isinstance(node, ast.Name):

            if isinstance(node.ctx, ast.Load):

                name = node.id

                if name in BUILTIN_NAMES:
                    continue

                if name not in defined:
                    undefined.add(name)

    return sorted(undefined)


# ============================================================
# FIND SIMILAR VARIABLE
# ============================================================

def find_similar_variable(undefined_name, defined_names):
    candidates = []

    for name in defined_names:

        if name in BUILTIN_NAMES:
            continue

        similarity = difflib.SequenceMatcher(
            None,
            undefined_name.lower(),
            name.lower()
        ).ratio()

        candidates.append(
            (
                similarity,
                name
            )
        )

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: (
            -item[0],
            item[1]
        )
    )

    best_similarity = candidates[0][0]
    best_name = candidates[0][1]

    if best_similarity >= 0.75:
        return best_name

    return None


# ============================================================
# REPLACE VARIABLE NAME
# ============================================================

def replace_name(code, old_name, new_name):
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None

    lines = code.splitlines()
    replacements = []

    for node in ast.walk(tree):

        if isinstance(node, ast.Name):

            if (
                node.id == old_name
                and isinstance(node.ctx, ast.Load)
            ):

                replacements.append(
                    (
                        node.lineno,
                        node.col_offset,
                        node.end_lineno,
                        node.end_col_offset
                    )
                )

    if not replacements:
        return None

    replacements.sort(
        reverse=True
    )

    for (
        start_line,
        start_col,
        end_line,
        end_col
    ) in replacements:

        if start_line != end_line:
            continue

        index = start_line - 1

        if index < 0 or index >= len(lines):
            continue

        line = lines[index]

        lines[index] = (
            line[:start_col]
            + new_name
            + line[end_col:]
        )

    return "\n".join(lines)


# ============================================================
# MISSING FUNCTION ARGUMENT DETECTOR
# ============================================================

def find_missing_function_arguments(code):
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    functions = {}

    for node in ast.walk(tree):

        if isinstance(node, ast.FunctionDef):

            positional_args = (
                node.args.posonlyargs
                + node.args.args
            )

            defaults = len(node.args.defaults)

            required_count = (
                len(positional_args) - defaults
            )

            required_names = [
                arg.arg
                for arg in positional_args[:required_count]
            ]

            functions[node.name] = {
                "required_names": required_names,
                "required_count": required_count
            }

        elif isinstance(node, ast.AsyncFunctionDef):

            positional_args = (
                node.args.posonlyargs
                + node.args.args
            )

            defaults = len(node.args.defaults)

            required_count = (
                len(positional_args) - defaults
            )

            required_names = [
                arg.arg
                for arg in positional_args[:required_count]
            ]

            functions[node.name] = {
                "required_names": required_names,
                "required_count": required_count
            }

    missing = []

    for node in ast.walk(tree):

        if not isinstance(node, ast.Call):
            continue

        if not isinstance(node.func, ast.Name):
            continue

        function_name = node.func.id

        if function_name not in functions:
            continue

        function_info = functions[function_name]

        required_names = function_info["required_names"]
        required_count = function_info["required_count"]

        positional_provided = len(node.args)

        # A call with fewer positional arguments than required.
        if positional_provided < required_count:

            missing_names = required_names[
                positional_provided:
            ]

            missing.append(
                {
                    "function": function_name,
                    "required_count": required_count,
                    "provided_count": positional_provided,
                    "missing_names": missing_names
                }
            )

    return missing


# ============================================================
# DETERMINISTIC NAMEERROR REPAIR
# ============================================================

def deterministic_nameerror_repair(code):
    undefined_names = find_undefined_names(code)

    if not undefined_names:

        return {
            "status": "NO_NAMEERROR",
            "code": None,
            "reason": "No undefined variable was detected."
        }

    defined_names = get_defined_names(code)

    for undefined_name in undefined_names:

        similar_name = find_similar_variable(
            undefined_name,
            defined_names
        )

        if similar_name:

            repaired_code = replace_name(
                code,
                undefined_name,
                similar_name
            )

            if repaired_code:

                return {
                    "status": "REPAIRED",
                    "code": repaired_code,
                    "reason": (
                        f"Detected probable typo: "
                        f"'{undefined_name}' -> "
                        f"'{similar_name}'."
                    )
                }

    return {
        "status": "UNSAFE",
        "code": None,
        "reason": (
            "The undefined variable could not be "
            "safely matched to an existing variable."
        )
    }


# ============================================================
# DEBUGGER AGENT
# ============================================================

def debugger_agent(code):

    # --------------------------------------------------------
    # SyntaxError detection
    # --------------------------------------------------------

    try:
        ast.parse(code)

    except SyntaxError as e:

        return (
            "Syntax Error: SyntaxError\n"
            f"Line: {e.lineno}\n"
            f"Message: {e.msg}\n\n"
            "Runtime Error: Not evaluated because "
            "the code contains a syntax error.\n\n"
            "Logical Error: Not evaluated.\n\n"
            "Suggested Fix:\n"
            "Fix only the syntax error."
        )

    # --------------------------------------------------------
    # NameError detection
    # --------------------------------------------------------

    undefined_names = find_undefined_names(code)

    if undefined_names:

        return (
            "Syntax Error: None\n\n"
            "Runtime Error: NameError\n\n"
            "Undefined variable(s): "
            + ", ".join(undefined_names)
            + "\n\n"
            "Logical Error: None\n\n"
            "Explanation:\n"
            "The variable(s) are used but are not defined.\n\n"
            "Repair Requirement:\n"
            "First check whether the undefined variable "
            "is a typo of an existing variable.\n"
            "If an obvious existing variable match exists, "
            "replace the typo.\n"
            "Otherwise do NOT invent a value."
        )

    # --------------------------------------------------------
    # Missing function arguments
    # --------------------------------------------------------

    missing_arguments = find_missing_function_arguments(
        code
    )

    if missing_arguments:

        details = []

        for item in missing_arguments:

            details.append(
                (
                    f"Function '{item['function']}' requires "
                    f"{item['required_count']} argument(s), "
                    f"but only {item['provided_count']} "
                    "were provided. "
                    "Missing argument(s): "
                    + ", ".join(item["missing_names"])
                    + "."
                )
            )

        return (
            "Syntax Error: None\n\n"
            "Runtime Error: TypeError\n\n"
            "Logical Error: None\n\n"
            "Explanation:\n"
            + "\n".join(details)
            + "\n\n"
            "Repair Requirement:\n"
            "Do NOT invent a value for the missing "
            "argument.\n"
            "The correct value cannot be determined "
            "from the original code."
        )

    # --------------------------------------------------------
    # Other errors -> Ollama
    # --------------------------------------------------------

    prompt = f"""
You are an expert Python Debugger Agent.

Analyze ONLY the ORIGINAL Python code.

Original Python code:
{code}

Identify:

1. Syntax Error
2. Runtime Error
3. Logical Error
4. Exact error type
5. Explanation
6. Suggested fix

IMPORTANT RULES:

- SyntaxError means Python cannot parse the code.
- NameError is a Runtime Error.
- TypeError is a Runtime Error.
- IndexError is a Runtime Error.
- KeyError is a Runtime Error.
- AttributeError is a Runtime Error.
- ZeroDivisionError is a Runtime Error.
- Do not call runtime errors SyntaxError.
- Do not invent values.
- Do not assume missing information.
- Do not rewrite the whole program.
- Clearly say None when a category has no error.
"""

    try:

        response = ollama.chat(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response["message"]["content"]

    except Exception as e:

        return (
            "Debugger Agent Error:\n"
            f"{e}"
        )


# ============================================================
# REPAIR AGENT
# ============================================================

def repair_agent(code, error_report):

    # --------------------------------------------------------
    # NameError repair
    # --------------------------------------------------------

    undefined_names = find_undefined_names(code)

    if undefined_names:

        result = deterministic_nameerror_repair(
            code
        )

        if result["status"] == "REPAIRED":

            return result["code"]

        # No safe repair
        return code

    # --------------------------------------------------------
    # Missing function arguments
    # --------------------------------------------------------

    missing_arguments = find_missing_function_arguments(
        code
    )

    if missing_arguments:

        # Never invent missing argument values.
        return code

    # --------------------------------------------------------
    # Other errors -> Ollama
    # --------------------------------------------------------

    prompt = f"""
You are an expert Python Repair Agent.

Original Python code:
{code}

Debugger report:
{error_report}

Repair ONLY the reported problem.

STRICT RULES:

1. Return ONLY valid Python code.
2. Do not use Markdown code fences.
3. Do not provide explanations.
4. Make the smallest reasonable repair.
5. Preserve the original purpose.
6. Preserve all correct code.
7. Do not invent values.
8. Do not guess missing values.
9. Never insert arbitrary values such as:
   0, 1, 10, 19, 20, 25, 30, None,
   "Unknown", or "unknown".
10. Do not invent missing function arguments.
11. Do not change unrelated operators.
12. Do not change unrelated variables.
13. Do not rewrite the entire program unnecessarily.
14. Do not add unnecessary input().
15. Make only changes supported by the original code
    and the debugger report.

Return ONLY the repaired Python code.
"""

    try:

        response = ollama.chat(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return clean_code(
            response["message"]["content"]
        )

    except Exception:

        return code


# ============================================================
# REPAIR VALIDATOR
# ============================================================

def repair_validator(
    original_code,
    repaired_code
):

    if not isinstance(
        repaired_code,
        str
    ):

        return {
            "valid": False,
            "reason": "Repair is not a string."
        }

    repaired_code = clean_code(
        repaired_code
    )

    if not repaired_code:

        return {
            "valid": False,
            "reason": "Repair returned empty code."
        }

    # --------------------------------------------------------
    # Repaired code must parse
    # --------------------------------------------------------

    try:

        ast.parse(repaired_code)

    except SyntaxError as e:

        return {
            "valid": False,
            "reason": (
                "Repaired code contains SyntaxError: "
                f"{e}"
            )
        }

    # --------------------------------------------------------
    # Original syntax error
    # --------------------------------------------------------

    try:

        ast.parse(original_code)

        original_has_syntax_error = False

    except SyntaxError:

        original_has_syntax_error = True

    if original_has_syntax_error:

        return {
            "valid": True,
            "reason": (
                "Original code contained a SyntaxError. "
                "The repaired code is valid Python."
            )
        }

    # --------------------------------------------------------
    # Original NameError
    # --------------------------------------------------------

    original_undefined = set(
        find_undefined_names(original_code)
    )

    if original_undefined:

        repaired_undefined = set(
            find_undefined_names(repaired_code)
        )

        remaining = (
            original_undefined
            & repaired_undefined
        )

        if remaining:

            return {
                "valid": False,
                "reason": (
                    "The repair still contains "
                    "undefined variable(s): "
                    + ", ".join(
                        sorted(remaining)
                    )
                )
            }

        # Verify an actual existing-name correction
        original_defined = get_defined_names(
            original_code
        )

        for undefined_name in original_undefined:

            possible_match = find_similar_variable(
                undefined_name,
                original_defined
            )

            if possible_match:

                if possible_match not in repaired_code:

                    return {
                        "valid": False,
                        "reason": (
                            f"The probable typo "
                            f"'{undefined_name}' was not "
                            f"corrected to "
                            f"'{possible_match}'."
                        )
                    }

            else:

                return {
                    "valid": False,
                    "reason": (
                        f"The variable "
                        f"'{undefined_name}' is undefined "
                        "and no safe existing-variable "
                        "match was found."
                    )
                }

        return {
            "valid": True,
            "reason": (
                "NameError was repaired by replacing "
                "the undefined variable with an "
                "existing matching variable."
            )
        }

    # --------------------------------------------------------
    # Original missing function arguments
    # --------------------------------------------------------

    original_missing = find_missing_function_arguments(
        original_code
    )

    if original_missing:

        repaired_missing = find_missing_function_arguments(
            repaired_code
        )

        if repaired_missing:

            return {
                "valid": False,
                "reason": (
                    "The repaired code still has "
                    "missing function arguments."
                )
            }

        # If the repair added an argument, make sure it
        # wasn't a guessed constant.
        try:

            repaired_tree = ast.parse(
                repaired_code
            )

        except SyntaxError:

            return {
                "valid": False,
                "reason": (
                    "Repaired code could not be parsed."
                )
            }

        original_tree = ast.parse(
            original_code
        )

        original_call_count = {}

        for node in ast.walk(
            original_tree
        ):

            if isinstance(
                node,
                ast.Call
            ):

                if isinstance(
                    node.func,
                    ast.Name
                ):

                    original_call_count.setdefault(
                        node.func.id,
                        []
                    ).append(
                        len(node.args)
                    )

        for node in ast.walk(
            repaired_tree
        ):

            if not isinstance(
                node,
                ast.Call
            ):
                continue

            if not isinstance(
                node.func,
                ast.Name
            ):
                continue

            function_name = node.func.id

            if function_name not in original_call_count:
                continue

            original_counts = original_call_count[
                function_name
            ]

            for original_count in original_counts:

                if len(node.args) > original_count:

                    new_args = node.args[
                        original_count:
                    ]

                    for argument in new_args:

                        if isinstance(
                            argument,
                            ast.Constant
                        ):

                            return {
                                "valid": False,
                                "reason": (
                                    "The repair added a "
                                    "constant value as a "
                                    "missing function "
                                    "argument. The value "
                                    "was not provided by "
                                    "the original code."
                                )
                            }

        return {
            "valid": True,
            "reason": (
                "Missing function argument issue "
                "was repaired without blindly "
                "inserting a constant value."
            )
        }

    # --------------------------------------------------------
    # General validation
    # --------------------------------------------------------

    return {
        "valid": True,
        "reason": "Repair passed static validation."
    }


# ============================================================
# TESTING AGENT
# ============================================================

def testing_agent(code):

    file_path = None

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
            [
                sys.executable,
                file_path
            ],
            capture_output=True,
            text=True,
            timeout=5
        )

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
            "error": "Program timed out during testing."
        }

    except Exception as e:

        return {
            "success": False,
            "output": "",
            "error": str(e)
        }

    finally:

        if (
            file_path
            and os.path.exists(file_path)
        ):

            try:
                os.remove(file_path)
            except Exception:
                pass


# ============================================================
# CRITIC AGENT
# ============================================================

def critic_agent(
    original_code,
    error_report,
    repaired_code,
    test_result
):

    # --------------------------------------------------------
    # First perform deterministic validation
    # --------------------------------------------------------

    validation = repair_validator(
        original_code,
        repaired_code
    )

    if not validation.get(
        "valid",
        False
    ):

        return (
            "REJECTED\n\n"
            + validation.get(
                "reason",
                "Static validation failed."
            )
        )

    # --------------------------------------------------------
    # Testing must pass
    # --------------------------------------------------------

    if not test_result.get(
        "success",
        False
    ):

        return (
            "REJECTED\n\n"
            "Testing failed.\n\n"
            + test_result.get(
                "error",
                ""
            )
        )

    # --------------------------------------------------------
    # NameError repairs are already verified deterministically
    # --------------------------------------------------------

    original_undefined = find_undefined_names(
        original_code
    )

    if original_undefined:

        return (
            "APPROVED\n\n"
            "The NameError was repaired "
            "deterministically by replacing the "
            "undefined variable with an existing "
            "matching variable. No arbitrary "
            "value was invented."
        )

    # --------------------------------------------------------
    # Missing argument repairs
    # --------------------------------------------------------

    original_missing = find_missing_function_arguments(
        original_code
    )

    if original_missing:

        return (
            "APPROVED\n\n"
            "The missing function argument problem "
            "was resolved without inserting an "
            "unsupported constant value."
        )

    # --------------------------------------------------------
    # Semantic Critic using Ollama
    # --------------------------------------------------------

    prompt = f"""
You are a strict Python Code Verification Agent.

Compare the ORIGINAL code and the REPAIRED code.

ORIGINAL CODE:
{original_code}

DEBUGGER REPORT:
{error_report}

REPAIRED CODE:
{repaired_code}

TEST RESULT:
{test_result}

Check:

1. Was the actual error fixed?
2. Is the repaired code valid Python?
3. Does it run successfully?
4. Is the original purpose preserved?
5. Is the meaning of operators preserved?
6. Are loops and conditions preserved?
7. Are data structures preserved?
8. Were arbitrary values invented?
9. Were unrelated changes introduced?
10. Is this the smallest reasonable repair?

IMPORTANT:

A repair must not be approved merely because it runs.

For example:

Original:
numbers = [10, 20, 30]
result = numbers * "2"

Good repair:
result = numbers * 2

Potentially incorrect repair:
result = [number * 2 for number in numbers]

The first preserves list repetition.
The second changes the meaning to element-wise multiplication.

Another example:

Original:
def add(a, b):
    return a + b

print(add(10))

Do NOT approve:
print(add(10, 20))

because 20 was invented.

Do NOT approve:
print(add(10, 0))

because 0 was invented.

Return:

APPROVED

or:

REJECTED

Then provide a short explanation.
"""

    try:

        response = ollama.chat(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        result = response[
            "message"
        ][
            "content"
        ].strip()

        if re.search(
            r"\bREJECTED\b",
            result,
            re.IGNORECASE
        ):

            return result

        if re.search(
            r"\bAPPROVED\b",
            result,
            re.IGNORECASE
        ):

            return result

        return (
            "REJECTED\n\n"
            "Critic did not provide a clear "
            "APPROVED or REJECTED decision."
        )

    except Exception as e:

        return (
            "REJECTED\n\n"
            f"Critic Agent error: {e}"
        )