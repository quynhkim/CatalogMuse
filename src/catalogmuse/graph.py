"""Listing graph.

Each agent does its work, then a review node stops until a person approves
or sends the work back with a note. The review node does no work before it
pauses, because LangGraph runs that node again when the person answers.
"""

from __future__ import annotations

from typing import Any, Callable, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from catalogmuse.tools import Tools, _short_noun

Mark = Callable[..., None]


class State(TypedDict, total=False):
    job_id: str
    spec_text: str
    spec: dict[str, Any]
    image_path: str
    work_dir: str
    feedback: dict[str, str]
    segment: dict[str, Any]
    art_director: dict[str, Any]
    scene: dict[str, Any]
    copy: dict[str, Any]
    rules: dict[str, Any]
    marketplaces: list[str]
    last_decision: dict[str, str]


def build_graph(tools: Tools, checkpointer: Any, mark: Mark) -> Any:
    def segment(state: State) -> dict[str, Any]:
        note = _note(state, "segment")
        saved = str((state.get("art_director") or {}).get("concept") or "")

        def work() -> dict[str, Any]:
            concept = saved
            if not _short_noun(note) and (not concept or note):
                named = tools.name_product(state["image_path"], state["spec"], note)
                concept = str(named.get("concept") or "")
            return tools.segment(state["image_path"], state["work_dir"], state["spec"], note, concept)

        output = _run(mark, state, "segment", work)
        art = dict(state.get("art_director") or {})
        art["concept"] = str(output["segment"].get("concept") or "")
        output["art_director"] = art
        return output

    def art_director(state: State) -> dict[str, Any]:
        note = _note(state, "art_director")
        concept = str((state.get("art_director") or {}).get("concept") or "")

        def styles() -> dict[str, Any]:
            cutout = str(state.get("work_dir") or "") + "/" + str((state.get("segment") or {}).get("file") or "")
            result = tools.art_director(state["spec"], note, cutout)
            if concept:
                result["concept"] = concept
            return result

        return _run(mark, state, "art_director", styles)

    def scene(state: State) -> dict[str, Any]:
        cutout = str(state["work_dir"]) + "/" + state["segment"]["file"]
        direction = state.get("art_director") or {}
        prompts = [str(item) for item in (direction.get("selected") or []) if str(item).strip()]
        if not prompts and str(direction.get("prompt") or "").strip():
            prompts = [str(direction["prompt"])]
        count = _variation_count(direction.get("variations"))
        total = len(prompts) * count

        def work() -> dict[str, Any]:
            def progress(done: int) -> None:
                mark(state["job_id"], "scene", "running", detail=f"Image {done} of {total}")

            return tools.scene(cutout, state["work_dir"], prompts, count, _note(state, "scene"), progress)

        return _run(mark, state, "scene", work)

    def copy(state: State) -> dict[str, Any]:
        return _run(
            mark,
            state,
            "copy",
            lambda: tools.copy(state["spec"], _note(state, "copy"), state.get("marketplaces") or ["amazon"]),
        )

    def rules(state: State) -> dict[str, Any]:
        drafted = state["copy"]
        return _run(
            mark,
            state,
            "rules",
            lambda: tools.rules(drafted, state.get("marketplaces") or ["amazon"], state.get("spec") or {}),
        )

    graph = StateGraph(State)
    graph.add_node("segment", segment)
    graph.add_node("review_segment", _review("segment", mark))
    graph.add_node("art_director", art_director)
    graph.add_node("review_art_director", _review("art_director", mark))
    graph.add_node("scene", scene)
    graph.add_node("review_scene", _review("scene", mark))
    graph.add_node("copy", copy)
    graph.add_node("rules", rules)
    graph.add_node("review_rules", _review("rules", mark))

    graph.add_edge(START, "segment")
    graph.add_edge("segment", "review_segment")
    graph.add_conditional_edges(
        "review_segment",
        _route("segment", "art_director"),
        {"segment": "segment", "art_director": "art_director"},
    )
    graph.add_edge("art_director", "review_art_director")
    graph.add_conditional_edges(
        "review_art_director",
        _route_art,
        {"art_director": "art_director", "segment": "segment", "scene": "scene"},
    )
    graph.add_edge("scene", "review_scene")
    graph.add_conditional_edges("review_scene", _route_scene, {"scene": "scene", "copy": "copy", "segment": "segment"})
    graph.add_edge("copy", "rules")
    graph.add_edge("rules", "review_rules")
    graph.add_conditional_edges("review_rules", _route_rules, {"copy": "copy", "done": END})
    return graph.compile(checkpointer=checkpointer)


def _note(state: State, agent: str) -> str:
    return str((state.get("feedback") or {}).get(agent) or "")


def _variation_count(value: Any) -> int:
    try:
        count = int(value or 1)
    except (TypeError, ValueError):
        return 1
    return min(4, max(1, count))


def _style_sentence(value: Any) -> str:
    sentence = " ".join(str(value).split())
    if "16:9" not in sentence:
        sentence = sentence.rstrip(".") + ", 16:9."
    return sentence[:500]


