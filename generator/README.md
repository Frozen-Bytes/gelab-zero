# Generator Module

The `generator` module is the **Planning Layer** of the agent. It takes the raw, technical data gathered by the `analyzer` and transforms it into structured instructions or "test cases" that the agent can execute.

## The Data Flow
1. **Input**: Technical summaries (Permissions, Activities, UI Labels) from the `analyzer`.
2. **Process**: The Generator uses LLM reasoning to determine what a user *would* want to do with this app.
3. **Output**: A List of "Goals" (e.g., "Login as a guest and find the settings menu").
