"""Isabella - Multi-Agent System. Parallel task execution using multiple API keys."""
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from openai import OpenAI

import config

def _get_clients() -> list:
    """Create one client per API key — 8 keys = 8 parallel workers."""
    clients = []
    for key in config.GROQ_API_KEYS:
        if key and key != "your-key-here":
            clients.append(OpenAI(api_key=key, base_url=config.GROQ_BASE_URL))
    return clients if clients else [OpenAI(api_key=config.GROQ_API_KEY, base_url=config.GROQ_BASE_URL)]

def _call_agent(client, role: str, task: str, model: str = None) -> dict:
    """Single agent call."""
    if model is None:
        model = config.BRAIN_MODEL
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": f"You are a {role}. Be concise."},
                {"role": "user", "content": task}
            ],
            temperature=0.7, max_tokens=300,
        )
        return {"role": role, "result": resp.choices[0].message.content.strip(), "success": True}
    except Exception as e:
        return {"role": role, "result": str(e), "success": False}


def parallel_think(tasks: list[dict]) -> list[dict]:
    """Run multiple agent tasks in parallel using different API keys.
    
    tasks = [{"role": "researcher", "task": "find info about X"}, 
             {"role": "analyzer", "task": "analyze Y"}, ...]
    
    Returns list of results.
    """
    clients = _get_clients()
    results = []

    with ThreadPoolExecutor(max_workers=len(clients)) as executor:
        futures = {}
        for i, task_info in enumerate(tasks):
            client = clients[i % len(clients)]  # round-robin across keys
            future = executor.submit(
                _call_agent, client,
                task_info.get("role", "assistant"),
                task_info.get("task", ""),
                task_info.get("model")
            )
            futures[future] = i

        for future in as_completed(futures):
            idx = futures[future]
            results.append((idx, future.result()))

    # Return in original order
    results.sort(key=lambda x: x[0])
    return [r for _, r in results]


def research_and_answer(question: str) -> str:
    """Use multiple agents: one researches, one answers, one verifies."""
    clients = _get_clients()

    if len(clients) >= 2:
        # Parallel: research + draft answer
        tasks = [
            {"role": "researcher", "task": f"List 3-5 key facts about: {question}"},
            {"role": "creative thinker", "task": f"What's an interesting perspective on: {question}"},
        ]
        results = parallel_think(tasks)
        research = results[0]["result"] if results[0]["success"] else ""
        creative = results[1]["result"] if results[1]["success"] else ""

        # Final synthesis with primary key
        synthesis_prompt = f"""Based on this research, answer the question naturally in 2-3 sentences.
Research: {research}
Creative angle: {creative}
Question: {question}"""

        final = _call_agent(clients[0], "synthesizer", synthesis_prompt)
        return final["result"]
    else:
        # Single key fallback
        result = _call_agent(clients[0], "assistant", question)
        return result["result"]


def solve_complex(task: str, subtasks: list[str] = None) -> str:
    """Break a complex task into subtasks and solve in parallel."""
    clients = _get_clients()

    if not subtasks:
        # Ask one agent to break down the task
        planner = _call_agent(clients[0], "task planner",
            f"Break this into 2-3 independent subtasks (one line each): {task}")
        if planner["success"]:
            subtasks = [line.strip("- ").strip() for line in planner["result"].split("\n") if line.strip()]
        else:
            subtasks = [task]

    # Execute subtasks in parallel
    tasks = [{"role": "executor", "task": st} for st in subtasks[:4]]
    results = parallel_think(tasks)

    successful = [r["result"] for r in results if r["success"]]
    return "\n".join(successful) if successful else "couldn't complete the task"
