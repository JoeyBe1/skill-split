# VS Code Extension Integration Guide

Concept for a VS Code extension that integrates skill-split using Language Server Protocol (LSP).

## Overview

A VS Code extension for skill-split would provide:
- **Section Navigation**: Jump between document sections
- **Progressive Disclosure**: Load sections on-demand in side panel
- **Search Integration**: FTS5 search across all indexed files
- **Live Preview**: Show section hierarchy in explorer

## Architecture

### Extension Components

```
vscode-skill-split/
├── client/
│   ├── src/
│   │   ├── extension.ts          # Main extension entry
│   │   ├── panel.ts              # Section preview panel
│   │   ├── treeView.ts           # Section hierarchy tree
│   │   └── search.ts             # Search functionality
│   ├── package.json
│   └── tsconfig.json
├── server/
│   ├── src/
│   │   ├── server.ts             # LSP server
│   │   ├── handler.ts            # Message handling
│   │   └── skillSplit.ts         # skill-split API wrapper
│   ├── package.json
│   └── tsconfig.json
└── README.md
```

## Implementation Plan

### Phase 1: Core Extension (MVP)

**Features:**
- Parse current file on open
- Show section hierarchy in tree view
- Navigate to section by double-click
- Basic search within file

**Files to Create:**

#### package.json (Extension Manifest)

```json
{
  "name": "vscode-skill-split",
  "displayName": "skill-split Section Navigation",
  "description": "Progressive disclosure for large documentation files",
  "version": "0.1.0",
  "engines": {
    "vscode": "^1.80.0"
  },
  "categories": ["Other"],
  "activationEvents": [
    "onLanguage:markdown",
    "onLanguage:yaml"
  ],
  "main": "./client/out/extension",
  "contributes": {
    "commands": [
      {
        "command": "skillSplit.parseFile",
        "title": "skill-split: Parse Current File"
      },
      {
        "command": "skillSplit.searchSections",
        "title": "skill-split: Search Sections"
      },
      {
        "command": "skillSplit.showTree",
        "title": "skill-split: Show Section Tree"
      }
    ],
    "views": {
      "explorer": [
        {
          "id": "skillSplitTree",
          "name": "Document Sections"
        }
      ]
    },
    "configuration": {
      "title": "skill-split",
      "properties": {
        "skillSplit.databasePath": {
          "type": "string",
          "default": "~/.claude/databases/skill-split.db",
          "description": "Path to skill-split database"
        },
        "skillSplit.autoParse": {
          "type": "boolean",
          "default": true,
          "description": "Automatically parse supported files on open"
        }
      }
    }
  },
  "dependencies": {
    "vscode-languageclient": "^9.0.1",
    "better-sqlite3": "^9.0.0"
  },
  "devDependencies": {
    "@types/vscode": "^1.80.0",
    "typescript": "^5.0.0"
  }
}
```

#### extension.ts (Main Extension)

```typescript
import * as vscode from 'vscode';
import { LanguageClient, LanguageClientOptions } from 'vscode-languageclient';
import { SectionTreeProvider } from './treeView';
import { SearchPanel } from './search';

let client: LanguageClient;
let treeProvider: SectionTreeProvider;

export function activate(context: vscode.ExtensionContext) {
    // Initialize section tree view
    treeProvider = new SectionTreeProvider(context);
    vscode.window.registerTreeDataProvider(
        'skillSplitTree',
        treeProvider
    );

    // Register commands
    context.subscriptions.push(
        vscode.commands.registerCommand('skillSplit.parseFile', async () => {
            const editor = vscode.window.activeTextEditor;
            if (editor) {
                await treeProvider.parseFile(editor.document.uri.fsPath);
            }
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('skillSplit.searchSections', () => {
            SearchPanel.createOrShow(context.extensionUri);
        })
    );

    // Auto-parse on file open
    if (vscode.workspace.getConfiguration('skillSplit').get('autoParse')) {
        vscode.workspace.onDidOpenTextDocument(async (doc) => {
            if (isSupportedFile(doc)) {
                await treeProvider.parseFile(doc.uri.fsPath);
            }
        });
    }

    // Start LSP server
    startLanguageServer(context);
}

function isSupportedFile(doc: vscode.TextDocument): boolean {
    const supported = ['markdown', 'yaml', 'python', 'javascript', 'typescript'];
    return supported.includes(doc.languageId);
}

async function startLanguageServer(context: vscode.ExtensionContext) {
    const serverModule = context.asAbsolutePath(
        path.join('server', 'out', 'server.js')
    );

    const clientOptions: LanguageClientOptions = {
        documentSelector: [
            { scheme: 'file', language: 'markdown' },
            { scheme: 'file', language: 'yaml' }
        ],
    };

    client = new LanguageClient(
        'skillSplitServer',
        'skill-split Language Server',
        serverModule,
        clientOptions
    );

    await client.start();
}

export function deactivate(): Thenable<void> {
    if (!client) {
        return Promise.resolve();
    }
    return client.stop();
}
```

