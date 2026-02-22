
import os
import sys
import re

from dotenv import load_dotenv
try:
    from langchain.globals import set_verbose, set_debug
except ImportError:
    from langchain_core.globals import set_verbose, set_debug
from langchain_groq.chat_models import ChatGroq
from langgraph.constants import END
from langgraph.graph import StateGraph

from agent.prompts import *
from agent.states import *
from agent.tools import (
    write_file,
    read_file,
    list_files,
)

_ = load_dotenv()

debug_enabled = os.getenv("AGENT_DEBUG", "0") == "1"
set_debug(debug_enabled)
set_verbose(debug_enabled)

llm = ChatGroq(model="openai/gpt-oss-120b")


def _extract_file_content(raw_content: str) -> str:
    """Extract file content from tagged output only."""
    if not raw_content:
        raise ValueError("Empty model response. Expected <FILE_CONTENT>...</FILE_CONTENT>.")

    match = re.search(
        r"<FILE_CONTENT>\s*(.*?)\s*</FILE_CONTENT>",
        raw_content,
        flags=re.DOTALL,
    )
    if not match:
        raise ValueError("Missing <FILE_CONTENT> block in model response.")
    content = match.group(1)

    return content


def planner_agent(state: dict) -> dict:
    """Converts user prompt into a structured Plan."""
    user_prompt = state["user_prompt"]
    resp = llm.with_structured_output(Plan, method="json_schema").invoke(
        planner_prompt(user_prompt)
    )
    if resp is None:
        raise ValueError("Planner did not return a valid response.")
    return {"plan": resp}


def architect_agent(state: dict) -> dict:
    """Creates TaskPlan from Plan."""
    plan: Plan = state["plan"]
    resp = llm.with_structured_output(TaskPlan, method="json_schema").invoke(
        architect_prompt(plan=plan.model_dump_json())
    )
    if resp is None:
        raise ValueError("Planner did not return a valid response.")

    resp.plan = plan
    print(
        f"[Architect] Generated {len(resp.implementation_steps)} implementation steps.",
        flush=True,
    )
    if debug_enabled:
        print(resp.model_dump_json(), flush=True)
    return {"task_plan": resp}


def coder_agent(state: dict) -> dict:
    """Coder agent that generates full file content and writes directly."""
    coder_state: CoderState = state.get("coder_state")
    if coder_state is None:
        coder_state = CoderState(task_plan=state["task_plan"], current_step_idx=0)

    steps = coder_state.task_plan.implementation_steps
    if coder_state.current_step_idx >= len(steps):
        print("[Coder] All steps completed.", flush=True)
        return {"coder_state": coder_state, "status": "DONE"}

    current_task = steps[coder_state.current_step_idx]
    existing_content = read_file.run(current_task.filepath)
    project_files = list_files.run(".")
    step_no = coder_state.current_step_idx + 1
    total_steps = len(steps)
    print(
        f"[Coder] Step {step_no}/{total_steps}: {current_task.filepath}",
        flush=True,
    )

    system_prompt = coder_system_prompt()
    user_prompt = (
        f"Task: {current_task.task_description}\n"
        f"File: {current_task.filepath}\n"
        f"Project files:\n{project_files}\n"
        f"Existing content:\n{existing_content}\n"
        "Return the FULL final content for this file only.\n"
        "Do not explain.\n"
        "Wrap output exactly with:\n"
        "<FILE_CONTENT>\n"
        "...content...\n"
        "</FILE_CONTENT>"
    )

    try:
        response = llm.invoke(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        )
        content = _extract_file_content(response.content if response else "")
        write_file.invoke({"path": current_task.filepath, "content": content})
    except Exception as exc:
        raise RuntimeError(
            f"Coder failed at step {step_no}/{total_steps} for '{current_task.filepath}'."
        ) from exc
    print(
        f"[Coder] Finished step {step_no}/{total_steps}: {current_task.filepath}",
        flush=True,
    )

    coder_state.current_step_idx += 1
    return {"coder_state": coder_state}


graph = StateGraph(dict)

graph.add_node("planner", planner_agent)
graph.add_node("architect", architect_agent)
graph.add_node("coder", coder_agent)

graph.add_edge("planner", "architect")
graph.add_edge("architect", "coder")
graph.add_conditional_edges(
    "coder",
    lambda s: "END" if s.get("status") == "DONE" else "coder",
    {"END": END, "coder": "coder"}
)

graph.set_entry_point("planner")
agent = graph.compile()
if __name__ == "__main__":
    prompt = (
        " ".join(sys.argv[1:])
        if len(sys.argv) > 1
        else "Build a colourful modern todo app in html css and js"
    )
    result = agent.invoke({"user_prompt": prompt}, {"recursion_limit": 100})
    print("Final State:", result)
