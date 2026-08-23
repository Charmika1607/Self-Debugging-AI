from agents import debugger_agent, repair_agent, testing_agent, critic_agent


print("=" * 50)
print("       SELF-DEBUGGING AI")
print("=" * 50)

print("\nEnter your Python code.")
print("Type END on a new line when you are finished.\n")

lines = []

while True:
    line = input()

    if line == "END":
        break

    lines.append(line)

code = "\n".join(lines)

print("\n🚀 Starting Self-Debugging Process...")
print("Please wait...\n")

max_attempts = 3
current_code = code

for attempt in range(1, max_attempts + 1):

    print("=" * 50)
    print(f"       ATTEMPT {attempt} / {max_attempts}")
    print("=" * 50)

    # ---------------- DEBUGGER ----------------
    print("\n🔍 Debugger Agent is analyzing the code...")
    print("Please wait...\n")

    error_report = debugger_agent(current_code)

    print("=" * 50)
    print("       DEBUGGER AGENT RESULT")
    print("=" * 50)
    print(error_report)

    # ---------------- REPAIR ----------------
    print("\n🔧 Repair Agent is fixing the code...")
    print("Please wait...\n")

    fixed_code = repair_agent(current_code, error_report)

    print("=" * 50)
    print("       REPAIRED CODE")
    print("=" * 50)
    print(fixed_code)

    # ---------------- TESTING ----------------
    print("\n🧪 Testing the repaired code...")
    print("Please wait...\n")

    test_result = testing_agent(fixed_code)

    print("=" * 50)
    print("       TESTING AGENT RESULT")
    print("=" * 50)

    if test_result["success"]:
        print("✅ Status: PASSED")
        print("\nProgram Output:")
        print(test_result["output"])
    else:
        print("❌ Status: FAILED")
        print("\nError:")
        print(test_result["error"])

    # ---------------- CRITIC ----------------
    print("\n🧠 Critic Agent is verifying the repair...")
    print("Please wait...\n")

    critic_result = critic_agent(
        current_code,
        error_report,
        fixed_code,
        test_result
    )

    print("=" * 50)
    print("       CRITIC AGENT RESULT")
    print("=" * 50)
    print(critic_result)

    # ---------------- DECISION ----------------
    critic_decision = critic_result.strip().upper()

    critic_decision = critic_decision.replace("*", "")
    critic_decision = critic_decision.replace("#", "")
    critic_decision = critic_decision.strip()

    if critic_decision.startswith("APPROVED"):

        print("\n" + "=" * 50)
        print("       🎉 SELF-DEBUGGING SUCCESSFUL")
        print("=" * 50)

        print("\nFinal Corrected Code:")
        print(fixed_code)

        break

    else:

        print("\n❌ Critic rejected the repair.")
        print("🔄 Sending the code back for another attempt...\n")

        current_code = fixed_code

else:

    print("\n" + "=" * 50)
    print("       ❌ MAXIMUM ATTEMPTS REACHED")
    print("=" * 50)

    print("\nThe system could not confidently repair the code.")