#### treeView.ts (Section Hierarchy)

```typescript
import * as vscode from 'vscode';
import * as path from 'path';
import Database from 'better-sqlite3';

export class SectionTreeItem extends vscode.TreeItem {
    constructor(
        public readonly id: number,
        public readonly label: string,
        public readonly level: number,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState,
        public readonly filePath: string
    ) {
        super(label, collapsibleState);
        this.tooltip = `Section ${id} (Level ${level})`;
        this.contextValue = level > 0 ? 'subsection' : 'section';
        this.iconPath = new vscode.ThemeIcon(
            level === 0 ? 'document' : 'folder'
        );
    }
}

export class SectionTreeProvider implements vscode.TreeDataProvider<SectionTreeItem> {
    private _onDidChangeTreeData = new vscode.EventEmitter<SectionTreeItem | undefined | void>();
    readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

    private db: Database.Database | undefined;
    private currentFile: string | undefined;

    constructor(private context: vscode.ExtensionContext) {
        this.connectDatabase();
    }

    private connectDatabase() {
        const dbPath = vscode.workspace
            .getConfiguration('skillSplit')
            .get<string>('databasePath');

        if (dbPath) {
            const expandedPath = dbPath.replace('~', process.env.HOME || '');
            this.db = new Database(expandedPath);
            this.db.pragma('journal_mode = WAL');
        }
    }

    async parseFile(filePath: string): Promise<void> {
        if (!this.db) {
            vscode.window.showErrorMessage('Database not connected');
            return;
        }

        // Call skill-split CLI to parse and store
        const terminal = vscode.window.createTerminal('skill-split');
        terminal.sendText(`cd "${path.dirname(filePath)}"`);
        terminal.sendText(`python -m skill_split parse "${filePath}"`);
        terminal.sendText(`python -m skill_split store "${filePath}"`);

        this.currentFile = filePath;
        this._onDidChangeTreeData.fire();
    }

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: SectionTreeItem): vscode.TreeItem {
        return element;
    }

    async getChildren(element?: SectionTreeItem): Promise<SectionTreeItem[]> {
        if (!this.db || !this.currentFile) {
            return [];
        }

        const parentId = element ? element.id : null;

        const query = `
            SELECT id, title, level
            FROM sections
            WHERE file_id = (SELECT id FROM files WHERE path = ?)
            AND parent_id IS ${parentId ? '?' : 'NULL'}
            ORDER BY order_index
        `;

        const stmt = this.db.prepare(query);
        const params = parentId
            ? [this.currentFile, parentId]
            : [this.currentFile];

        const rows = stmt.all(...params) as any[];

        return rows.map(row => new SectionTreeItem(
            row.id,
            row.title,
            row.level,
            vscode.TreeItemCollapsibleState.Collapsed,
            this.currentFile!
        ));
    }
}
```

#### search.ts (Search Panel)

