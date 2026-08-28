import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading

from agents import (
    debugger_agent,
    repair_agent,
    repair_validator,
    testing_agent,
    critic_agent,
    find_undefined_names,
    find_missing_function_arguments,
    deterministic_nameerror_repair
)


MAX_ATTEMPTS = 3


# ============================================================
# DISPLAY HELPER
# ============================================================

def print_separator():
    return "=" * 60


# ============================================================
# START DEBUGGING
# ============================================================

def run_debugger():
    code = code_input.get(
        "1.0",
        tk.END
    ).strip()

    if not code:
        messagebox.showwarning(
            "No Code",
            "Please enter Python code first."
        )
        return

    debug_button.config(
        state=tk.DISABLED
    )

    output_box.delete(
        "1.0",
        tk.END
    )

    thread = threading.Thread(
        target=debug_process,
        args=(code,),
        daemon=True
    )

    thread.start()


# ============================================================
# SAFE AGENT CALL
# ============================================================

def safe_agent_call(agent_function, *args):
    try:
        return agent_function(*args)

    except Exception as e:
        update_output(
            "\n❌ AGENT ERROR\n"
            + str(e)
            + "\n\n"
        )
        return None


# ============================================================
# CHECK UNSAFE NAMEERROR
# ============================================================

def check_unsafe_nameerror(code):
    """
    Detects an undefined variable that cannot be safely
    matched to an existing variable.

    Example:

        name = "Charmika"
        print(age)

    'age' has no obvious existing match, so automatic
    repair should stop instead of inventing a value.
    """

    undefined_names = find_undefined_names(code)

    if not undefined_names:
        return None

    repair_result = deterministic_nameerror_repair(code)

    if repair_result.get("status") == "REPAIRED":
        return None

    names = ", ".join(
        sorted(undefined_names)
    )

    return (
        "❌ SAFE REPAIR NOT POSSIBLE\n\n"
        f"Undefined variable(s): {names}\n\n"
        "No safe matching variable was found in the "
        "original code.\n\n"
        "The system will not invent a value and will "
        "not guess the missing information.\n\n"
        "Manual correction is required."
    )


# ============================================================
# DEBUG PROCESS
# ============================================================

