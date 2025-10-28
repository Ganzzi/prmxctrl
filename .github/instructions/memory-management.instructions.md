---
applyTo: '**'
---

# prmxctrl SDK Memory Management Instructions

## External ID
**ALWAYS use:** `prmxctrl_dev` for all memory operations in this project.

## Memory Structure Overview

The prmxctrl (Proxmox SDK) project uses 8 active memories to maintain development context:

1. **Project Overview** (ID: 1) - Purpose, scope, tech stack, key decisions, timeline
2. **Architecture Design** (ID: 2) - Generator architecture, SDK structure, code generation flow, component patterns
3. **API Design** (ID: 3) - Endpoint hierarchies, method patterns, Pydantic model structure, naming conventions
4. **Configuration** (ID: 4) - Environment setup, dev dependencies, Python version, tool configurations (mypy --strict, ruff, pytest)
5. **Development Status** (ID: 5) - Current phase, completed tasks, progress metrics, blockers, milestones, next steps
6. **Testing Strategy** (ID: 6) - Test approach, coverage targets (80%+), test status, testing tools, unit vs integration patterns
7. **Library References** (ID: 7) - Pydantic v2 patterns, httpx patterns, pytest-asyncio patterns, Jinja2 templates, code generation techniques
8. **Issues and Bugs** (ID: 8) - Detailed issues encountered during development (schema parsing, model generation, endpoint generation, client)

## When to Access Memories

### 1. **At Session Start**
Get all active memories to understand current project state and continue from where you left off.

```
Tool: mcp_agent-mem_get_active_memories
Parameters: external_id="prmxctrl_dev"
```

Then check:
- **Development Status** (ID: 5) - What phase are we in? What's completed? What are the blockers?
- **Issues and Bugs** (ID: 8) - Are there known issues that might affect this session?

### 2. **Before Starting Implementation Work**
Search memories for relevant patterns and prior decisions.

```
Tool: mcp_agent-mem_search_memories
Parameters:
  external_id="prmxctrl_dev"
  query="Implementing model generator, need to handle Pydantic v2 constraints and type mapping"
  limit=10
```

