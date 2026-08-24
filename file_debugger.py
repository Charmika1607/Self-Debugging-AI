import os

from agents import (
    debugger_agent,
    repair_agent,
    testing_agent,
    critic_agent
)


MAX_ATTEMPTS = 3

INPUT_FILE = "buggy_code.py"
OUTPUT_FILE = "fixed_code.py"


def main():

    print("=" * 60)
    print("          SELF-DEBUGGING AI - FILE MODE")
    print("=" * 60)

    # -------------------------------------------------
    # CHECK INPUT FILE
    # -------------------------------------------------

    if not os.path.exists(INPUT_FILE):

        print(f"\n❌ Error: {INPUT_FILE} not found.")

        return

    # -------------------------------------------------
    # READ PYTHON FILE
    # -------------------------------------------------

    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        original_code = file.read()

    current_code = original_code

    print(f"\n📂 Input file: {INPUT_FILE}")
    print("🚀 Starting Self-Debugging Process...\n")

    # -------------------------------------------------
    # SELF-DEBUGGING LOOP
    # -------------------------------------------------

    for attempt in range(1, MAX_ATTEMPTS + 1):

        print("=" * 60)
        print(f"              ATTEMPT {attempt} / {MAX_ATTEMPTS}")
        print("=" * 60)

        # -------------------------------------------------
        # DEBUGGER AGENT
        # -------------------------------------------------

        print("\n🔍 Debugger Agent")
        print("Analyzing the Python code...\n")

        error_report = debugger_agent(current_code)

        print("-" * 60)
        print("DEBUGGER REPORT")
        print("-" * 60)

        print(error_report)

        # -------------------------------------------------
        # REPAIR AGENT
        # -------------------------------------------------

        print("\n🔧 Repair Agent")
        print("Generating corrected code...\n")

        repaired_code = repair_agent(
            current_code,
            error_report
        )

        print("-" * 60)
        print("REPAIRED CODE")
        print("-" * 60)

        print(repaired_code)

        # -------------------------------------------------
        # TESTING AGENT
        # -------------------------------------------------

        print("\n🧪 Testing Agent")
        print("Testing repaired code...\n")

        test_result = testing_agent(repaired_code)

        print("-" * 60)
        print("TEST RESULT")
        print("-" * 60)

        if test_result["success"]:

            print("✅ Status: PASSED")

            print("\nProgram Output:")
            print(test_result["output"])

        else:

            print("❌ Status: FAILED")

            print("\nError:")
            print(test_result["error"])

        # -------------------------------------------------
        # CRITIC AGENT
        # -------------------------------------------------

        print("\n🧠 Critic Agent")
        print("Verifying the repair...\n")

        critic_result = critic_agent(
            current_code,
            error_report,
            repaired_code,
            test_result
        )

        print("-" * 60)
        print("CRITIC RESULT")
        print("-" * 60)

        print(critic_result)

        # -------------------------------------------------
        # DECISION
        # -------------------------------------------------

        critic_decision = critic_result.strip().upper()

        critic_decision = critic_decision.replace("*", "")
        critic_decision = critic_decision.replace("#", "")
        critic_decision = critic_decision.strip()

        if critic_decision.startswith("APPROVED"):

            print("\n" + "=" * 60)
            print("          🎉 SELF-DEBUGGING SUCCESSFUL")
            print("=" * 60)

            # -------------------------------------------------
            # SAVE FINAL CODE
            # -------------------------------------------------

            with open(
                OUTPUT_FILE,
                "w",
                encoding="utf-8"
            ) as file:

                file.write(repaired_code)

            print("\n📁 Final corrected code saved to:")

            print(f"   {OUTPUT_FILE}")

            print("\nFinal Corrected Code:")
            print(repaired_code)

            return

        else:

            print("\n❌ Critic rejected the repair.")

            print(
                "🔄 Sending the code back "
                "for another attempt...\n"
            )

            current_code = repaired_code

    # -------------------------------------------------
    # MAXIMUM ATTEMPTS
    # -------------------------------------------------

    print("\n" + "=" * 60)
    print("          ❌ MAXIMUM ATTEMPTS REACHED")
    print("=" * 60)

    print(
        "\nThe system could not confidently "
        "repair the code."
    )


if __name__ == "__main__":
    main()