```typescript
import * as vscode from 'vscode';
import * as path from 'path';
import Database from 'better-sqlite3';

export class SearchPanel {
    public static currentPanel: SearchPanel | undefined;
    private readonly _panel: vscode.WebviewPanel;
    private _disposables: vscode.Disposable[] = [];

    public static createOrShow(extensionUri: vscode.Uri) {
        const column = vscode.window.activeTextEditor
            ? vscode.window.activeTextEditor.viewColumn
            : undefined;

        if (SearchPanel.currentPanel) {
            SearchPanel.currentPanel._panel.reveal(column);
            return;
        }

        const panel = vscode.window.createWebviewPanel(
            'skillSplitSearch',
            'Search Sections',
            column || vscode.ViewColumn.One,
            {
                enableScripts: true,
                localResourceRoots: [extensionUri]
            }
        );

        SearchPanel.currentPanel = new SearchPanel(panel, extensionUri);
    }

    private constructor(panel: vscode.WebviewPanel, extensionUri: vscode.Uri) {
        this._panel = panel;

        this._panel.webview.html = this._getHtmlForWebview(extensionUri);

        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);

        this._panel.webview.onDidReceiveMessage(
            message => {
                switch (message.command) {
                    case 'search':
                        this.performSearch(message.query);
                        break;
                    case 'openSection':
                        this.openSection(message.sectionId);
                        break;
                }
            },
            null,
            this._disposables
        );
    }

    private async performSearch(query: string) {
        const dbPath = vscode.workspace
            .getConfiguration('skillSplit')
            .get<string>('databasePath');

        if (!dbPath) return;

        const expandedPath = dbPath.replace('~', process.env.HOME || '');
        const db = new Database(expandedPath);

        const searchQuery = `
            SELECT section_id, rank
            FROM sections_fts
            WHERE sections_fts MATCH ?
            ORDER BY rank
            LIMIT 50
        `;

        const stmt = db.prepare(searchQuery);
        const results = stmt.all(query) as any[];

        this._panel.webview.postMessage({
            command: 'searchResults',
            results: results
        });
    }

    private openSection(sectionId: number) {
        vscode.commands.executeCommand('skillSplit.navigateToSection', sectionId);
    }

    private _getHtmlForWebview(extensionUri: vscode.Uri): string {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Search Sections</title>
    <style>
        body {
            padding: 20px;
            font-family: var(--vscode-font-family);
        }
        .search-box {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        input {
            flex: 1;
            padding: 8px;
            background: var(--vscode-input-background);
            color: var(--vscode-input-foreground);
            border: 1px solid var(--vscode-input-border);
        }
        button {
            padding: 8px 16px;
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            cursor: pointer;
        }
        .results {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .result-item {
            padding: 10px;
            background: var(--vscode-editor-background);
            border: 1px solid var(--vscode-panel-border);
            cursor: pointer;
        }
        .result-item:hover {
            background: var(--vscode-editor-inactiveSelectionBackground);
        }
    </style>
</head>
<body>
    <div class="search-box">
        <input type="text" id="searchInput" placeholder="Search sections..." />
        <button id="searchButton">Search</button>
    </div>
    <div class="results" id="results"></div>

    <script>
        const vscode = acquireVsCodeApi();

        document.getElementById('searchButton').addEventListener('click', () => {
            const query = document.getElementById('searchInput').value;
            vscode.postMessage({ command: 'search', query });
        });

        window.addEventListener('message', event => {
            const message = event.data;
            if (message.command === 'searchResults') {
                const resultsDiv = document.getElementById('results');
                resultsDiv.innerHTML = message.results.map(r =>
                    \`<div class="result-item" onclick="vscode.postMessage({
                        command: 'openSection',
                        sectionId: \${r.section_id}
                    })">
                        Section \${r.section_id} (rank: \${r.rank})
                    </div>\`
                ).join('');
            }
        });
    </script>
</body>
</html>`;
    }

    public dispose() {
        SearchPanel.currentPanel = undefined;
        this._panel.dispose();
        while (this._disposables.length) {
            this._disposables.pop()!.dispose();
        }
    }
}
```

### Phase 2: LSP Server Integration

**Features:**
- Code actions for section navigation
- Diagnostics for section structure
- Hover information for section references
- Go to definition for section links

#### server.ts (LSP Server)

```typescript
import {
    createConnection,
    TextDocuments,
    ProposedFeatures,
    InitializeParams,
    DidChangeConfigurationNotification,
    TextDocumentSyncKind,
    InitializeResult
} from 'vscode-languageserver/node';

import {
    TextDocument
} from 'vscode-languageserver-textdocument';

