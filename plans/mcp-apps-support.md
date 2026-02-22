# Implementation Plan: MCP Apps Support for duck-mcp

## Overview

Add MCP Apps support to duck-mcp — interactive HTML UIs rendered inside MCP hosts (Claude Desktop, VS Code Copilot, etc.) in sandboxed iframes. A new `ask_questions` tool will accept structured question configurations and present a rich React-based form UI to the user, complementing the existing elicitation-based tools.

### Goals
- Add a new `ask_questions` tool backed by a single React MCP App
- Support single-select, multi-select, and free-text question types in one form
- Serve the UI as a bundled single HTML file via a `ui://` resource
- Keep all existing elicitation tools unchanged

### Non-Goals
- Replacing existing elicitation tools
- Multiple separate MCP App UIs
- Server-side rendering of the form

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ MCP Host (Claude Desktop / VS Code Copilot)                 │
│                                                             │
│  Agent calls ask_questions(questions=[...])                  │
│       │                                                     │
│       ▼                                                     │
│  Host fetches ui://duck/mcp-app.html resource               │
│  (auto-served by FastMCP with text/html;profile=mcp-app)    │
│       │                                                     │
│       ▼                                                     │
│  ┌──────────────────────────────────────────┐               │
│  │ Sandboxed iframe (React MCP App)         │               │
│  │                                          │               │
│  │  ontoolresult → receives questions JSON  │               │
│  │  Renders dynamic form                    │               │
│  │  User fills + submits                    │               │
│  │  callServerTool("submit_answers", data)  │               │
│  └──────────────────────────────────────────┘               │
│       │                                                     │
│       ▼                                                     │
│  submit_answers tool stores result                          │
│  ask_questions returns collected answers                     │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────┐
│ duck-mcp FastMCP 3.0 Server                              │
│                                                          │
│  from fastmcp.server.apps import AppConfig               │
│                                                          │
│  @mcp.resource("ui://duck/mcp-app.html")                 │
│    → auto-serves HTML with correct MIME type              │
│                                                          │
│  @mcp.tool(app=AppConfig(resource_uri=RESOURCE_URI))     │
│    ask_questions → returns question config                │
│                                                          │
│  @mcp.tool(app=AppConfig(                                │
│      resource_uri=RESOURCE_URI, visibility=["app"]))      │
│    submit_answers → receives form answers (App-only)      │
└──────────────────────────────────────────────────────────┘
```

### FastMCP 3.0 Apps API

FastMCP 3.0 provides first-class MCP Apps support via `fastmcp.server.apps`:

- **`AppConfig`** — typed model linking tools to UI resources. Use `app=AppConfig(resource_uri="ui://...")` on `@mcp.tool`.
- **`ui://` resources** — automatically served with MIME type `text/html;profile=mcp-app`. No manual MIME type configuration needed.
- **`visibility`** — controls where a tool appears: `["model"]` (default, LLM-visible), `["app"]` (only callable from App UI), or `["model", "app"]` (both).
- **`ResourceCSP`** — Content Security Policy for iframe (e.g., allow CDN scripts).
- **`ResourcePermissions`** — request browser capabilities (camera, clipboard, etc.).
- **`ctx.client_supports_extension(UI_EXTENSION_ID)`** — runtime check if the host supports Apps.
- **`ToolResult`** from `fastmcp.tools` — explicit control over tool response content types.

### Data Flow

1. Agent calls `ask_questions` with a `questions` array
2. Tool returns the questions config as text content (this becomes the tool result the App receives)
3. Host preloads `ui://duck/mcp-app.html` and renders it in an iframe
4. React App receives the tool result via `app.ontoolresult` callback
5. App parses the question config JSON and renders a dynamic form
6. User fills out the form and clicks Submit
7. App calls `app.callServerTool("submit_answers", { answers: {...} })`
8. The `submit_answers` tool on the server processes and stores the answers
9. The `ask_questions` tool returns the structured answers to the agent

### Answer Collection Strategy

Use `app.callServerTool()` to call a companion `submit_answers` tool. This is the most explicit and debuggable pattern — the server has a dedicated tool that receives structured answer data, and the main `ask_questions` tool can coordinate with it.

**Alternative considered**: `app.updateContext()` — less explicit, harder to test independently. Rejected in favor of the companion tool approach.

**Note on synchronization**: The `ask_questions` tool needs to wait for the user to submit answers via the UI. This requires an async coordination mechanism on the server side (e.g., `asyncio.Event` or `asyncio.Queue`) so that `ask_questions` blocks until `submit_answers` is called by the App. A per-invocation correlation ID will link the two calls.

### UI Design

