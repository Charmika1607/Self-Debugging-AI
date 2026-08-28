import re

from agents import (
    debugger_agent,
    repair_agent,
    repair_validator,
    testing_agent,
    critic_agent,
    find_missing_function_arguments
)


# ============================================================
# DISPLAY HELPER
# ============================================================

def print_separator():
    print("\n" + "=" * 60)


# ============================================================
# CLEAN AI CODE
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
# CHECK CRITIC APPROVAL
# ============================================================

def is_approved(critic_result):
    if not isinstance(critic_result, str):
        return False

    return (
        re.search(
            r"\bAPPROVED\b",
            critic_result,
            re.IGNORECASE
        )
        is not None
    )


# ============================================================
# SAFE AGENT CALL
# ============================================================

def safe_agent_call(agent_function, *args):
    try:
        return agent_function(*args)

    except Exception as e:
        print("\n❌ AGENT ERROR")
        print(f"Error: {e}")
        return None


# ============================================================
# CHECK WHETHER REPAIR IS POSSIBLE
# ============================================================

def check_unrepairable_case(code):
    """
    Detects cases where the program is missing information
    that cannot safely be invented.

    Currently handles missing function arguments.
    """

    missing_arguments = find_missing_function_arguments(code)

    if not missing_arguments:
        return None

    messages = []

    for item in missing_arguments:

        messages.append(
            f"Function '{item['function']}' requires "
            f"{item['required_count']} argument(s), but only "
            f"{item['provided_count']} were provided. "
            f"Missing argument(s): "
            f"{', '.join(item['missing_names'])}."
        )

    return (
        "❌ AUTOMATIC REPAIR NOT POSSIBLE\n\n"
        + "\n".join(messages)
        + "\n\n"
        "The original code does not provide the missing "
        "value.\n"
        "The system will not invent a value.\n"
        "Manual/user input is required."
    )


# ============================================================
# SELF DEBUGGING SYSTEM
# ============================================================