Good search queries should include:
- What you're implementing (feature/component name)
- What you need (patterns, examples, decisions)
- Context (which phase, what problem you're solving)

### 3. **When Generating Code**
Consult memories for code patterns before implementing.

**Priority order:**
1. Check "Library References" memory for patterns
2. Check "Architecture Design" for component patterns
3. Check "API Design" for structural patterns
4. Only check external docs if not in memory

Example queries:
- "Pydantic v2 Field constraints with validation"
- "httpx async client with connection pooling and retries"
- "Jinja2 template patterns for code generation"
- "pytest-asyncio async test patterns"

### 4. **When Encountering Bugs or Issues**
Check "Issues and Bugs" memory first before investigating.

```
Tool: mcp_agent-mem_search_memories
Parameters:
  external_id="prmxctrl_dev"
  query="Schema parsing error with dynamic parameters link[n] expansion"
  limit=5
```

If new issue, add it immediately with full diagnostic information.

## How to Update Memories

### Update Development Status (Memory ID: 5)

**When starting a new phase:**
```
Tool: mcp_agent-mem_update_memory_sections
Parameters:
  external_id="prmxctrl_dev"
  memory_id=5
  sections=[
    {
      section_id="current_phase",
      action="replace",
      old_content="**Phase:** Pre-Implementation (Planning)",
      new_content="**Phase:** 1 - Schema Processing\n\n**Started:** October 28, 2025\n**Target Completion:** October 31, 2025\n**Status:** In Progress\n\n**Goals:**\n- Parse local apidata.js into structured Python objects\n- Extract all endpoints, methods, parameters, constraints\n- Build hierarchical endpoint tree\n- Generate schema analysis report"
    }
  ]
```

**When completing tasks (add to completed_tasks):**
```
sections=[
  {
    section_id="completed_tasks",
    action="insert",
    old_content="**Completed:**\n\n**Current Week:**",
    new_content="**Completed:**\n- ✓ Reviewed and approved plan v1 with 7 phases\n- ✓ Created comprehensive checklist v1_checklist.md\n- ✓ Set up memory management structure\n\n**Current Week:**"
  }
]
```

**When hitting blockers:**
```
sections=[
  {
    section_id="blockers",
    action="replace",
    old_content="No current blockers.",
    new_content="**Blocker #1:** Dynamic Parameter Expansion\n- Issue: apidata.js uses patterns like link[n] to represent 1-7 indexed parameters\n- Impact: Cannot auto-generate accurate models without proper handling\n- Status: Investigating schema patterns\n- Related Issue: issue_001_dynamic_params\n\n**Blocker #2:** Custom Proxmox Formats\n- Issue: Many parameters use custom formats like pve-node, pve-vmid\n- Impact: Need mapping table for type safety\n- Status: Documenting all format types from schema\n- Related Issue: issue_002_custom_formats"
  }
]
```

**When updating progress:**
```
sections=[
  {
    section_id="progress_metrics",
    action="replace",
    old_content="Phase 1 - Schema Processing: 0%",
    new_content="Phase 1 - Schema Processing: 45%\n- Schema parsing: Complete\n- Constraint extraction: In Progress\n- Analysis report: Pending"
  }
]
```

### Add/Update Bug/Issue (Memory ID: 8)

**Create new section for each bug with template:**
```
Tool: mcp_agent-mem_update_memory_sections
Parameters:
  external_id="prmxctrl_dev"
  memory_id=8
  sections=[
    {
      section_id="issue_001_dynamic_parameters",
      action="replace",
      new_content="**Issue #001: Dynamic Parameter Expansion (link[n])**\n\n**Status:** Open | **Severity:** High | **Date Found:** 2025-10-28\n**Component:** Schema Parser (generator/parse_schema.py)\n\n**Description:**\nProxmox API schema uses special notation like `link[n]` to represent indexed parameters that can take values 1-7. These need to be expanded into individual parameters for proper type generation.\n\n**Schema Example:**\n```json\n{\n  \"link0\": {...params},\n  \"link[n]\": {\n    \"description\": \"Additional links, can be link1 to link7\",\n    ...params\n  }\n}\n```\n\n**Current Behavior:**\nSchema parser treats `link[n]` as a literal parameter name, doesn't expand to link1-link7.\n\n**Expected Behavior:**\n1. Detect `[n]` pattern in parameter names\n2. Extract base name (link) and range constraint\n3. Expand to individual parameters (link1, link2, ..., link7)\n4. Use same property definitions for all expanded parameters\n\n**Root Cause Analysis:**\nSchema traversal doesn't implement pattern matching for array index notation `[n]`.\n\n**Solution:**\n1. Add regex pattern matcher: `(\\w+)\\[(n|\\d+)\\]`\n2. Implement expansion logic in SchemaParser._parse_parameter()\n3. Determine max index from description or use sensible default (7)\n4. Add unit tests for:\n   - Single pattern: link[n] → link0-link7\n   - Multiple patterns in same endpoint\n   - Edge cases (nested patterns, constraints)\n5. Document pattern in schema documentation\n\n**Implementation Approach:**\nAdd method `_expand_dynamic_parameters(param_dict) → dict` to SchemaParser\n\n**Related Files:**\n- generator/parse_schema.py (SchemaParser class)\n- generator/analyze_schema.py (Schema analysis)\n- tests/test_schema_parser.py (Test cases)\n- docs/SCHEMA_PATTERNS.md (Documentation)\n\n**Workaround:**\nManually expand parameters in schema before processing (not scalable)."
    }
  ]