import { SkillSplitHandler } from './handler';

// Create a connection for the server
const connection = createConnection(ProposedFeatures.all);

// Create a simple text document manager
const documents = new TextDocuments<TextDocument>(
    TextDocument
);

let handler: SkillSplitHandler;

connection.onInitialize((params: InitializeParams) => {
    return {
        capabilities: {
            textDocumentSync: TextDocumentSyncKind.Incremental,
            // Tell the client that this server supports code actions
            codeActionProvider: true,
            // Tell the client that this server supports hover
            hoverProvider: true,
        }
    } as InitializeResult;
});

// The content of a text document has changed
connection.onDidChangeContent(change => {
    validateSectionDocument(change.document);
});

async function validateSectionDocument(textDocument: TextDocument): Promise<void> {
    const diagnostics = [];
    const text = textDocument.getText();

    // Use skill-split parser to validate structure
    const result = await handler.validateDocument(text);

    for (const error of result.errors) {
        diagnostics.push({
            severity: 1, // Error
            range: {
                start: textDocument.positionAt(error.offset),
                end: textDocument.positionAt(error.offset + error.length)
            },
            message: error.message,
            source: 'skill-split'
        });
    }

    // Send the computed diagnostics to the client
    connection.sendDiagnostics({
        uri: textDocument.uri,
        diagnostics
    });
}

// This handler provides the initial list of the completion items
connection.onCompletion(() => {
    return [];
});

// This handler resolves additional information for the item selected in the completion list
connection.onCompletionResolve(() => {
    return {};
});

// Make the text document manager listen on the connection for open, change and close text document events
documents.listen(connection);

// Listen on the connection
connection.listen();

// Initialize skill-split handler
handler = new SkillSplitHandler();
```

### Phase 3: Advanced Features

**Features:**
- Section composition wizard
- Batch file indexing
- Sync with Supabase
- Semantic search integration

## Installation

### For Users

1. Build the extension:
```bash
cd vscode-skill-split
npm install
npm run compile
```

2. Install in VS Code:
```bash
code --install-extension vscode-skill-split-0.1.0.vsix
```

3. Configure settings:
```json
{
  "skillSplit.databasePath": "~/.claude/databases/skill-split.db",
  "skillSplit.autoParse": true
}
```

### For Developers

1. Fork and clone repository
2. Install dependencies:
```bash
npm install
```

3. Open in VS Code with debugging:
```bash
code .
# Press F5 to launch Extension Development Host
```

## Usage

### Basic Navigation

1. Open a markdown file
2. View "Document Sections" in Explorer
3. Double-click sections to navigate
4. Use search to find content

### Keyboard Shortcuts

```json
{
  "key": "ctrl+shift+s",
  "command": "skillSplit.searchSections"
},
{
  "key": "ctrl+shift+t",
  "command": "skillSplit.showTree"
}
```

## API Reference

### Commands

- `skillSplit.parseFile` - Parse current file
- `skillSplit.searchSections` - Open search panel
- `skillSplit.showTree` - Show section tree
- `skillSplit.navigateToSection` - Jump to section

### Configuration

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `databasePath` | string | `~/.claude/databases/skill-split.db` | Database location |
| `autoParse` | boolean | `true` | Auto-parse files on open |
| `maxSections` | number | `1000` | Max sections to display |

## Troubleshooting

### Database Not Found

```typescript
// Check database path configuration
const config = vscode.workspace.getConfiguration('skillSplit');
const dbPath = config.get<string>('databasePath');
console.log('Database path:', dbPath);
```

### Tree View Empty

1. Ensure file is parsed: Run `skillSplit: Parse Current File` command
2. Check database contains sections
3. Verify file is supported (markdown, yaml, etc.)

## Future Enhancements

- **Remote Database**: Connect to Supabase for shared sections
- **Collaboration**: Share section selections with team
- **AI Integration**: Use semantic search with embeddings
- **WebAssembly**: Compile skill-split to WASM for browser use

## Contributing

Contributions welcome! Please see CONTRIBUTING.md for guidelines.

## License

MIT License - see LICENSE for details

---

*Last Updated: 2025-02-10*