def _image_choice(decision: dict[str, Any], output: dict[str, Any] | None) -> dict[str, Any]:
    images = [
        item
        for item in (output or {}).get("images") or []
        if isinstance(item, dict) and item.get("file")
    ]
    known = [str(item["file"]) for item in images]
    raw = decision.get("images")
    wanted = [str(item).strip() for item in raw if str(item).strip()] if isinstance(raw, list) else []
    chosen = [name for name in wanted if name in known] if wanted else known
    updated = dict(output or {})
    updated["selected"] = chosen
    if chosen:
        updated["file"] = chosen[0]
    return updated


def _scene_choice(decision: dict[str, Any], output: dict[str, Any] | None) -> dict[str, Any]:
    raw = decision.get("styles")
    selected = [_style_sentence(item) for item in raw if str(item).strip()] if isinstance(raw, list) else []
    if not selected and str(decision.get("prompt") or "").strip():
        selected = [_style_sentence(decision.get("prompt"))]
    if not selected:
        existing = (output or {}).get("styles") or []
        if existing:
            selected = [_style_sentence(existing[0])]
    updated = dict(output or {})
    updated["selected"] = selected[:8]
    updated["prompt"] = updated["selected"][0] if updated["selected"] else ""
    updated["variations"] = _variation_count(decision.get("variations"))
    return updated


def _run(mark: Mark, state: State, agent: str, work: Callable[[], Any]) -> dict[str, Any]:
    job_id = state["job_id"]
    mark(job_id, agent, "running")
    try:
        result = work()
    except Exception as exc:
        mark(job_id, agent, "failed", detail=str(exc))
        raise
    mark(job_id, agent, "waiting", output=result)
    return {agent: result}


def _review(agent: str, mark: Mark) -> Callable[[State], dict[str, Any]]:
    def review(state: State) -> dict[str, Any]:
        output = state.get(agent)
        approve_allowed = True
        if agent == "rules":
            approve_allowed = not (output or {}).get("violations")
        decision = interrupt(
            {"agent": agent, "output": output, "approve_allowed": approve_allowed}
        )
        if not isinstance(decision, dict) or decision.get("action") not in {"approve", "changes"}:
            decision = {"action": "changes", "note": "Send approve, or changes with a note."}
        note = str(decision.get("note") or "")
        feedback = dict(state.get("feedback") or {})
        if decision["action"] == "approve":
            if agent == "rules" and not approve_allowed:
                decision = {"action": "changes", "note": note or "The rule list is not clear."}
            elif agent == "art_director" and not (output or {}).get("styles"):
                current = dict(output) if isinstance(output, dict) else {}
                concept = " ".join(str(decision.get("prompt") or current.get("concept") or "").split())[:80]
                if not concept:
                    decision = {"action": "changes", "note": note or "Name the object, such as headphones."}
                else:
                    current["concept"] = concept
                    mark(state["job_id"], agent, "approved", output=current)
                    feedback.pop(agent, None)
                    return {"last_decision": decision, "feedback": feedback, "art_director": current}
            elif agent == "art_director":
                output = _scene_choice(decision, output if isinstance(output, dict) else None)
                if not output.get("selected"):
                    decision = {"action": "changes", "note": note or "Select at least one style."}
                else:
                    mark(state["job_id"], agent, "approved", output=output)
                    feedback.pop(agent, None)
                    return {"last_decision": decision, "feedback": feedback, "art_director": output}
            elif agent == "scene":
                output = _image_choice(decision, output if isinstance(output, dict) else None)
                if not output.get("selected"):
                    decision = {"action": "changes", "note": "Select at least one image."}
                else:
                    mark(state["job_id"], agent, "approved", output=output)
                    feedback.pop(agent, None)
                    return {"last_decision": decision, "feedback": feedback, "scene": output}
            elif agent == "rules":
                mark(state["job_id"], "copy", "approved", output=state.get("copy"))
                mark(state["job_id"], agent, "approved", output=output)
                feedback.pop("copy", None)
                feedback.pop(agent, None)
                return {"last_decision": decision, "feedback": feedback}
            else:
                mark(state["job_id"], agent, "approved", output=output)
                feedback.pop(agent, None)
        if decision["action"] == "changes":
            note = str(decision.get("note") or "")
            target = "copy" if agent == "rules" else "segment" if agent == "scene" else agent
            feedback[target] = note
            mark(state["job_id"], agent, "changes_requested", detail=note, output=output)
        return {"last_decision": decision, "feedback": feedback}

    return review


def _route_art(state: State) -> str:
    if state.get("last_decision", {}).get("action") == "changes":
        return "art_director"
    output = state.get("art_director") or {}
    if isinstance(output, dict) and output.get("styles"):
        return "scene"
    return "segment"


def _route_scene(state: State) -> str:
    if state.get("last_decision", {}).get("action") == "changes":
        return "segment"
    return "copy"


def _route(agent: str, nxt: str) -> Callable[[State], str]:
    def route(state: State) -> str:
        if state.get("last_decision", {}).get("action") == "changes":
            return agent
        return nxt

    return route


def _route_rules(state: State) -> str:
    if state.get("last_decision", {}).get("action") == "changes":
        return "copy"
    return "done"