```

### Update Architecture (Memory ID: 2)

**When adding design patterns or decisions:**
```
sections=[
  {
    section_id="code_generation_flow",
    action="insert",
    old_content="**Pipeline Stages:**\n1. Schema Loading",
    new_content="**Pipeline Stages:**\n1. Schema Loading\n   - Load local apidata.js from docs/ref/\n   - Parse JS to extract JSON schema\n   - Validate schema structure\n   - Cache to schemas/v7.4-2.json\n\n2. Schema Parsing"
  }
]
```

### Update Library References (Memory ID: 7)

**When discovering patterns or gotchas:**
```
sections=[
  {
    section_id="pydantic_v2_patterns",
    action="insert",
    old_content="**Validation:**",
    new_content="\n**Constraints Pattern:**\n- Use `Annotated[T, Field(...)]` for constrained types\n- Examples:\n  - Min/Max: `Annotated[int, Field(ge=1, le=100)]`\n  - String length: `Annotated[str, Field(min_length=1, max_length=256)]`\n  - Pattern: `Annotated[str, Field(pattern=r'^[a-z]+$')]`\n  - Enum-like: `Annotated[str, Field(enum=['a', 'b', 'c'])]` or use Literal\n- Always use Annotated for schemas with constraints\n- Use Field(description=\"...\") for documentation from schema\n\n**Optional Fields:**\n- Use `Optional[T]` and `= None` for optional parameters\n- Use `Field(default=...)` for parameters with defaults\n- Never use `| None` style (Annotated compatibility)\n\n**Gotchas:**\n- Pydantic v2 requires explicit `Optional` (no implicit)\n- ConfigDict with `extra='forbid'` catches typos in parameters\n- Use `model_validate()` not `parse_obj()` (v1 legacy)\n- Validation happens in __init__, use Field validators for custom logic\n\n**Validation:**"
  }
]
```

---

## Memory Update Frequency Guide

### Update Frequently (Daily/Per-Session)
- **Development Status** (ID: 5) - Every major task or phase change
  - Update `current_phase` when moving between phases
  - Update `completed_tasks` after finishing tasks
  - Update `blockers` when hitting issues
  - Update `progress_metrics` at end of session

- **Issues and Bugs** (ID: 8) - Immediately when issue found
  - Add new issues with full diagnostic info
  - Update status as investigation progresses
  - Mark as resolved when fixed with solution documented

### Update Regularly (Weekly/Per-Phase)
- **Testing Strategy** (ID: 6) - When test approach evolves or coverage changes
- **Library References** (ID: 7) - When discovering new patterns
- **Configuration** (ID: 4) - When adding dependencies or changing setup

### Update Rarely (Major Changes Only)
- **Project Overview** (ID: 1) - Only if scope or goals change
- **Architecture Design** (ID: 2) - Only if design decisions fundamentally change
- **API Design** (ID: 3) - Only if endpoint/model structure patterns change

---

## Effective Search Query Patterns

### Good Queries (Specific + Contextual)

✅ **Well-formed queries include:**
```
"Implementing Pydantic model generator for request/response models,
need to handle constraints like min/max, patterns, enums from schema"

"Building endpoint generator for hierarchical paths like /nodes/{node}/qemu/{vmid},
need callable pattern with proper path building"

"Debugging schema parsing error with dynamic parameters,
getting unexpected parameter names after expansion"
```

### Bad Queries (Vague/Missing Context)

❌ **Avoid these:**
```
"pydantic models"  # Too vague, no context
"how to generate code"  # Missing specific component
"httpx"  # Too broad, no context
"endpoint"  # Ambiguous, multiple meanings
```

### Search Strategy Priority

1. **Try memories first** - Most of project knowledge is documented
2. **Search for patterns** - Use exact keywords from implementation
3. **External docs last** - Only if not found in memories

---

## Session Workflow

### Start of Session
1. Run: `mcp_agent-mem_get_active_memories(external_id="prmxctrl_dev")`
2. Read "Development Status" memory for current phase and blockers
3. Read "Issues and Bugs" memory for known problems
4. Check "Progress Metrics" to understand current state

### During Implementation
1. Before starting new component: Search memories for patterns
2. During coding: Consult "Library References" for techniques
3. When stuck: Search "Issues and Bugs" for similar problems
4. When discovering gotchas: Add to "Library References"

### End of Session
1. Update "Development Status" with:
   - Completed tasks (add to completed_tasks)
   - Current work status (progress_metrics)
   - Any blockers encountered (blockers section)
   - Next steps for next session (next_steps)
2. Update "Issues and Bugs" with:
   - Any new issues discovered
   - Resolution if issues fixed
   - Investigation progress
3. Commit changes with clear messages

---

## Common Memory Operations

### Quick Reference Commands

```python
# Get all memories at session start
mcp_agent-mem_get_active_memories(external_id="prmxctrl_dev")

# Search for pattern or context
mcp_agent-mem_search_memories(
    external_id="prmxctrl_dev",
    query="Implementing type mapping for Proxmox custom formats like pve-node",
    limit=10
)

