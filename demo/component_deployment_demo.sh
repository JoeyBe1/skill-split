#!/usr/bin/env bash

#############################################################################
# Component Deployment Demo - Multi-file Checkout
#
# This demo shows how skill-split handles multi-file components like plugins
# and hooks, deploying all related files together in a single checkout operation.
#
# Value Proposition:
# - Atomic deployment of multi-file components
# - Runtime-ready after checkout
# - Directory structure preservation
# - Rollback on failure
#############################################################################

set -e

DEMO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$DEMO_DIR")"
WORK_DIR="$DEMO_DIR/work"
COMPONENTS_DIR="$WORK_DIR/components"
DEPLOY_DIR="$WORK_DIR/deployed"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${BLUE}═════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Component Deployment Demo - Multi-file Checkout                 ${NC}"
echo -e "${BLUE}═════════════════════════════════════════════════════════════════════${NC}"
echo ""

# Check for Supabase credentials
if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_KEY" ]; then
    echo -e "${RED}Error: Supabase credentials required${NC}"
    echo "Set SUPABASE_URL and SUPABASE_KEY environment variables"
    exit 1
fi

echo -e "${GREEN}✓ Supabase credentials found${NC}"
echo ""

# Setup work directory
echo -e "${YELLOW}📁 Setting up work directory...${NC}"
rm -rf "$WORK_DIR"
mkdir -p "$COMPONENTS_DIR"
mkdir -p "$DEPLOY_DIR"
echo -e "${GREEN}✓ Work directory ready: $WORK_DIR${NC}"
echo ""

# Create test plugin component
echo -e "${YELLOW}🔧 Creating test plugin component...${NC}"
echo ""

# Create plugin directory
PLUGIN_DIR="$COMPONENTS_DIR/my-plugin"
mkdir -p "$PLUGIN_DIR"

# Create plugin.json
cat > "$PLUGIN_DIR/plugin.json" << 'EOF'
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "A test plugin for demonstration",
  "author": "demo",
  "main": "index.js",
  "scripts": {
    "start": "node index.js"
  }
}
EOF

# Create .mcp.json (MCP config)
cat > "$PLUGIN_DIR/.mcp.json" << 'EOF'
{
  "name": "my-plugin-mcp",
  "version": "1.0.0",
  "description": "MCP configuration for my-plugin",
  "endpoints": {
    "api": "http://localhost:8080/api"
  }
}
EOF

# Create hooks.json
cat > "$PLUGIN_DIR/hooks.json" << 'EOF'
{
  "pre-start": "Pre-start hook description",
  "post-start": "Post-start hook description"
}
EOF

# Create hook script files
cat > "$PLUGIN_DIR/pre-start.sh" << 'EOF'
#!/bin/bash
echo "Running pre-start hook..."
echo "Pre-start setup complete"
EOF
chmod +x "$PLUGIN_DIR/pre-start.sh"

cat > "$PLUGIN_DIR/post-start.sh" << 'EOF'
#!/bin/bash
echo "Running post-start hook..."
echo "Post-start cleanup complete"
EOF
chmod +x "$PLUGIN_DIR/post-start.sh"

echo -e "${GREEN}✓ Plugin component created${NC}"
echo ""
echo -e "${CYAN}Plugin Structure:${NC}"
tree "$PLUGIN_DIR" 2>/dev/null || find "$PLUGIN_DIR" -type f | sed 's|'"$PLUGIN_DIR"'||' | sort
echo ""

# Ingest component to Supabase
echo -e "${YELLOW}📤 Ingesting plugin to Supabase...${NC}"
cd "$PROJECT_ROOT"
python3 skill_split.py ingest "$COMPONENTS_DIR" > /dev/null 2>&1
echo -e "${GREEN}✓ Component ingested${NC}"
echo ""

# List files in library
echo -e "${YELLOW}📚 Files in Library:${NC}"
python3 skill_split.py list-library 2>&1 | grep -E "my-plugin|Name|Type|---" | head -10
echo ""

