# Duck MCP App UI

React-based form UI for the `ask_questions` tool, built with Vite and bundled as a single HTML file.

## Development

```bash
npm install
npm run dev      # Start Vite dev server
npm run build    # Build to ../dist/mcp-app.html
npm run typecheck # TypeScript type checking
```

## Architecture

The UI is a pager/wizard that shows one question per page:

```
App.tsx                    # MCP App bootstrap (useApp hook)
└── QuestionPager.tsx      # Main pager/wizard component
    ├── PagerControls.tsx  # Navigation (Back/Next/Submit + page indicator)
    ├── SingleSelectPage   # Radio buttons
    ├── MultiSelectPage    # Checkboxes
    └── TextInputPage      # Textarea
```

### Communication Flow

1. Host calls `ask_questions` tool → returns question config JSON
2. Host renders this UI in a sandboxed iframe
3. UI receives question config via `app.ontoolresult`
4. User fills out the form and navigates pages
5. On submit, UI calls `app.callServerTool("submit_answers", { session_id, answers })`

### Key Dependencies

- `@modelcontextprotocol/ext-apps` — MCP Apps SDK (React hooks)
- `react-markdown` + `rehype-highlight` — Markdown rendering with syntax highlighting
- `highlight.js` — Code syntax highlighting (vs2015/VS Code Dark+ theme)
- `vite-plugin-singlefile` — Bundles everything into one HTML file

## Adding New Question Types

1. Add the type to `src/types.ts` (`QuestionType` union)
2. Create a new page component in `src/components/`
3. Add a case to the `renderQuestion` switch in `QuestionPager.tsx`
4. Update the Python schema in `server.py`

## Styling

VS Code dark theme. All styles in `src/styles/app.css` using CSS custom properties. No external CSS frameworks.