The MCP App uses a **pager/wizard-style layout**:
- **One question per page** — each question occupies its own "page" within the App
- **Navigation arrows** (← →) to move between question pages
- **Page indicator** showing current position (e.g., "1 / 3")
- **Submit button** on the last page (replaces the "Next" arrow)
- **VS Code dark theme** — dark background (#1e1e1e), VS Code-style colors, borders, and system font stack at 13px

See the full [UI Design Specification](#ui-design-specification) section below for wireframes, theme details, and navigation behavior.

---

## UI Design Specification

### Layout: Pager/Wizard

The MCP App uses a pager (wizard) layout where each question occupies its own page:

```
┌────────────────────────────────────┐
│  What framework do you prefer?     │  ← Question label
│                                    │
│  ○ React                           │  ← Radio buttons (single-select)
│  ○ Vue                             │
│  ○ Svelte                          │
│  ○ Angular                         │
│                                    │
│  ← Back          1 / 3      Next → │  ← Pager controls
└────────────────────────────────────┘

┌────────────────────────────────────┐
│  Which features do you need?       │
│                                    │
│  ☐ Authentication                  │  ← Checkboxes (multi-select)
│  ☑ Database                        │
│  ☑ REST API                        │
│  ☐ WebSockets                      │
│                                    │
│  ← Back          2 / 3      Next → │
└────────────────────────────────────┘

┌────────────────────────────────────┐
│  Any additional notes?             │
│                                    │
│  ┌──────────────────────────────┐  │  ← Textarea (open text)
│  │                              │  │
│  │                              │  │
│  └──────────────────────────────┘  │
│                                    │
│  ← Back          3 / 3    Submit → │  ← Submit on last page
└────────────────────────────────────┘
```

### Theme: VS Code Dark

- Background: #1e1e1e (primary), #252526 (secondary/cards)
- Text: #cccccc (primary), #969696 (secondary)
- Accent: #0078d4 (VS Code blue)
- Borders: #3c3c3c
- Input backgrounds: #3c3c3c
- Font: System font stack at 13px (VS Code default)
- Custom-styled radio buttons and checkboxes

### Markdown & Code Rendering

Question labels, option text, and text answers may contain **full markdown** (headings, bold, italic, lists, links, tables, etc.) with embedded code blocks. Render all markdown properly:

- Use **`react-markdown`** to parse and render markdown to React elements
- Use **`rehype-highlight`** (rehype plugin for highlight.js) to automatically syntax-highlight fenced code blocks
- Fenced code blocks (`` ```lang ... ``` ``) render in `<pre><code>` with highlight.js coloring
- Inline code (`` `...` ``) renders with `--bg-secondary` background and monospace font
- Markdown elements (headings, bold, italic, lists, links, blockquotes, tables) render with VS Code dark theme styling
- highlight.js uses the **VS Code Dark+** theme (`vs2015`) for code coloring
- All dependencies bundled via npm/Vite (no CDN — keeps the single-file bundle self-contained)
- Import only commonly-needed highlight.js languages to minimize bundle size (javascript, typescript, python, json, bash, html, css, kotlin, swift, xml, yaml, sql, go, rust, java, c, cpp)
- `highlightjs-badge` or similar is NOT needed — keep it minimal

### Navigation Behavior

- **Back arrow**: Disabled (grayed out) on the first page
- **Next arrow**: Advances to the next question (validates required fields first)
- **Submit button**: Replaces "Next" on the last page; submits all answers
- **Page indicator**: Shows "X / N" format (e.g., "1 / 3")
- **Keyboard**: Arrow keys or Enter to navigate, Tab between options

---

## Phases

### Phase 1: Server-Side Foundation
**Goal**: Register the new tool, resource, and answer collection mechanism in `server.py`.

### Phase 2: React MCP App
**Goal**: Build the React frontend that renders dynamic forms and communicates with the host.

### Phase 3: Build Pipeline
**Goal**: Integrate the UI build into the project's build/test/deploy workflow.

### Phase 4: Testing
**Goal**: Unit tests for the Python server, integration tests, and manual validation.

### Phase 5: Documentation & Cleanup
**Goal**: Update README, add developer docs, finalize for release.

---

## Phase 1: Server-Side Foundation

### Task 1.1: Add `ask_questions` tool with `AppConfig`

**File**: `server.py`

Add a new tool that:
- Accepts a structured `questions` parameter (list of question objects)
- Uses FastMCP 3.0's `app=AppConfig(resource_uri=...)` to link to the MCP App UI
- Returns the questions config as JSON text content (the App will receive this via `ontoolresult`)
- Optionally checks if the host supports Apps via `ctx.client_supports_extension(UI_EXTENSION_ID)`

```python
import json
import uuid

from fastmcp import Context
from fastmcp.server.apps import AppConfig, UI_EXTENSION_ID

RESOURCE_URI = "ui://duck/mcp-app.html"

@mcp.tool(app=AppConfig(resource_uri=RESOURCE_URI))
async def ask_questions(questions: list[dict], ctx: Context) -> str:
    """
    Ask the user one or more questions via an interactive form UI.

    Each question has: id, type (single_select | multi_select | text),
    label, options (for select types), and required (bool).

    Args:
        questions: List of question configuration objects

    Returns:
        JSON string with the user's answers
    """
    session_id = str(uuid.uuid4())
    config = {"session_id": session_id, "questions": questions}

    if ctx.client_supports_extension(UI_EXTENSION_ID):
        # Host supports MCP Apps — return config for the App UI to render
        return json.dumps(config)
    else:
        # Fallback: return plain text for non-App hosts
        lines = ["Please answer the following questions:"]
        for q in questions:
            lines.append(f"\n{q['label']}")
            if q.get('options'):
                for opt in q['options']:
                    lines.append(f"  - {opt}")
        return "\n".join(lines)
```

**Design note on answer collection**: The `ask_questions` tool returns the questions config immediately. The App renders the form, the user submits, and the App calls `submit_answers` via `app.callServerTool()`. The agent receives the `submit_answers` result as a separate tool call in the conversation. This non-blocking approach avoids async coordination complexity.

**Acceptance Criteria**:
- [ ] `ask_questions` tool registered with `app=AppConfig(resource_uri=RESOURCE_URI)`
- [ ] Tool accepts `questions` list parameter with proper schema
- [ ] Tool returns questions config as JSON text
- [ ] Graceful fallback when host doesn't support Apps extension

---

### Task 1.2: Add `submit_answers` companion tool (App-only visibility)

**File**: `server.py`

A tool called by the MCP App (via `app.callServerTool()`) to deliver form answers back to the server. Uses `visibility=["app"]` so it's **hidden from the LLM** — only callable from within the App UI.

```python
@mcp.tool(
    app=AppConfig(
        resource_uri=RESOURCE_URI,
        visibility=["app"],  # Hidden from LLM, only callable from App UI
    )
)
async def submit_answers(session_id: str, answers: dict) -> str:
    """
    Receive answers from the MCP App form UI.
    Called by the MCP App when the user submits the form.

    Args:
        session_id: The session ID from the ask_questions call
        answers: Dictionary mapping question IDs to user answers

    Returns:
        Confirmation of received answers
    """
    formatted = json.dumps(answers, indent=2)
    return f"User answers received:\n{formatted}"
```

**Key**: `visibility=["app"]` ensures:
- The LLM never sees or tries to call `submit_answers` directly
- Only the MCP App UI can invoke it via `app.callServerTool()`
- Cleaner tool listing for the agent

**Acceptance Criteria**:
- [ ] `submit_answers` tool registered with `visibility=["app"]`
- [ ] Tool does NOT appear in LLM-visible tool listing
- [ ] Tool IS callable from the MCP App via `callServerTool()`
- [ ] Accepts `session_id` and `answers` parameters
- [ ] Returns formatted answer data

---

### Task 1.3: Add `ui://duck/mcp-app.html` resource

**File**: `server.py`

Register a `ui://` resource that serves the bundled HTML file. FastMCP 3.0 **automatically serves `ui://` resources with MIME type `text/html;profile=mcp-app`** — no manual MIME type configuration needed.

```python
from pathlib import Path

UI_DIST_PATH = Path(__file__).parent / "dist" / "mcp-app.html"

@mcp.resource(RESOURCE_URI)
def mcp_app_resource() -> str:
    """Serve the MCP App HTML for the ask_questions tool UI."""
    if not UI_DIST_PATH.exists():
        raise FileNotFoundError(
            f"MCP App HTML not found at {UI_DIST_PATH}. "
            "Run 'make build-ui' to build the UI first."
        )
    return UI_DIST_PATH.read_text(encoding="utf-8")
```

**Note**: Since we bundle React + highlight.js via Vite (no external CDN), the default deny-all CSP is fine. If we later need to load external resources, add CSP:
```python
from fastmcp.server.apps import AppConfig, ResourceCSP

@mcp.resource(
    RESOURCE_URI,
    app=AppConfig(csp=ResourceCSP(resource_domains=["https://unpkg.com"]))
)
def mcp_app_resource() -> str: ...
```

**Acceptance Criteria**:
- [ ] Resource registered at `ui://duck/mcp-app.html`
- [ ] Returns the contents of `dist/mcp-app.html`
- [ ] FastMCP auto-serves with `text/html;profile=mcp-app` MIME type (no manual config)
- [ ] Clear error message if HTML file not built yet

---

### Task 1.4: Verify FastMCP AppConfig integration

**Description**: Write tests confirming that FastMCP 3.0's `AppConfig` correctly wires up the tool-to-resource linkage and visibility settings.

**File**: `tests/test_server.py` (add tests)

```python
from fastmcp import Client

@pytest.mark.asyncio
async def test_ask_questions_has_app_config():
    """Verify ask_questions tool is linked to the MCP App resource."""
    async with Client(mcp) as client:
        tools = await client.list_tools()
        ask_q = next(t for t in tools if t.name == "ask_questions")
        # FastMCP 3.0 exposes AppConfig as _meta.ui in the protocol
        assert ask_q.meta is not None
        ui_meta = ask_q.meta.get("ui", {})
        assert ui_meta.get("resourceUri") == "ui://duck/mcp-app.html"

@pytest.mark.asyncio
async def test_submit_answers_app_only_visibility():
    """Verify submit_answers is hidden from LLM (app-only visibility)."""
    async with Client(mcp) as client:
        tools = await client.list_tools()
        # submit_answers should NOT appear in the default (model) tool listing
        tool_names = [t.name for t in tools]
        assert "submit_answers" not in tool_names
        # But it should still be callable from the App
```

**Note**: FastMCP 3.0 handles the `AppConfig` → `_meta.ui` mapping natively. The `visibility=["app"]` setting ensures `submit_answers` is excluded from LLM-visible tool listings. These tests verify both behaviors.

**Acceptance Criteria**:
- [ ] Test confirms `ask_questions` has `_meta.ui.resourceUri` in tool listing
- [ ] Test confirms `submit_answers` is NOT in the default tool listing (app-only)
- [ ] Both tests pass with FastMCP >= 3.0.0

---

## Phase 2: React MCP App

### Task 2.1: Initialize React + Vite + TypeScript project

**Directory**: `ui/`

```
ui/
├── package.json
├── vite.config.ts
├── tsconfig.json
├── tsconfig.node.json
├── index.html            # Vite entry HTML
└── src/
    ├── main.tsx           # React entry point
    ├── App.tsx            # Main App component
    ├── types.ts           # Shared type definitions
    ├── components/
    │   ├── QuestionPager.tsx    # Main pager/wizard component
    │   ├── PagerControls.tsx    # Navigation arrows + page indicator
    │   ├── SingleSelectPage.tsx # Radio buttons for one question
    │   ├── MultiSelectPage.tsx  # Checkboxes for one question
    │   └── TextInputPage.tsx    # Textarea for one question
    └── styles/
        └── app.css
```

**Key dependencies**:
```json
{
  "dependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "@modelcontextprotocol/ext-apps": "latest",
    "highlight.js": "^11.11.0",
    "react-markdown": "^9.0.0",
    "rehype-highlight": "^7.0.0"
  },
  "devDependencies": {
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "@vitejs/plugin-react": "^4.0.0",
    "typescript": "^5.6.0",
    "vite": "^6.0.0",
    "vite-plugin-singlefile": "^2.0.0"
  }
}
```

**Vite config** (`ui/vite.config.ts`):
```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { viteSingleFile } from "vite-plugin-singlefile";

export default defineConfig({
  plugins: [react(), viteSingleFile()],
  build: {
    outDir: "../dist",
    emptyOutDir: true,
  },
});
```

**Acceptance Criteria**:
- [ ] `npm install` succeeds in `ui/`
- [ ] `npm run build` produces `dist/mcp-app.html` (single file, no external assets)
- [ ] HTML file size is reasonable (< 500KB)

---

### Task 2.2: Define TypeScript types

**File**: `ui/src/types.ts`

```typescript
export type QuestionType = "single_select" | "multi_select" | "text";

export interface Question {
  id: string;
  type: QuestionType;
  label: string;       // May contain markdown code blocks/inline code
  options?: string[];  // Option text may also contain inline code
  required?: boolean;
}

export interface QuestionConfig {
  session_id: string;
  questions: Question[];
}

export type AnswerValue = string | string[] | null;

export interface Answers {
  [questionId: string]: AnswerValue;
}
```

**Acceptance Criteria**:
- [ ] Types compile without errors
- [ ] Types match the Python-side schema from `ask_questions`

---

### Task 2.3: Implement MCP App bootstrap with `@modelcontextprotocol/ext-apps`

**File**: `ui/src/App.tsx`

```tsx
import { useApp } from "@modelcontextprotocol/ext-apps/react";
import { useState } from "react";
import { QuestionConfig, Answers } from "./types";
import { QuestionPager } from "./components/QuestionPager";

export function App() {
  const [config, setConfig] = useState<QuestionConfig | null>(null);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { app, error: appError } = useApp({
    appInfo: { name: "Duck Questions", version: "1.0.0" },
    onAppCreated: (app) => {
      app.ontoolresult = async (result) => {
        try {
          // The tool result contains the questions config as JSON text
          const text = result.content
            ?.filter((c) => c.type === "text")
            .map((c) => c.text)
            .join("");
          if (text) {
            setConfig(JSON.parse(text));
          }
        } catch (e) {
          setError("Failed to parse question configuration");
        }
      };
    },
  });

  const handleSubmit = async (answers: Answers) => {
    if (!app || !config) return;
    try {
      await app.callServerTool("submit_answers", {
        session_id: config.session_id,
        answers,
      });
      setSubmitted(true);
    } catch (e) {
      setError("Failed to submit answers");
    }
  };

  if (appError) return <div className="error">App error: {appError}</div>;
  if (error) return <div className="error">{error}</div>;
  if (submitted) return <div className="success">Answers submitted! ✓</div>;
  if (!config) return <div className="loading">Waiting for questions...</div>;

  return <QuestionPager config={config} onSubmit={handleSubmit} />;
}
```

**Acceptance Criteria**:
- [ ] App initializes with `useApp` hook
- [ ] `ontoolresult` callback parses question config
- [ ] Passes config to `QuestionPager` component (not `QuestionForm`)
- [ ] Submit calls `app.callServerTool("submit_answers", ...)`
- [ ] Loading, error, and success states render correctly

---

### Task 2.4: Implement pager components and VS Code dark theme

Component hierarchy:

```
App.tsx
└── QuestionPager.tsx          (main pager component)
    ├── PagerControls.tsx      (arrows + page indicator)
    ├── SingleSelectPage.tsx   (radio buttons for one question)
    ├── MultiSelectPage.tsx    (checkboxes for one question)
    └── TextInputPage.tsx      (textarea for one question)
```

#### `ui/src/components/QuestionPager.tsx`
The main pager/wizard component:
- Maintains `currentPage` state (0-indexed)
- Shows one question at a time
- Renders the correct page component based on question type (`single_select` → `SingleSelectPage`, `multi_select` → `MultiSelectPage`, `text` → `TextInputPage`)
- Navigation: left arrow (disabled on first page), right arrow / "Submit" button on last page
- Page indicator: "1 / 3" text or dot indicators
- Validates current question before allowing navigation to next page
- Smooth transition between pages (optional: CSS slide animation)
- Manages form state (answers map) across all pages
- Calls `onSubmit(answers)` when the user clicks Submit on the last page

#### `ui/src/components/PagerControls.tsx`
Bottom navigation bar:
- Left arrow button (← or "Back") — disabled on the first page
- Page indicator ("Question 1 of 3") in `--text-secondary` color
- Right arrow button (→ or "Next"), replaced with "Submit" on the last page
- Buttons styled as VS Code-style buttons (blue accent for primary actions)

#### `ui/src/components/SingleSelectPage.tsx`
Single question page with radio buttons:
- Question label/title at top (slightly larger text, `--text-primary` color)
- Label rendered via `Markdown` component (supports full markdown with code blocks)
- Vertical list of radio button options (custom styled to match VS Code)
- Option labels rendered via `Markdown` (inline code, bold, etc. supported)
- Required indicator if applicable
- Accessible: proper `<fieldset>`, `<legend>`, `<label>` usage

#### `ui/src/components/MultiSelectPage.tsx`
Single question page with checkboxes:
- Question label/title at top, rendered via `Markdown`
- Vertical list of checkbox options (custom styled to match VS Code)
- Option labels rendered via `Markdown` (inline code, bold, etc. supported)
- Accessible: proper labeling

#### `ui/src/components/TextInputPage.tsx`
Single question page with textarea:
- Question label/title at top, rendered via `Markdown`
- Full-width textarea with dark background (`#3c3c3c`) and subtle border (`#5a5a5a`)

#### `ui/src/components/Markdown.tsx`
Reusable component for rendering markdown content that may include code:
- Uses **`react-markdown`** to parse and render full markdown (headings, bold, italic, lists, links, blockquotes, tables, code blocks, inline code)
- Uses **`rehype-highlight`** plugin to automatically apply highlight.js syntax highlighting to fenced code blocks
- Fenced code blocks → `<pre><code class="hljs language-xxx">` with syntax colors from `vs2015` theme
- Inline code → `<code class="inline-code">` with monospace font and subtle background
- Markdown elements styled to match VS Code dark theme (see `app.css`)
- Import only commonly-needed highlight.js languages to minimize bundle size
- Props: `content: string` (the markdown text to render), `inline?: boolean` (for option labels — renders without wrapping `<p>` tags)

#### `ui/src/styles/app.css`

VS Code dark theme styling (no light mode — matches the VS Code aesthetic):

```css
/* VS Code Dark Theme Colors */
:root {
  --bg-primary: #1e1e1e;
  --bg-secondary: #252526;
  --bg-hover: #2a2d2e;
  --bg-active: #37373d;
  --text-primary: #cccccc;
  --text-secondary: #969696;
  --accent: #0078d4;          /* VS Code blue */
  --accent-hover: #1177bb;
  --border: #3c3c3c;
  --input-bg: #3c3c3c;
  --input-border: #5a5a5a;
  --button-bg: #0078d4;
  --button-hover: #1177bb;
  --button-text: #ffffff;
  --error: #f14c4c;
  --success: #73c991;
  --font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-size: 13px;
}

body {
  background: var(--bg-primary);
  color: var(--text-primary);
  font-family: var(--font-family);
  font-size: var(--font-size);
  margin: 0;
  padding: 16px;
}
```

Key styling details:
- Radio buttons and checkboxes: custom styled to match VS Code
- Input fields: dark background (`#3c3c3c`) with subtle border (`#5a5a5a`)
- Buttons: VS Code blue accent (`#0078d4`) for primary actions
- Navigation arrows: subtle icon buttons, not too prominent
- Page indicator: small text in `--text-secondary` color
- Question labels: slightly larger text, `--text-primary` color
- Smooth transitions between pages (opacity + transform)
- Focus states: visible outlines using `--accent` color
- Compact spacing to fit well in iframe context

**Code block styling** (via highlight.js `vs2015` theme + custom overrides):
- Import `highlight.js/styles/vs2015.css` globally in `main.tsx`
- Fenced code blocks: `<pre><code>` with `--bg-secondary` background, `border: 1px solid var(--border)`, `border-radius: 4px`, `padding: 12px`, `overflow-x: auto`, monospace font (`'Cascadia Code', 'Fira Code', 'Consolas', monospace`)
- Inline code: `<code class="inline-code">` with `background: var(--bg-secondary)`, `padding: 1px 4px`, `border-radius: 3px`, monospace font, slightly smaller size
- highlight.js handles syntax coloring; the `vs2015` theme aligns with VS Code Dark+

**Markdown element styling** (for content rendered by `react-markdown`):
- Headings (`h1`–`h4`): `--text-primary`, scaled sizes, bottom border on `h1`/`h2`
- Bold/italic: `--text-primary` with appropriate font-weight/style
- Lists (`ul`, `ol`): proper indentation, `--text-primary` bullets/numbers
- Links (`a`): `--accent` color (#0078d4), underline on hover
- Blockquotes: left border in `--border` color, `--text-secondary` text, `--bg-secondary` background
- Tables: `--border` borders, `--bg-secondary` header background, compact padding
- Horizontal rules: `--border` color
- Paragraphs: `--text-primary`, normal line-height
- All markdown elements respect the compact spacing needed for iframe context

**Acceptance Criteria**:
- [ ] Pager shows one question per page
- [ ] Navigation arrows work (back/next)
- [ ] Page indicator shows current position (e.g., "1 / 3")
- [ ] Submit appears only on the last page
- [ ] Required field validation prevents advancing to next page
- [ ] VS Code dark theme styling applied consistently
- [ ] All three question types render correctly on their page
- [ ] Code blocks in question labels render with highlight.js syntax highlighting
- [ ] Inline code in option text renders with monospace font and subtle background
- [ ] Full markdown (bold, italic, lists, links, headings, blockquotes, tables) renders correctly in question labels and options
- [ ] Smooth transitions between pages
- [ ] Keyboard navigation works (arrows, Enter to advance)
- [ ] No external CSS frameworks (keep bundle small, highlight.js is bundled via npm)

---

### Task 2.5: Wire up `main.tsx` and `index.html`

**File**: `ui/index.html`
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Duck Questions</title>
</head>
<body>
  <div id="root"></div>
  <script type="module" src="/src/main.tsx"></script>
</body>
</html>
```

**File**: `ui/src/main.tsx`
```tsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import "./styles/app.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
```

**Acceptance Criteria**:
- [ ] `npm run dev` launches dev server for local testing
- [ ] `npm run build` produces single `dist/mcp-app.html` with all JS/CSS inlined

---

## Phase 3: Build Pipeline

### Task 3.1: Add `build-ui` Makefile target

**File**: `Makefile` (modify)

Add targets:
```makefile
build-ui: ## Build the MCP App UI
	cd ui && npm ci && npm run build

clean-ui: ## Clean UI build artifacts
	rm -rf dist/
	rm -rf ui/node_modules
```

Update existing targets:
```makefile
build: build-ui ## Build the package (includes UI)
	uv build

clean: clean-ui ## Clean up build artifacts and cache (includes UI)
	... existing clean commands ...
```

**Acceptance Criteria**:
- [ ] `make build-ui` installs npm deps and produces `dist/mcp-app.html`
- [ ] `make build` runs UI build before Python package build
- [ ] `make clean` removes UI artifacts too

---

### Task 3.2: Update `scripts/build.sh`

**File**: `scripts/build.sh` (modify)

Add UI build step before the Python build:
```bash
# Build UI
echo "🎨 Building MCP App UI..."
cd ui && npm ci && npm run build && cd ..
```

**Acceptance Criteria**:
- [ ] `scripts/build.sh` builds UI first, then runs tests, then builds Python package

---

### Task 3.3: Update `pyproject.toml` to include `dist/`

**File**: `pyproject.toml` (modify)

Ensure the built HTML file is included in the wheel and FastMCP 3.0+ is required:
```toml
[project]
dependencies = [
    "fastmcp>=3.0.0",
]

[tool.hatch.build.targets.wheel]
include = ["server.py", "fastmcp.json", "dist/mcp-app.html"]
```

**Acceptance Criteria**:
- [ ] `fastmcp>=3.0.0` in project dependencies (for AppConfig, UI_EXTENSION_ID support)
- [ ] `uv build` produces a wheel that includes `dist/mcp-app.html`

---

### Task 3.4: Add `.gitignore` entries

**File**: `.gitignore` (create or modify)

```gitignore
# UI build artifacts
dist/
ui/node_modules/

# Existing
__pycache__/
*.pyc
*.egg-info
.pytest_cache
htmlcov
.coverage
```

**Decision**: Whether to commit `dist/mcp-app.html` or gitignore it.
- **Gitignore (recommended)**: Keeps repo clean, requires build step before running. CI builds it.
- **Commit**: Simpler for users who clone and run without building. But creates merge conflicts.

Recommend gitignoring and requiring `make build-ui` as a prerequisite.

**Acceptance Criteria**:
- [ ] `dist/` and `ui/node_modules/` are gitignored
- [ ] README documents the build prerequisite

---

### Task 3.5: Add `ui/package.json` scripts

**File**: `ui/package.json`

```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "typecheck": "tsc --noEmit"
  }
}
```

**Acceptance Criteria**:
- [ ] `npm run dev` starts Vite dev server
- [ ] `npm run build` produces `../dist/mcp-app.html`
- [ ] `npm run typecheck` validates TypeScript

---

## Phase 4: Testing

### Task 4.1: Python unit tests for new tools

**File**: `tests/test_server.py` (modify)

Add tests:

1. **`test_ask_questions_tool_exists`** — Verify `ask_questions` appears in tool listing
2. **`test_ask_questions_has_ui_meta`** — Verify `_meta.ui.resourceUri` is present (Task 1.4)
3. **`test_submit_answers_tool_exists`** — Verify `submit_answers` appears in tool listing
4. **`test_ask_questions_returns_config`** — Call `ask_questions` with sample questions, verify it returns valid JSON with session_id and questions
5. **`test_submit_answers_returns_formatted`** — Call `submit_answers` with sample answers, verify formatted output
6. **`test_mcp_app_resource_exists`** — Verify `ui://duck/mcp-app.html` is in resource listing
7. **`test_mcp_app_resource_serves_html`** — Read the resource, verify it returns HTML content (requires `dist/mcp-app.html` to exist; skip if not built)

**Acceptance Criteria**:
- [ ] All new tests pass with `make test`
- [ ] Tests for resource HTML are skippable when UI not built
- [ ] Existing tests remain green

---

### Task 4.2: UI typecheck in CI

Ensure `npm run typecheck` in `ui/` is part of the test pipeline.

**File**: `scripts/test.sh` (modify)

Add:
```bash
# Typecheck UI
echo "🎨 Typechecking MCP App UI..."
cd ui && npm ci && npm run typecheck && cd ..
```

**File**: `Makefile` (modify)

Add:
```makefile
test-ui: ## Typecheck the MCP App UI
	cd ui && npm ci && npm run typecheck
```

**Acceptance Criteria**:
- [ ] `make test-ui` runs TypeScript type checking
- [ ] `scripts/test.sh` includes UI typecheck

---

### Task 4.3: Manual end-to-end testing

**Description**: Test the full flow in a real MCP host.

**Steps**:
1. `make build-ui` to build the React app
2. `make run` or `fastmcp dev` to start the server
3. Connect from Claude Desktop or VS Code Copilot
4. Have the agent call `ask_questions` with a sample question config
5. Verify the form renders in the host's iframe
6. Fill out the form and submit
7. Verify the agent receives the answers

**Acceptance Criteria**:
- [ ] Form renders correctly in at least one MCP host
- [ ] All three question types work
- [ ] Submit delivers answers back to the agent
- [ ] Error states (missing required fields) work correctly

---

## Phase 5: Documentation & Cleanup

### Task 5.1: Update README

**File**: `README.md` (modify)

Add sections:
- **MCP Apps** section explaining the `ask_questions` tool and UI
- **Building the UI** section with prerequisites (Node.js 18+) and `make build-ui`
- Update **Project Structure** to include `ui/` and `dist/`
- Update **Features** list to include `ask_questions`
- Add note about MCP Apps host compatibility

**Acceptance Criteria**:
- [ ] README documents build prerequisites (Node.js, npm)
- [ ] README explains the new tool and how it works
- [ ] Project structure section is accurate

---

### Task 5.2: Update `fastmcp.json` if needed

**File**: `fastmcp.json` (check)

Verify that `fastmcp.json` doesn't need updates for the new resource/tool. The `source.path` and `source.entrypoint` should remain the same since everything is in `server.py`.

**Acceptance Criteria**:
- [ ] `fastmcp run` still works with the updated server
- [ ] `fastmcp inspect` shows the new tool and resource

---

### Task 5.3: Add `ui/README.md` developer guide

**File**: `ui/README.md` (create)

Brief developer guide:
- How to run the UI in development mode (`npm run dev`)
- How to build for production (`npm run build`)
- Architecture of the React app
- How to add new question types

**Acceptance Criteria**:
- [ ] Developer can understand and modify the UI from the README alone

---

## File Change Summary

| File | Action | Phase |
|------|--------|-------|
| `server.py` | Modify — add `ask_questions`, `submit_answers`, `mcp_app_resource` | 1 |
| `ui/package.json` | Create | 2 |
| `ui/vite.config.ts` | Create | 2 |
| `ui/tsconfig.json` | Create | 2 |
| `ui/index.html` | Create | 2 |
| `ui/src/main.tsx` | Create | 2 |
| `ui/src/App.tsx` | Create | 2 |
| `ui/src/types.ts` | Create | 2 |
| `ui/src/components/QuestionPager.tsx` | Create — main pager/wizard component (was QuestionForm) | 2 |
| `ui/src/components/PagerControls.tsx` | Create — navigation arrows + page indicator | 2 |
| `ui/src/components/SingleSelectPage.tsx` | Create — radio buttons page (was SingleSelect) | 2 |
| `ui/src/components/MultiSelectPage.tsx` | Create — checkboxes page (was MultiSelect) | 2 |
| `ui/src/components/TextInputPage.tsx` | Create — textarea page (was TextInput) | 2 |
| `ui/src/components/Markdown.tsx` | Create — full markdown rendering with react-markdown + rehype-highlight (highlight.js) | 2 |
| `ui/src/styles/app.css` | Create (imports `highlight.js/styles/vs2015.css`) | 2 |
| `Makefile` | Modify — add `build-ui`, `clean-ui`, `test-ui` targets | 3 |
| `scripts/build.sh` | Modify — add UI build step | 3 |
| `scripts/test.sh` | Modify — add UI typecheck step | 3 |
| `pyproject.toml` | Modify — include `dist/` in wheel | 3 |
| `.gitignore` | Create/Modify — add `dist/`, `ui/node_modules/` | 3 |
| `tests/test_server.py` | Modify — add tests for new tools/resource | 4 |
| `README.md` | Modify — document MCP Apps support | 5 |
| `ui/README.md` | Create — developer guide | 5 |
| `fastmcp.json` | Verify (likely no change) | 5 |

---

## Risks & Mitigations

| # | Risk | Impact | Likelihood | Mitigation |
|---|------|--------|------------|------------|
| 1 | **FastMCP 3.0 `AppConfig` API changes** | Tool registration breaks on update | Low | FastMCP 3.0 is stable and documented. Pin `fastmcp>=3.0.0,<4.0.0`. The `app=AppConfig(...)` API is the official way. |
| 2 | **`@modelcontextprotocol/ext-apps` SDK API differs from examples** | App bootstrap code won't work | Medium | Pin SDK version. Check actual exports (`useApp`, `ontoolresult`, `callServerTool`). The SDK is new and may change. |
| 3 | **Host doesn't support `app.callServerTool()`** | Can't send answers back via companion tool | Medium | Fallback: use `app.updateContext()` or `app.sendMessage()` instead. Test in target hosts early. Use `ctx.client_supports_extension(UI_EXTENSION_ID)` for runtime detection. |
| 4 | **Single HTML file too large** | Slow resource loading | Low | React 19 + react-markdown + highlight.js (subset of languages) + minimal CSS should be < 400KB. Monitor bundle size. Only import needed highlight.js languages to avoid bundling all 190+ grammars. Consider Preact if needed. |
| 5 | **`ui://` scheme not supported by host** | Resource fetch fails | Low | FastMCP 3.0 auto-serves `ui://` with correct MIME type. Use `ctx.client_supports_extension(UI_EXTENSION_ID)` to detect and provide plain-text fallback. |
| 6 | **`visibility=["app"]` not respected by host** | `submit_answers` visible to LLM | Low | This is a MCP Apps spec feature. Older hosts may ignore it. Not harmful — just suboptimal UX. |
| 7 | **Node.js build dependency** | Developers without Node.js can't build | Low | Document prerequisite clearly. Consider pre-building and committing `dist/mcp-app.html` for ease of use. |

---

## Open Questions

1. **Exact `@modelcontextprotocol/ext-apps` API surface**: The SDK is new. Need to verify `useApp`, `ontoolresult`, `callServerTool` exist as documented. Check npm package before starting Phase 2.

2. ~~**MIME type for UI resources**~~: **Resolved** — FastMCP 3.0 auto-serves `ui://` resources with `text/html;profile=mcp-app`. No manual configuration needed.

3. ~~**FastMCP `meta` field behavior**~~: **Resolved** — FastMCP 3.0 provides `app=AppConfig(resource_uri=...)` which correctly generates `_meta.ui.resourceUri` in the MCP protocol. No raw `meta` dict needed.

4. **Pre-built HTML in repo**: Should `dist/mcp-app.html` be committed for zero-build-step usage, or gitignored for cleanliness? Current recommendation: gitignore, but reconsider if user feedback indicates friction.

---

## Implementation Order

```
Phase 1 (Server) ──► Phase 2 (UI) ──► Phase 3 (Build Pipeline)
                                              │
                                              ▼
                                       Phase 4 (Testing)
                                              │
                                              ▼
                                       Phase 5 (Docs)
```

Phases 1 and 2 can be partially parallelized:
- Task 1.1–1.3 (Python server) and Task 2.1–2.2 (project setup + types) are independent
- Task 2.3+ (App implementation) depends on understanding the `ext-apps` SDK (research in parallel with Phase 1)
- Phase 3 depends on both Phase 1 and 2 being complete
- Phase 4 can start testing Python side as soon as Phase 1 is done

---

## Estimated Task Sizing

| Task | Size | Notes |
|------|------|-------|
| 1.1 | S | Straightforward tool registration |
| 1.2 | S | Simple companion tool |
| 1.3 | S | Resource serving |
| 1.4 | S | Verification test |
| 2.1 | M | Project scaffolding + config |
| 2.2 | S | Type definitions |
| 2.3 | M | App bootstrap with SDK |
| 2.4 | L | Form components (3 types + validation + styling) |
| 2.5 | S | Entry point wiring |
| 3.1 | S | Makefile targets |
| 3.2 | S | Build script update |
| 3.3 | S | pyproject.toml update |
| 3.4 | S | .gitignore |
| 3.5 | S | package.json scripts |
| 4.1 | M | Python unit tests |
| 4.2 | S | UI typecheck in CI |
| 4.3 | M | Manual E2E testing |
| 5.1 | M | README update |
| 5.2 | S | fastmcp.json verification |
| 5.3 | S | UI developer guide |

**S** = < 30 min, **M** = 30–90 min, **L** = 90+ min