def debug_process(original_code):

    try:

        # ====================================================
        # CHECK UNSAFE NAMEERROR BEFORE ATTEMPTS
        # ====================================================

        unsafe_nameerror = check_unsafe_nameerror(
            original_code
        )

        if unsafe_nameerror:

            update_output(
                "\n"
                + print_separator()
                + "\n"
                + "SAFE REPAIR ANALYSIS\n"
                + print_separator()
                + "\n\n"
            )

            update_output(
                unsafe_nameerror
                + "\n\n"
            )

            update_output(
                print_separator()
                + "\n"
                + "❌ SELF-DEBUGGING STOPPED SAFELY\n"
                + print_separator()
                + "\n"
            )

            return

        # ====================================================
        # CHECK MISSING FUNCTION ARGUMENTS
        # ====================================================

        missing_arguments = []

        try:
            missing_arguments = (
                find_missing_function_arguments(
                    original_code
                )
            )
        except Exception:
            missing_arguments = []

        if missing_arguments:

            update_output(
                "\n"
                + print_separator()
                + "\n"
                + "SAFE REPAIR ANALYSIS\n"
                + print_separator()
                + "\n\n"
            )

            for item in missing_arguments:

                update_output(
                    f"Function '{item['function']}' "
                    f"requires "
                    f"{item['required_count']} "
                    f"argument(s), but only "
                    f"{item['provided_count']} "
                    f"were provided.\n"
                )

                update_output(
                    "Missing argument(s): "
                    + ", ".join(
                        item["missing_names"]
                    )
                    + "\n\n"
                )

            update_output(
                "The original code does not provide "
                "the missing value.\n"
                "The system will NOT invent a value.\n"
                "Manual/user input is required.\n\n"
            )

            update_output(
                print_separator()
                + "\n"
                + "❌ SELF-DEBUGGING STOPPED SAFELY\n"
                + print_separator()
                + "\n"
            )

            return

        # ====================================================
        # MAIN RETRY LOOP
        # ====================================================

        for attempt in range(
            1,
            MAX_ATTEMPTS + 1
        ):

            update_output(
                "\n"
                + print_separator()
                + "\n"
                + f"ATTEMPT {attempt} / {MAX_ATTEMPTS}"
                + "\n"
                + print_separator()
                + "\n"
            )

            # =================================================
            # DEBUGGER
            # =================================================

            update_output(
                "\n🔍 DEBUGGER AGENT\n"
                "Analyzing the original Python code...\n"
                "Please wait...\n\n"
            )

            error_report = safe_agent_call(
                debugger_agent,
                original_code
            )

            if error_report is None:

                if attempt < MAX_ATTEMPTS:

                    update_output(
                        "🔄 Retrying from ORIGINAL code...\n\n"
                    )

                    continue

                return

            update_output(
                "----- DEBUGGER REPORT -----\n"
                + error_report
                + "\n\n"
            )

            # =================================================
            # REPAIR
            # =================================================

            update_output(
                "🔧 REPAIR AGENT\n"
                "Generating corrected code...\n"
                "Please wait...\n\n"
            )

            repaired_code = safe_agent_call(
                repair_agent,
                original_code,
                error_report
            )

            if repaired_code is None:

                if attempt < MAX_ATTEMPTS:

                    update_output(
                        "🔄 Retrying from ORIGINAL code...\n\n"
                    )

                    continue

                return

            repaired_code = repaired_code.strip()

            update_output(
                "----- REPAIRED CODE -----\n"
                + repaired_code
                + "\n\n"
            )

            # =================================================
            # VALIDATOR
            # =================================================

            update_output(
                "🛡️ REPAIR VALIDATOR\n"
                "Checking whether the repair is valid...\n"
                "Please wait...\n\n"
            )

            validation_result = safe_agent_call(
                repair_validator,
                original_code,
                repaired_code
            )

            if validation_result is None:

                if attempt < MAX_ATTEMPTS:

                    update_output(
                        "🔄 Retrying from ORIGINAL code...\n\n"
                    )

                    continue

                return

            update_output(
                "----- VALIDATOR RESULT -----\n"
            )

            if not isinstance(
                validation_result,
                dict
            ):

                update_output(
                    "❌ Invalid validator response.\n\n"
                )

                if attempt < MAX_ATTEMPTS:

                    update_output(
                        "🔄 Retrying...\n\n"
                    )

                    continue

                return

            is_valid = validation_result.get(
                "valid",
                False
            )

            reason = validation_result.get(
                "reason",
                "No reason provided."
            )

            if not is_valid:

                update_output(
                    "❌ INVALID\n"
                    + reason
                    + "\n\n"
                )

                # --------------------------------------------
                # IMPORTANT:
                # If this is an unsafe NameError, stop.
                # --------------------------------------------

                if find_undefined_names(
                    original_code
                ):

                    unsafe_result = (
                        check_unsafe_nameerror(
                            original_code
                        )
                    )

                    if unsafe_result:

                        update_output(
                            unsafe_result
                            + "\n\n"
                            + print_separator()
                            + "\n"
                            + "❌ SELF-DEBUGGING "
                            "STOPPED SAFELY\n"
                            + print_separator()
                            + "\n"
                        )

                        return

                if attempt < MAX_ATTEMPTS:

                    update_output(
                        "⚠️ Repair rejected by Validator.\n"
                        "🔄 Retrying from ORIGINAL code...\n\n"
                    )

                    continue

                update_output(
                    print_separator()
                    + "\n"
                    + "❌ MAXIMUM ATTEMPTS REACHED\n"
                    + print_separator()
                    + "\n\n"
                    + "The system could not produce "
                    + "a safe repair.\n"
                )

                return

            update_output(
                "✅ VALID\n"
                + reason
                + "\n\n"
            )

            # =================================================
            # TESTING
            # =================================================

            update_output(
                "🧪 TESTING AGENT\n"
                "Testing repaired code...\n"
                "Please wait...\n\n"
            )

            test_result = safe_agent_call(
                testing_agent,
                repaired_code
            )

            if test_result is None:

                if attempt < MAX_ATTEMPTS:

                    update_output(
                        "🔄 Retrying from ORIGINAL code...\n\n"
                    )

                    continue

                return

            if not isinstance(
                test_result,
                dict
            ):

                update_output(
                    "❌ Invalid testing response.\n\n"
                )

                if attempt < MAX_ATTEMPTS:

                    update_output(
                        "🔄 Retrying...\n\n"
                    )

                    continue

                return

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

                update_output(
                    "✅ TEST PASSED\n\n"
                    "Program Output:\n"
                    + test_output
                    + "\n\n"
                )

            else:

                update_output(
                    "❌ TEST FAILED\n\n"
                    "Program Output:\n"
                    + test_output
                    + "\n\n"
                    "Error:\n"
                    + test_error
                    + "\n\n"
                )

            # =================================================
            # CRITIC
            # =================================================

            update_output(
                "🧠 CRITIC AGENT\n"
                "Verifying the repair...\n"
                "Please wait...\n\n"
            )

            critic_result = safe_agent_call(
                critic_agent,
                original_code,
                error_report,
                repaired_code,
                test_result
            )

            if critic_result is None:

                if attempt < MAX_ATTEMPTS:

                    update_output(
                        "🔄 Retrying from ORIGINAL code...\n\n"
                    )

                    continue

                return

            update_output(
                "----- CRITIC RESULT -----\n"
                + critic_result
                + "\n\n"
            )

            # =================================================
            # DECISION
            # =================================================

            critic_text = (
                critic_result
                .strip()
                .upper()
                .replace("*", "")
                .replace("#", "")
                .strip()
            )

            if (
                test_success
                and critic_text.startswith(
                    "APPROVED"
                )
            ):

                update_output(
                    print_separator()
                    + "\n"
                    + "🎉 SELF-DEBUGGING SUCCESSFUL\n"
                    + print_separator()
                    + "\n\n"
                    + "Final Corrected Code:\n\n"
                    + repaired_code
                    + "\n"
                )

                return

            # =================================================
            # CRITIC REJECTED
            # =================================================

            update_output(
                "❌ Critic rejected the repair.\n"
            )

            if not test_success:

                update_output(
                    "Reason: Testing failed.\n"
                )

            else:

                update_output(
                    "Reason: Critic did not approve "
                    "the repair.\n"
                )

            if attempt < MAX_ATTEMPTS:

                update_output(
                    "🔄 Trying another attempt "
                    "from ORIGINAL code...\n\n"
                )

                continue

            update_output(
                "\n"
                + print_separator()
                + "\n"
                + "❌ MAXIMUM ATTEMPTS REACHED\n"
                + print_separator()
                + "\n\n"
                + "The system could not confidently "
                + "repair the code.\n"
            )

            return

    except Exception as e:

        update_output(
            "\n"
            + print_separator()
            + "\n"
            + "❌ SYSTEM ERROR\n"
            + print_separator()
            + "\n\n"
            + str(e)
            + "\n"
        )

    finally:
        enable_button()