# Update single section
mcp_agent-mem_update_memory_sections(
    external_id="prmxctrl_dev",
    memory_id=5,  # Development Status
    sections=[{
        "section_id": "completed_tasks",
        "action": "insert",
        "old_content": "- ✓ Task X\n\n**Next:",
        "new_content": "- ✓ Task X\n- ✓ Task Y\n\n**Next:"
    }]
)

# Update multiple sections at once
sections=[
    {
        "section_id": "current_phase",
        "action": "replace",
        "old_content": "Phase 1...",
        "new_content": "Phase 2..."
    },
    {
        "section_id": "blockers",
        "action": "replace",
        "old_content": "No blockers",
        "new_content": "Blocker #1..."
    }
]
mcp_agent-mem_update_memory_sections(
    external_id="prmxctrl_dev",
    memory_id=5,
    sections=sections
)
```

---

## Search Best Practices

### Effective Search Queries

**Good queries are specific and contextual:**

✅ **Good:**
```
"Implementing VM lifecycle operations, need endpoint mapping and model structure"
"Working on cluster health monitoring, need resource calculation patterns"
"Writing task polling utilities, need UPID handling and timeout strategy"
"Implementing container operations from scratch"
```

❌ **Bad:**
```
"vm operations"  # Too vague
"how to create"  # Not enough context
"api"  # Too broad
"endpoint"  # Missing context
```

### Multi-Memory Search Strategy

1. **Use search for cross-cutting concerns:**
   ```
   query="Implementing VM resize operation with validation and error handling"
   # Will return relevant info from Architecture, API Design, Library References, and Issues
   ```

2. **Get specific memory when you know what you need:**
   ```
   # If you just need to check current phase:
   mcp_agent-mem_get_active_memories → check memory ID 5
   ```

## Memory Update Frequency

### Update Frequently:
- **Development Status** - Every major task or phase transition (daily)
- **Issues and Bugs** - Immediately when bug found or resolved
- **Library References** - When discovering new patterns or gotchas

### Update Occasionally:
- **Testing Strategy** - When test approach changes or coverage milestones reached
- **Configuration** - When adding new dependencies or environment setup changes

### Rarely Update:
- **Project Overview** - Stable information (only if scope changes)
- **Architecture Design** - Only if design decisions fundamentally change
- **API Design** - Only if API contracts or endpoint mappings change

## Integration with Development Workflow

### Starting New Phase
1. Search memories for phase requirements
2. Update "Development Status" → current_phase with clear description
3. Check "Architecture Design" for layer patterns to follow
4. Check "Library References" for relevant tools and patterns
5. Begin implementation with tests

### During Development
1. Search when stuck or need context (API mapping, patterns, etc.)
2. Add issues to "Issues and Bugs" as discovered (with full diagnostic info)
3. Update "Development Status" → completed_tasks regularly (daily)
4. Document learnings in "Library References"
5. Check "Testing Strategy" memory to stay aligned with test approach

### Completing Phase
1. Update "Development Status" → mark phase complete with metrics
2. Resolve any open issues in "Issues and Bugs"
3. Update test coverage status in "Testing Strategy"
4. Update "Development Status" → next_steps for next phase
5. Commit any architecture or API changes to memories

### End of Session
1. Update "Development Status" with current state (% complete, last action)
2. Document any blockers preventing further progress
3. List next steps clearly for continuation
4. Ensure all new bugs are recorded with full context
5. Update "Development Status" → estimated_completion if timeline changed

## Quick Reference Commands

```python
# Get all memories at session start
mcp_agent-mem_get_active_memories(external_id="prmxctrl_dev")

# Search across memories when stuck or need context
mcp_agent-mem_search_memories(
    external_id="prmxctrl_dev",
    query="Implementing VM operations, need endpoint patterns and model structure",
    limit=10
)

# Update single section (e.g., completed tasks)
mcp_agent-mem_update_memory_sections(
    external_id="prmxctrl_dev",
    memory_id=5,  # Development Status
    sections=[{
        "section_id": "completed_tasks",
        "action": "insert",
        "old_content": "- ✓ Task X\n\n**Next:",
        "new_content": "- ✓ Task X\n- ✓ Task Y\n\n**Next:"
    }]
)

