import type { App as McpApp } from "@modelcontextprotocol/ext-apps";
import { useApp } from "@modelcontextprotocol/ext-apps/react";
import { useState } from "react";
import type { QuestionConfig, Answers, Question } from "./types";
import { QuestionPager } from "./components/QuestionPager";

export function App() {
  const [config, setConfig] = useState<QuestionConfig | null>(null);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [appRef, setAppRef] = useState<McpApp | null>(null);

  const { app, error: appError } = useApp({
    appInfo: { name: "Duck Questions", version: "1.0.0" },
    capabilities: {},
    onAppCreated: (createdApp) => {
      setAppRef(createdApp);
      createdApp.ontoolinput = (params) => {
        try {
          const questions = params.arguments?.questions as Question[] | undefined;
          if (questions) {
            setConfig({
              session_id: "",
              questions,
            });
          }
        } catch {
          setError("Failed to parse question configuration");
        }
      };
    },
  });

  const handleSubmit = async (answers: Answers) => {
    const currentApp = appRef || app;
    if (!currentApp || !config) return;
    try {
      await currentApp.callServerTool({
        name: "submit_answers",
        arguments: {
          session_id: "",
          answers,
        },
      });
      setSubmitted(true);
    } catch {
      setError("Failed to submit answers");
    }
  };

  if (appError) return <div className="status error">App error: {String(appError)}</div>;
  if (error) return <div className="status error">{error}</div>;
  if (submitted) return <div className="status success">Answers submitted! ✓</div>;
  if (!config) return <div className="status loading">Waiting for questions...</div>;

  return <QuestionPager config={config} onSubmit={handleSubmit} />;
}
