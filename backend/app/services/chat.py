from app.schemas import ChatRequest, ChatResponse, Diagram, Source
from app.services.diagram import render_pitch_svg
from app.services.rag import build_grounded_answer, retrieve_laws, scenario_from_results, sources_from_results


def answer_question(request: ChatRequest) -> ChatResponse:
    question = request.question.strip()
    results = retrieve_laws(question)
    scenario_type = scenario_from_results(results)
    answer = build_grounded_answer(question, results)

    diagram = None
    if scenario_type != "general":
        diagram = Diagram(
            scenario_type=scenario_type,
            title=diagram_title(scenario_type),
            svg=render_pitch_svg(scenario_type),
        )

    return ChatResponse(
        answer=answer,
        sources=sources_from_results(results),
        diagram=diagram,
    )


def diagram_title(scenario_type: str) -> str:
    titles = {
        "offside": "Offside line example",
        "penalty": "Penalty area foul example",
        "throw_in": "Throw-in restart example",
    }
    return titles[scenario_type]
