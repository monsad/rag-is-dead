from typing import TypedDict, List
from langgraph.graph import END, StateGraph, START
from data_prep import embed_texts
from sources import fetch_wikipedia_extract
from llm_utils import (grade_relevance, generate_rag, predict_alternative, rewrite_question,
                       grade_hallucination, grade_answer)

class GraphState(TypedDict):
    question: str
    generation: str
    documents: List[str]
    is_alternative: bool

def retrieve(state, client, collection_name):
    print("---RETRIEVE---")
    query_vecs = embed_texts([state["question"]])
    res = client.search(
        collection_name=collection_name,
        data=query_vecs,
        limit=5,
        output_fields=["text"],
    )
    docs = [hit["entity"]["text"] for hit in res[0]]
    if not docs:
        wiki = fetch_wikipedia_extract(state["question"], lang="pl")
        if wiki:
            docs = [wiki]
    return {"documents": docs}

def grade_documents(state):
    print("---GRADE DOCUMENTS---")
    filtered = []
    for doc in state["documents"]:
        score = grade_relevance(state["question"], doc)
        print(f"---GRADE: {'RELEVANT' if score == 'yes' else 'NOT RELEVANT'}---")
        if score == "yes":
            filtered.append(doc)
    return {"documents": filtered}

def fallback_documents(state):
    print("---FALLBACK WIKI---")
    wiki = fetch_wikipedia_extract(state["question"], lang="pl")
    docs = [wiki] if wiki else []
    return {"documents": docs}

def generate(state):
    print("---GENERATE---")
    context = "\n\n".join(state["documents"])
    if state.get("is_alternative", False):
        gen = predict_alternative(state["question"], context)
    else:
        gen = generate_rag(state["question"], context)
    return {"generation": gen}

def transform_query(state):
    print("---TRANSFORM QUERY---")
    new_question = rewrite_question(state["question"])
    return {"question": new_question}

def detect_alternative(state):
    print("---DETECT ALTERNATIVE HISTORY---")
    q = state["question"].lower()
    keywords = [
        "what if",
        "alternative",
        "counterfactual",
        "predict if",
        "co by było gdyby",
        "gdyby",
        "kontrafakty",
        "kontrafaktycz",
        "alternatyw",
        "hipotetycz"
    ]
    is_alt = any(k in q for k in keywords)
    return {"is_alternative": is_alt}

def decide_to_generate(state):
    print("---DECIDE: GRADED DOCS---")
    if not state["documents"]:
        print("---NO RELEVANT DOCS: FALLBACK WIKI---")
        return "fallback_documents"
    print("---HAS RELEVANT DOCS: GENERATE---")
    return "generate"

def grade_generation(state):
    print("---GRADE GENERATION---")
    context = "\n\n".join(state["documents"])
    hall_score = grade_hallucination(context, state["generation"])
    if hall_score == "yes":
        print("---GROUNDED---")
        ans_score = grade_answer(state["question"], state["generation"])
        if ans_score == "yes":
            print("---USEFUL---")
            return "useful"
        print("---NOT USEFUL: TRANSFORM---")
        return "not_useful"
    print("---NOT GROUNDED: REGENERATE---")
    return "not_supported"

def build_workflow(client, collection_name):
    workflow = StateGraph(GraphState)
    
    workflow.add_node("detect_alternative", detect_alternative)
    workflow.add_node("retrieve", lambda state: retrieve(state, client, collection_name))
    workflow.add_node("grade_documents", grade_documents)
    workflow.add_node("fallback_documents", fallback_documents)
    workflow.add_node("generate", generate)
    workflow.add_node("transform_query", transform_query)
    
    workflow.add_edge(START, "detect_alternative")
    workflow.add_edge("detect_alternative", "retrieve")
    workflow.add_edge("retrieve", "grade_documents")
    workflow.add_conditional_edges(
        "grade_documents",
        decide_to_generate,
        {"fallback_documents": "fallback_documents", "generate": "generate"},
    )
    workflow.add_edge("fallback_documents", "generate")
    workflow.add_edge("transform_query", "retrieve")
    workflow.add_conditional_edges(
        "generate",
        grade_generation,
        {"not_supported": END, "useful": END, "not_useful": END},
    )
    
    return workflow.compile()