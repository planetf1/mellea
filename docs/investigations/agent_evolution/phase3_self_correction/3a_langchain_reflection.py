from typing import TypedDict, List
from warnings import filterwarnings

filterwarnings("ignore")

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END

# Developer Value Note:
# To implement "Reflection" in LangChain, we must use LangGraph.
# 1. Define State (TypedDict).
# 2. Define Nodes (Functions taking State -> State).
# 3. Define Edges (Routing logic).
# 4. Compile Graph.
# In Mellea, this is a simple python while loop.


class AgentState(TypedDict):
    messages: List[BaseMessage]
    question: str
    answer: str
    critique: str
    iterations: int


def run_demo():
    print("--- Phase 3a: Reflection w/ LangGraph (The Manual Architecture) ---")

    llm = ChatOllama(model="llama3.2:1b", temperature=0)

    # Node 1: Solver
    def solver_node(state: AgentState):
        print("  > Solver Node: Generating initial solution...")
        msg = f"Solve this problem: {state['question']}"
        response = llm.invoke(msg)
        return {"answer": response.content, "iterations": state["iterations"] + 1}

    # Node 2: Critic
    def critic_node(state: AgentState):
        print("  > Critic Node: Reviewing solution...")
        # Match Mellea's "Physics Professor" prompt for fairness
        msg = f"""You are a Physics Professor checking a student's work.
        Problem: {state["question"]}
        Student Answer: {state["answer"]}
        
        Check specifically for:
        1. Unit mismatch.
        2. Calculation errors.
        3. Logic errors (Relative speed).
        
        If correct, say 'CORRECT'.
        If wrong, explain WHY it is wrong in 1 sentence.
        """
        response = llm.invoke(msg)
        return {"critique": response.content}

    # Node 3: Refiner
    def refiner_node(state: AgentState):
        print("  > Refiner Node: Improving solution...")
        msg = f"Problem: {state['question']}\nPrevious Solution: {state['answer']}\nCritique: {state['critique']}\nProvide a corrected solution."
        response = llm.invoke(msg)
        # Update answer with refined version
        return {"answer": response.content}

    # Conditional Edge
    def should_continue(state: AgentState):
        if state["iterations"] > 2:
            return "end"
        if (
            "correct" in state["critique"].lower()
            and "incorrect" not in state["critique"].lower()
        ):
            return "end"
        return "refine"

    # Build Graph
    workflow = StateGraph(AgentState)
    workflow.add_node("solver", solver_node)
    workflow.add_node("critic", critic_node)
    workflow.add_node("refiner", refiner_node)

    workflow.set_entry_point("solver")
    workflow.add_edge("solver", "critic")
    workflow.add_conditional_edges(
        "critic", should_continue, {"end": END, "refine": "refiner"}
    )
    workflow.add_edge("refiner", "critic")  # Loop back to critic

    app = workflow.compile()

    question = "A train leaves New York at 60 mph. Another leaves 2 hours later at 80 mph. How long until the second train catches the first?"
    print(f"Question: {question}")

    # Execute Graph
    inputs = {
        "question": question,
        "messages": [],
        "answer": "",
        "critique": "",
        "iterations": 0,
    }
    result = app.invoke(inputs)

    print("-" * 20)
    print(f"Final Answer: {result['answer']}")


if __name__ == "__main__":
    run_demo()