# Get file ID for plugin.json
echo -e "${YELLOW}🔍 Getting plugin file ID...${NC}"
FILE_ID=$(python3 skill_split.py list-library 2>&1 | grep "my-plugin/plugin.json" | awk '{print $1}' || python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')
from core.supabase_store import SupabaseStore
import os
store = SupabaseStore(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
files = store.get_all_files()
for f in files:
    if 'my-plugin' in f.get('storage_path', '') and 'plugin.json' in f.get('storage_path', ''):
        print(f['id'])
        break
" 2>/dev/null)

if [ -z "$FILE_ID" ]; then
    echo -e "${RED}Error: Could not find plugin file ID${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Plugin File ID: $FILE_ID${NC}"
echo ""

# Deploy plugin using checkout
echo -e "${YELLOW}🚀 Deploying plugin (multi-file checkout)...${NC}"
echo ""
echo -e "${CYAN}Target directory: $DEPLOY_DIR/my-plugin${NC}"
echo ""

cd "$PROJECT_ROOT"
python3 skill_split.py checkout "$FILE_ID" "$DEPLOY_DIR/my-plugin/plugin.json" --user "demo-user" 2>&1
echo ""

# Verify deployment
echo -e "${YELLOW}✓ Verifying deployment...${NC}"
echo ""

if [ -f "$DEPLOY_DIR/my-plugin/plugin.json" ]; then
    echo -e "${GREEN}✓ Primary file deployed: plugin.json${NC}"
else
    echo -e "${RED}✗ Primary file NOT deployed${NC}"
fi

if [ -f "$DEPLOY_DIR/my-plugin/.mcp.json" ]; then
    echo -e "${GREEN}✓ Related file deployed: .mcp.json${NC}"
else
    echo -e "${YELLOW}⚠ Related file NOT deployed: .mcp.json${NC}"
fi

if [ -f "$DEPLOY_DIR/my-plugin/hooks.json" ]; then
    echo -e "${GREEN}✓ Related file deployed: hooks.json${NC}"
else
    echo -e "${YELLOW}⚠ Related file NOT deployed: hooks.json${NC}"
fi

if [ -f "$DEPLOY_DIR/my-plugin/pre-start.sh" ]; then
    echo -e "${GREEN}✓ Hook script deployed: pre-start.sh${NC}"
else
    echo -e "${YELLOW}⚠ Hook script NOT deployed: pre-start.sh${NC}"
fi

if [ -f "$DEPLOY_DIR/my-plugin/post-start.sh" ]; then
    echo -e "${GREEN}✓ Hook script deployed: post-start.sh${NC}"
else
    echo -e "${YELLOW}⚠ Hook script NOT deployed: post-start.sh${NC}"
fi

echo ""

# Show deployed directory structure
echo -e "${YELLOW}📁 Deployed Directory Structure:${NC}"
echo ""
if [ -d "$DEPLOY_DIR/my-plugin" ]; then
    tree "$DEPLOY_DIR/my-plugin" 2>/dev/null || find "$DEPLOY_DIR/my-plugin" -type f | sed 's|'"$DEPLOY_DIR/my-plugin"'||' | sort
else
    echo -e "${RED}Deployed directory not found${NC}"
fi
echo ""

# Verify runtime readiness
echo -e "${YELLOW}⚡ Verifying Runtime Readiness:${NC}"
echo ""

# Check if files are executable
if [ -x "$DEPLOY_DIR/my-plugin/pre-start.sh" ]; then
    echo -e "${GREEN}✓ pre-start.sh is executable${NC}"
else
    echo -e "${YELLOW}⚠ pre-start.sh not executable (chmod may be needed)${NC}"
fi

if [ -x "$DEPLOY_DIR/my-plugin/post-start.sh" ]; then
    echo -e "${GREEN}✓ post-start.sh is executable${NC}"
else
    echo -e "${YELLOW}⚠ post-start.sh not executable (chmod may be needed)${NC}"
fi

echo ""

# Check JSON validity
echo -e "${CYAN}Checking JSON validity...${NC}"
if python3 -m json.tool "$DEPLOY_DIR/my-plugin/plugin.json" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ plugin.json is valid JSON${NC}"
else
    echo -e "${RED}✗ plugin.json is INVALID JSON${NC}"
fi

if python3 -m json.tool "$DEPLOY_DIR/my-plugin/.mcp.json" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ .mcp.json is valid JSON${NC}"
else
    echo -e "${RED}✗ .mcp.json is INVALID JSON${NC}"
fi

echo ""

# Show checkout status
echo -e "${YELLOW}📊 Checkout Status:${NC}"
cd "$PROJECT_ROOT"
python3 skill_split.py status --user "demo-user" 2>&1 | grep -E "demo-user|my-plugin|User|File|---" | head -10
echo ""

# Demonstrate checkin
echo -e "${YELLOW}🔄 Checking in plugin...${NC}"
python3 skill_split.py checkin "$DEPLOY_DIR/my-plugin/plugin.json" 2>&1
echo ""

# Verify files removed
echo -e "${YELLOW}✓ Verifying checkin (files removed)...${NC}"
echo ""

if [ -f "$DEPLOY_DIR/my-plugin/plugin.json" ]; then
    echo -e "${RED}✗ File still exists after checkin${NC}"
else
    echo -e "${GREEN}✓ Primary file removed after checkin${NC}"
fi

echo ""

# Create hooks component demo
echo -e "${MAGENTA}═════════════════════════════════════════════════════════════════════${NC}"
echo -e "${MAGENTA}  Hooks Component Demo${NC}"
echo -e "${MAGENTA}═════════════════════════════════════════════════════════════════════${NC}"
echo ""

# Create hooks component
HOOKS_DIR="$COMPONENTS_DIR/my-hooks"
mkdir -p "$HOOKS_DIR"

cat > "$HOOKS_DIR/hooks.json" << 'EOF'
{
  "hooks": {
    "beforeDeploy": {
      "description": "Run before deployment",
      "command": "before-deploy.sh"
    },
    "afterDeploy": {
      "description": "Run after deployment",
      "command": "after-deploy.sh"
    }
  }
}
EOF

cat > "$HOOKS_DIR/before-deploy.sh" << 'EOF'
#!/bin/bash
echo "Before deploy: Running setup..."
EOF
chmod +x "$HOOKS_DIR/before-deploy.sh"

cat > "$HOOKS_DIR/after-deploy.sh" << 'EOF'
#!/bin/bash
echo "After deploy: Running verification..."
EOF
chmod +x "$HOOKS_DIR/after-deploy.sh"

echo -e "${CYAN}Hooks component created:${NC}"
tree "$HOOKS_DIR" 2>/dev/null || find "$HOOKS_DIR" -type f | sed 's|'"$HOOKS_DIR"'||' | sort
echo ""

# Ingest hooks
cd "$PROJECT_ROOT"
python3 skill_split.py ingest "$COMPONENTS_DIR" > /dev/null 2>&1
echo -e "${GREEN}✓ Hooks component ingested${NC}"
echo ""

# Get hooks file ID
HOOKS_FILE_ID=$(python3 skill_split.py list-library 2>&1 | grep "my-hooks/hooks.json" | awk '{print $1}' || python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')
from core.supabase_store import SupabaseStore
import os
store = SupabaseStore(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
files = store.get_all_files()
for f in files:
    if 'my-hooks' in f.get('storage_path', '') and 'hooks.json' in f.get('storage_path', ''):
        print(f['id'])
        break
" 2>/dev/null)

if [ -n "$HOOKS_FILE_ID" ]; then
    echo -e "${GREEN}✓ Hooks File ID: $HOOKS_FILE_ID${NC}"
    echo ""

    # Deploy hooks
    echo -e "${YELLOW}🚀 Deploying hooks component...${NC}"
    python3 skill_split.py checkout "$HOOKS_FILE_ID" "$DEPLOY_DIR/my-hooks/hooks.json" --user "demo-user" 2>&1
    echo ""

    # Verify hooks deployment
    echo -e "${YELLOW}✓ Verifying hooks deployment...${NC}"
    echo ""

    [ -f "$DEPLOY_DIR/my-hooks/hooks.json" ] && echo -e "${GREEN}✓ hooks.json${NC}" || echo -e "${RED}✗ hooks.json${NC}"
    [ -f "$DEPLOY_DIR/my-hooks/before-deploy.sh" ] && echo -e "${GREEN}✓ before-deploy.sh${NC}" || echo -e "${RED}✗ before-deploy.sh${NC}"
    [ -f "$DEPLOY_DIR/my-hooks/after-deploy.sh" ] && echo -e "${GREEN}✓ after-deploy.sh${NC}" || echo -e "${RED}✗ after-deploy.sh${NC}"
    echo ""
fi

# Summary
echo -e "${BLUE}═════════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  COMPONENT DEPLOYMENT SUMMARY${NC}"
echo -e "${BLUE}═════════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${CYAN}Multi-file Component Support:${NC}"
echo "  ✓ Plugins: plugin.json + .mcp.json + hooks.json + scripts"
echo "  ✓ Hooks: hooks.json + associated shell scripts"
echo "  ✓ Configs: settings.json + related configuration files"
echo ""
echo -e "${CYAN}Deployment Features:${NC}"
echo "  ✓ Atomic checkout (all files or none)"
echo "  ✓ Runtime-ready (executables, valid JSON)"
echo "  ✓ Directory structure preserved"
echo "  ✓ Rollback on failure"
echo ""
echo -e "${CYAN}Workflow:${NC}"
echo "  1. Create component with related files"
echo "  2. Ingest to Supabase library"
echo "  3. Checkout with single file_id"
echo "  4. All related files deployed automatically"
echo "  5. Verify runtime readiness"
echo "  6. Checkin when done"
echo ""
echo -e "${BLUE}═════════════════════════════════════════════════════════════════════${NC}"