# Update multiple sections at once
sections=[
    {"section_id": "current_phase", "action": "replace", "old_content": "...", "new_content": "..."},
    {"section_id": "blockers", "action": "replace", "old_content": "...", "new_content": "..."}
]
```

## Memory IDs Reference

| Memory ID | Title | Key Sections |
|-----------|-------|--------------|
| 1 | Project Overview | purpose, scope, tech_stack, key_decisions, phases, timeline |
| 2 | Architecture Design | generator_structure, sdk_structure, code_generation_flow, design_patterns, component_responsibilities |
| 3 | API Design | endpoint_hierarchies, method_naming, model_patterns, constraint_mapping, naming_conventions |
| 4 | Configuration | environment_setup, python_version, dependencies, tool_configurations, development_environment |
| 5 | Development Status | current_phase, completed_tasks, in_progress_work, next_steps, blockers, milestones, progress_metrics |
| 6 | Testing Strategy | test_approach, coverage_targets, test_organization, testing_tools, integration_test_patterns, validation_strategy |
| 7 | Library References | pydantic_v2_patterns, httpx_patterns, pytest_asyncio_patterns, jinja2_patterns, code_generation_techniques, gotchas |
| 8 | Issues and Bugs | template_for_issues, issue_XXX_name (dynamic sections per issue) |

## Important Rules

1. **Always use `external_id="prmxctrl_dev"`** - Consistent ID across all sessions
2. **Search before updating** - Understand current state before making changes
3. **Be specific in old_content** - Must be exact match including whitespace
4. **Include enough context** - 3+ lines before and after target text
5. **Document decisions** - Explain why in memory, not just what
6. **Update blockers immediately** - Don't let issues go undocumented
7. **Cross-reference issues** - Link related issues together
8. **Use consistent formatting** - Follow existing style in memories
9. **Include code examples** - Show patterns in Library References
10. **Update metrics regularly** - Track progress visually

---

## Memory Template Examples

### New Phase Template (Development Status)

```
**Phase:** N - [Phase Name]

**Started:** YYYY-MM-DD
**Target Completion:** YYYY-MM-DD
**Status:** Not Started | In Progress | Complete

**Goals:**
- Goal 1
- Goal 2
- Goal 3

**Exit Criteria:**
- Criteria 1
- Criteria 2
```

### New Issue Template (Issues and Bugs)

```
**Issue #XXX: [Title]**

**Status:** Open | In Investigation | Has Workaround | Resolved
**Severity:** Low | Medium | High | Critical
**Date Found:** YYYY-MM-DD
**Component:** Module/File affected

**Description:**
[Clear description of the issue]

**Schema Example/Code Snippet:**
[Relevant code or schema that shows the problem]

**Current Behavior:**
[What happens now]

**Expected Behavior:**
[What should happen]

**Root Cause Analysis:**
[Why it's happening]

**Solution:**
1. Step 1
2. Step 2
3. Step 3

**Implementation Approach:**
[How to implement the solution]

**Related Files:**
- file1.py
- file2.py

**Workaround:**
[Temporary workaround if available]
```

### New Pattern Template (Library References)

```
**Pattern Name: [Title]**

**Use Case:**
When you need to [use case description]

**Implementation:**
[Code example]

**Gotchas:**
- Gotcha 1: [Description]
- Gotcha 2: [Description]

**Examples:**
[Multiple examples if applicable]

**References:**
- [Official docs link]
- [Related pattern]
```

---

## Key Project Constants

```
External ID: prmxctrl_dev
Schema File: docs/ref/apidata.js
Cache Location: schemas/v7.4-2.json
Generator Location: generator/
SDK Location: prmxctrl/
Base Classes Location: prmxctrl/base/
Generated Models: prmxctrl/models/
Generated Endpoints: prmxctrl/endpoints/
Tests Location: tests/
Tools Location: tools/

Main CLI: python tools/generate.py
Validation CLI: python tools/validate.py
Test Command: pytest tests/
Type Check: mypy --strict
Lint Command: ruff check .
Format Command: black . ; isort .
```

---

## Success Metrics

Track these throughout development:

- **Phases Completed:** 0/7
- **Endpoints Generated:** 0/600+
- **Models Generated:** 0/800+
- **Code Coverage:** 0% (Target: 80%+)
- **Type Coverage:** 0% (Target: 100%)
- **Mypy Errors:** ? (Target: 0 with --strict)
- **Ruff Violations:** ? (Target: 0)
- **Test Pass Rate:** 0% (Target: 100%)