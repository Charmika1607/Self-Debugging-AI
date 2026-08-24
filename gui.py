import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading

from agents import (
    debugger_agent,
    repair_agent,
    testing_agent,
    critic_agent
)


MAX_ATTEMPTS = 3


def run_debugger():
    code = code_input.get("1.0", tk.END).strip()

    if not code:
        messagebox.showwarning("No Code", "Please enter Python code first.")
        return

    debug_button.config(state=tk.DISABLED)
    output_box.delete("1.0", tk.END)

    thread = threading.Thread(
        target=debug_process,
        args=(code,),
        daemon=True
    )

    thread.start()


def debug_process(original_code):
    current_code = original_code

    try:
        for attempt in range(1, MAX_ATTEMPTS + 1):

            update_output(
                f"\n{'=' * 60}\n"
                f"ATTEMPT {attempt} / {MAX_ATTEMPTS}\n"
                f"{'=' * 60}\n"
            )

            # ---------------- DEBUGGER ----------------
            update_output(
                "\n🔍 DEBUGGER AGENT\n"
                "Analyzing the Python code...\n\n"
            )

            error_report = debugger_agent(current_code)

            update_output(
                "----- DEBUGGER REPORT -----\n"
                + error_report
                + "\n\n"
            )

            # ---------------- REPAIR ----------------
            update_output(
                "🔧 REPAIR AGENT\n"
                "Generating corrected code...\n\n"
            )

            repaired_code = repair_agent(
                current_code,
                error_report
            )

            update_output(
                "----- REPAIRED CODE -----\n"
                + repaired_code
                + "\n\n"
            )

            # ---------------- TESTING ----------------
            update_output(
                "🧪 TESTING AGENT\n"
                "Testing repaired code...\n\n"
            )

            test_result = testing_agent(repaired_code)

            if test_result["success"]:

                update_output(
                    "✅ TEST PASSED\n\n"
                    "Program Output:\n"
                    + test_result["output"]
                    + "\n\n"
                )

            else:

                update_output(
                    "❌ TEST FAILED\n\n"
                    "Error:\n"
                    + test_result["error"]
                    + "\n\n"
                )

            # ---------------- CRITIC ----------------
            update_output(
                "🧠 CRITIC AGENT\n"
                "Verifying the repair...\n\n"
            )

            critic_result = critic_agent(
                current_code,
                error_report,
                repaired_code,
                test_result
            )

            update_output(
                "----- CRITIC RESULT -----\n"
                + critic_result
                + "\n\n"
            )

            # ---------------- DECISION ----------------
            critic_decision = critic_result.strip().upper()

            critic_decision = critic_decision.replace("*", "")
            critic_decision = critic_decision.replace("#", "")
            critic_decision = critic_decision.strip()

            if critic_decision.startswith("APPROVED"):

                update_output(
                    "\n"
                    + "=" * 60
                    + "\n"
                    + "🎉 SELF-DEBUGGING SUCCESSFUL\n"
                    + "=" * 60
                    + "\n\n"
                    + "Final Corrected Code:\n\n"
                    + repaired_code
                    + "\n"
                )

                enable_button()
                return

            else:

                update_output(
                    "❌ Critic rejected the repair.\n"
                    "🔄 Trying another attempt...\n\n"
                )

                current_code = repaired_code

        update_output(
            "\n"
            + "=" * 60
            + "\n"
            + "❌ MAXIMUM ATTEMPTS REACHED\n"
            + "=" * 60
            + "\n\n"
            + "The system could not confidently repair the code.\n"
        )

    except Exception as e:

        update_output(
            "\n❌ SYSTEM ERROR\n\n"
            + str(e)
            + "\n"
        )

    finally:
        enable_button()


def update_output(text):
    root.after(
        0,
        lambda: (
            output_box.insert(tk.END, text),
            output_box.see(tk.END)
        )
    )


def enable_button():
    root.after(
        0,
        lambda: debug_button.config(state=tk.NORMAL)
    )


# =====================================================
# GUI
# =====================================================

root = tk.Tk()

root.title("Self-Debugging AI")
root.geometry("1100x750")

root.configure(bg="#f4f6f8")


# ---------------- TITLE ----------------

title = tk.Label(
    root,
    text="🤖 SELF-DEBUGGING AI",
    font=("Arial", 24, "bold"),
    bg="#f4f6f8"
)

title.pack(pady=15)


subtitle = tk.Label(
    root,
    text="Multi-Agent Python Code Debugging System",
    font=("Arial", 12),
    bg="#f4f6f8"
)

subtitle.pack()


# ---------------- CODE INPUT ----------------

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


# ---------------- BUTTON ----------------

debug_button = tk.Button(
    root,
    text="🔍 DEBUG & REPAIR",
    font=("Arial", 13, "bold"),
    padx=20,
    pady=8,
    command=run_debugger
)

debug_button.pack(pady=15)


# ---------------- OUTPUT ----------------

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


root.mainloop()