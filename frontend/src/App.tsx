import { FormEvent, useMemo, useState } from "react";
import { BookOpen, Loader2, Send, Sparkles } from "lucide-react";

type Source = {
  title: string;
  detail: string;
  url?: string | null;
  score?: number | null;
};

type Diagram = {
  scenario_type: "offside" | "penalty" | "throw_in" | "general";
  title: string;
  svg: string;
};

type ChatResponse = {
  answer: string;
  sources: Source[];
  diagram: Diagram | null;
};

type Message = {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  diagram?: Diagram | null;
};

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

const EXAMPLE_QUESTIONS = [
  "Why was that offside?",
  "When is a foul in the box a penalty?",
  "Who gets the throw-in when the ball goes out?",
];

export function App() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Ask a football rules question. I can explain the rule and draw a simple pitch diagram for offside, penalties, and throw-ins.",
    },
  ]);
  const [question, setQuestion] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const latestDiagram = useMemo(
    () => [...messages].reverse().find((message) => message.diagram)?.diagram,
    [messages],
  );

  async function submitQuestion(nextQuestion = question) {
    const trimmed = nextQuestion.trim();
    if (!trimmed || isLoading) return;

    setQuestion("");
    setError(null);
    setIsLoading(true);
    setMessages((current) => [...current, { role: "user", content: trimmed }]);

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: trimmed }),
      });

      if (!response.ok) {
        throw new Error("The API did not return a valid response.");
      }

      const data = (await response.json()) as ChatResponse;
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: data.answer,
          sources: data.sources,
          diagram: data.diagram,
        },
      ]);
    } catch {
      setError("Could not reach the Kickoff API. Start the FastAPI server on port 8000 and try again.");
    } finally {
      setIsLoading(false);
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void submitQuestion();
  }

  return (
    <main className="app-shell">
      <section className="workspace">
        <aside className="sidebar">
          <div className="brand">
            <div className="brand-mark">
              <Sparkles size={21} />
            </div>
            <div>
              <p>Kickoff</p>
              <span>Football-IQ</span>
            </div>
          </div>

          <div className="reference-block">
            <div className="section-label">
              <BookOpen size={16} />
              Starter Rules
            </div>
            <button onClick={() => void submitQuestion(EXAMPLE_QUESTIONS[0])}>Offside</button>
            <button onClick={() => void submitQuestion(EXAMPLE_QUESTIONS[1])}>Penalties</button>
            <button onClick={() => void submitQuestion(EXAMPLE_QUESTIONS[2])}>Throw-ins</button>
          </div>
        </aside>

        <section className="chat-panel">
          <header className="topbar">
            <div>
              <h1>Football rules, explained like match day.</h1>
              <p>Beginner answers with visual pitch diagrams.</p>
            </div>
          </header>

          <div className="content-grid">
            <section className="conversation" aria-label="Chat conversation">
              {messages.map((message, index) => (
                <article className={`message ${message.role}`} key={`${message.role}-${index}`}>
                  <p>{message.content}</p>
                  {message.sources?.map((source) => (
                    <div className="source" key={source.title}>
                      <div className="source-title">
                        {source.url ? (
                          <a href={source.url} rel="noreferrer" target="_blank">
                            {source.title}
                          </a>
                        ) : (
                          <strong>{source.title}</strong>
                        )}
                        {source.score ? <em>score {source.score}</em> : null}
                      </div>
                      <span>{source.detail}</span>
                    </div>
                  ))}
                </article>
              ))}
              {isLoading ? (
                <article className="message assistant loading">
                  <Loader2 size={18} />
                  <p>Thinking through the rule...</p>
                </article>
              ) : null}
            </section>

            <aside className="diagram-panel" aria-label="Pitch diagram">
              <div className="diagram-heading">
                <span>Visual Explainer</span>
                <strong>{latestDiagram?.title ?? "Waiting for a scenario"}</strong>
              </div>
              {latestDiagram ? (
                <div className="pitch" dangerouslySetInnerHTML={{ __html: latestDiagram.svg }} />
              ) : (
                <div className="empty-pitch">
                  <span>Ask about offside, a penalty, or a throw-in.</span>
                </div>
              )}
            </aside>
          </div>

          <form className="composer" onSubmit={handleSubmit}>
            <input
              aria-label="Ask a football rule question"
              placeholder="Ask: why was that offside?"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
            />
            <button aria-label="Send question" disabled={isLoading || !question.trim()} type="submit">
              {isLoading ? <Loader2 size={20} /> : <Send size={20} />}
            </button>
          </form>
          {error ? <p className="error">{error}</p> : null}
        </section>
      </section>
    </main>
  );
}