def self_debug(code):

    original_code = code
    max_attempts = 3

    # --------------------------------------------------------
    # Check for known unrepairable cases BEFORE AI attempts
    # --------------------------------------------------------

    unrepairable_message = check_unrepairable_case(
        original_code
    )

    if unrepairable_message:

        print_separator()
        print("SAFE REPAIR ANALYSIS")
        print_separator()

        print()
        print(unrepairable_message)

        print()
        print_separator()
        print("❌ SELF-DEBUGGING STOPPED SAFELY")
        print_separator()

        return False

    # --------------------------------------------------------
    # Main retry loop
    # --------------------------------------------------------

    for attempt in range(1, max_attempts + 1):

        print_separator()
        print(f"ATTEMPT {attempt} / {max_attempts}")
        print_separator()

        # ====================================================
        # DEBUGGER AGENT
        # ====================================================

        print("\n🔍 DEBUGGER AGENT")
        print("Analyzing the original Python code...")
        print("Please wait...")

        error_report = safe_agent_call(
            debugger_agent,
            original_code
        )

        if error_report is None:

            print("\n❌ Debugger Agent failed.")

            if attempt < max_attempts:
                print("Retrying...")
                continue

            return False

        print("\n----- DEBUGGER REPORT -----")
        print(error_report)

        # ====================================================
        # RE-CHECK FOR UNREPAIRABLE FUNCTION ARGUMENTS
        # ====================================================

        missing_arguments = find_missing_function_arguments(
            original_code
        )

        if missing_arguments:

            print()
            print(
                "⚠️ A required function argument is missing."
            )

            for item in missing_arguments:

                print(
                    f"Function '{item['function']}': "
                    f"missing "
                    f"{', '.join(item['missing_names'])}"
                )

            print()
            print(
                "The correct value cannot be determined "
                "from the original code."
            )

            print(
                "The system will not invent a value."
            )

            print_separator()
            print("❌ SELF-DEBUGGING STOPPED SAFELY")
            print_separator()

            return False

        # ====================================================
        # REPAIR AGENT
        # ====================================================

        print("\n🔧 REPAIR AGENT")
        print("Generating corrected code...")
        print("Please wait...")

        repaired_code = safe_agent_call(
            repair_agent,
            original_code,
            error_report
        )

        if repaired_code is None:

            print("\n❌ Repair Agent failed.")

            if attempt < max_attempts:
                print("Retrying...")
                continue

            return False

        repaired_code = clean_code(
            repaired_code
        )

        if not repaired_code:

            print(
                "\n❌ Repair Agent returned empty code."
            )

            if attempt < max_attempts:
                print("Retrying...")
                continue

            return False

        print("\n----- REPAIRED CODE -----")
        print(repaired_code)

        # ====================================================
        # REPAIR VALIDATOR
        # ====================================================

        print("\n🛡️ REPAIR VALIDATOR")
        print(
            "Checking whether the repair is valid..."
        )
        print("Please wait...")

        validation_result = safe_agent_call(
            repair_validator,
            original_code,
            repaired_code
        )

        if validation_result is None:

            print("\n❌ Validator failed.")

            if attempt < max_attempts:
                print("Retrying...")
                continue

            return False

        print("\n----- VALIDATOR RESULT -----")

        if not isinstance(
            validation_result,
            dict
        ):

            print(
                "❌ Invalid validator response."
            )

            if attempt < max_attempts:
                print("Retrying...")
                continue

            return False

        valid = validation_result.get(
            "valid",
            False
        )

        reason = validation_result.get(
            "reason",
            "No reason provided."
        )

        if valid:

            print("✅ VALID")
            print(reason)

        else:

            print("❌ INVALID")
            print(reason)

            if attempt < max_attempts:

                print(
                    "\n⚠️ Repair rejected by Validator."
                )

                print(
                    "Retrying from ORIGINAL code..."
                )

                continue

            print_separator()
            print("❌ SELF-DEBUGGING FAILED")
            print_separator()

            print(
                "\nThe AI could not generate a repair "
                "that passed safety validation."
            )

            return False

        # ====================================================
        # TESTING AGENT
        # ====================================================

        print("\n🧪 TESTING AGENT")
        print("Testing repaired code...")
        print("Please wait...")

        test_result = safe_agent_call(
            testing_agent,
            repaired_code
        )

        if test_result is None:

            print("\n❌ Testing Agent failed.")

            if attempt < max_attempts:
                print("Retrying...")
                continue

            return False

        if not isinstance(
            test_result,
            dict
        ):

            print(
                "\n❌ Invalid testing result."
            )

            if attempt < max_attempts:
                print("Retrying...")
                continue

            return False

        test_success = test_result.get(
            "success",
            False
        )

        test_output = test_result.get(
            "output",
            ""
        )

        test_error = test_result.get(
            "error",
            ""
        )

        if test_success:

            print("\n✅ TEST PASSED")

            print("\nProgram Output:")
            print(test_output)

        else:

            print("\n❌ TEST FAILED")

            print("\nProgram Output:")
            print(test_output)

            print("\nError:")
            print(test_error)

        # ====================================================
        # CRITIC AGENT
        # ====================================================

        print("\n🧠 CRITIC AGENT")
        print("Verifying the repair...")
        print("Please wait...")

        critic_result = safe_agent_call(
            critic_agent,
            original_code,
            error_report,
            repaired_code,
            test_result
        )

        if critic_result is None:

            print("\n❌ Critic Agent failed.")

            if attempt < max_attempts:
                print("Retrying from ORIGINAL code...")
                continue

            return False

        print("\n----- CRITIC RESULT -----")
        print(critic_result)

        # ====================================================
        # FINAL APPROVAL
        # ====================================================

        if (
            test_success
            and is_approved(critic_result)
        ):

            print_separator()
            print("🎉 SELF-DEBUGGING SUCCESSFUL")
            print_separator()

            print("\nFinal Corrected Code:\n")
            print(repaired_code)

            return True

        # ====================================================
        # CRITIC REJECTED
        # ====================================================

        print("\n⚠️ Critic rejected the repair.")

        if not test_success:
            print("Reason: Testing failed.")

        elif not is_approved(critic_result):
            print(
                "Reason: Critic did not approve "
                "the repair."
            )

        if attempt < max_attempts:

            print(
                "\n🔄 Retrying from ORIGINAL code..."
            )

            continue

        # ====================================================
        # ALL ATTEMPTS FAILED
        # ====================================================

        print_separator()
        print("❌ SELF-DEBUGGING FAILED")
        print_separator()

        print(
            "\nThe system could not produce a repair "
            "that passed validation, testing, and "
            "critic verification."
        )

        return False

    return False


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():

    print("=" * 60)
    print("       SELF-DEBUGGING AI")
    print("=" * 60)

    print()
    print("Enter your Python code.")
    print(
        "Type END on a new line when you are finished."
    )
    print()

    code_lines = []

    while True:

        try:
            line = input()

        except EOFError:
            break

        except KeyboardInterrupt:

            print("\n\n❌ Program cancelled.")
            return

        if line.strip() == "END":
            break

        code_lines.append(line)

    code = "\n".join(code_lines)

    if not code.strip():

        print("\n❌ No Python code was entered.")
        return

    print(
        "\n🚀 Starting Self-Debugging Process..."
    )

    print("Please wait...")

    try:

        success = self_debug(code)

        if not success:

            print(
                "\n⚠️ Self-debugging process ended "
                "without success."
            )

    except Exception as e:

        print_separator()
        print("❌ UNEXPECTED SYSTEM ERROR")
        print_separator()

        print(f"\nError: {e}")


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()