# ============================================================
# THREAD-SAFE OUTPUT
# ============================================================

def update_output(text):
    root.after(
        0,
        lambda: (
            output_box.insert(
                tk.END,
                text
            ),
            output_box.see(
                tk.END
            )
        )
    )


def enable_button():
    root.after(
        0,
        lambda: debug_button.config(
            state=tk.NORMAL
        )
    )


# ============================================================
# GUI
# ============================================================

root = tk.Tk()

root.title(
    "Self-Debugging AI"
)

root.geometry(
    "1100x750"
)

root.configure(
    bg="#f4f6f8"
)


# ============================================================
# TITLE
# ============================================================

title = tk.Label(
    root,
    text="🤖 SELF-DEBUGGING AI",
    font=("Arial", 24, "bold"),
    bg="#f4f6f8"
)

title.pack(
    pady=15
)


subtitle = tk.Label(
    root,
    text="Multi-Agent Python Code Debugging System",
    font=("Arial", 12),
    bg="#f4f6f8"
)

subtitle.pack()


# ============================================================
# CODE INPUT
# ============================================================

input_label = tk.Label(
    root,
    text="Enter Python Code:",
    font=("Arial", 13, "bold"),
    bg="#f4f6f8"
)

input_label.pack(
    anchor="w",
    padx=25,
    pady=(20, 5)
)


code_input = scrolledtext.ScrolledText(
    root,
    height=12,
    font=("Consolas", 12),
    wrap=tk.NONE
)

code_input.pack(
    fill="both",
    padx=25
)


# ============================================================
# DEBUG BUTTON
# ============================================================

debug_button = tk.Button(
    root,
    text="🔍 DEBUG & REPAIR",
    font=("Arial", 13, "bold"),
    padx=20,
    pady=8,
    command=run_debugger
)

debug_button.pack(
    pady=15
)


# ============================================================
# OUTPUT
# ============================================================

output_label = tk.Label(
    root,
    text="System Output:",
    font=("Arial", 13, "bold"),
    bg="#f4f6f8"
)

output_label.pack(
    anchor="w",
    padx=25,
    pady=(5, 5)
)


output_box = scrolledtext.ScrolledText(
    root,
    height=20,
    font=("Consolas", 11),
    wrap=tk.WORD
)

output_box.pack(
    fill="both",
    expand=True,
    padx=25,
    pady=(0, 20)
)


# ============================================================
# START GUI
# ============================================================

root.mainloop()