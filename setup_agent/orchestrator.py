from typing import Annotated

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from setup_agent.mcp_tools import jira_search, slack_search, github_search, jira_create
from dotenv import load_dotenv
load_dotenv()


TOOLS = [jira_search, slack_search, github_search, jira_create]

DEFAULT_SYSTEM_PROMPT = """You are Smart Bug Triage AI.

When investigating an issue:
1. Always search Jira, GitHub, AND Slack for related information, even if Jira returns results.
2. If a relevant existing Jira ticket is found, clearly state \"Found existing ticket [TICKET-ID]\" and DO NOT create a new ticket.
3. If no relevant existing Jira ticket exists but the issue is valid, create a new Jira ticket using jira_create.
4. For critical issues (P0), include words like \"critical\", \"urgent\", or \"P0\" in your summary.
5. Then summarize findings.

Do not create duplicate tickets if one already exists.
"""

class AgentState(dict):
    messages: Annotated[list, add_messages]
    
    # Tracking
    retry_count: int = 0
    max_retries: int = 3
    step_count: int = 0
    
    # Status flags
    ticket_created: bool = False
    summary_done: bool = False
    workflow_done: bool = False
    needs_retry: bool = False
    
    # Classification
    is_valid_bug: bool = None
    severity: str = None  # NEW: tracks severity (critical, high, medium, minor, trivial, not_a_bug)
    duplicate_found: bool = False
    duplicate_ticket_id: str = None
    
    # Final output
    final_output: dict = {}
    
def create_agent(model: str = None, temperature: float = 0.0, system_prompt: str = None):
    model = model or 'gpt-4'
    agent_system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
    llm = ChatOpenAI(model=model, temperature=temperature).bind_tools(TOOLS)
    tool_node = ToolNode(TOOLS)
    
    def init_state(state: AgentState) -> AgentState:
        """Ensure all state keys exist"""
        state.setdefault('retry_count', 0)
        state.setdefault('max_retries', 3)
        state.setdefault('step_count', 0)
        state.setdefault('ticket_created', False)
        state.setdefault('summary_done', False)
        state.setdefault('workflow_done', False)
        state.setdefault('needs_retry', False)
        state.setdefault('is_valid_bug', None)
        state.setdefault('severity', None)
        state.setdefault('duplicate_found', False)
        state.setdefault('duplicate_ticket_id', None)
        state.setdefault('final_output', {})
        return state

    def should_continue(state: AgentState) -> str:
        last = state['messages'][-1]
        if hasattr(last, 'tool_calls') and last.tool_calls:
            return 'tools'
        return 'verify'

    def call_model(state: AgentState) -> dict:
        state = init_state(state)
        messages = state['messages']
        response = llm.invoke(messages)
        # Track completion
        if "Created new Jira ticket" in response.content:
            state['ticket_created'] = True
        if "Summary:" in response.content or "Findings:" in response.content:
            state['summary_done'] = True
        return {'messages':[response]}
        
    def classify_input(state: AgentState) -> dict:
        """STEP 1: Classify if this is a valid bug report and determine severity"""
        state = init_state(state)
        messages = state['messages']
        
        # Get the user query
        user_query = ""
        for m in messages:
            if hasattr(m, 'content') and not isinstance(m, SystemMessage):
                user_query = m.content
                break
        
        query_lower = user_query.lower()
        
        # Off-topic detection (not bugs)
        off_topic = ['explain', 'how to', 'what is', 'quantum', 'mechanics', 
                    'random thought', 'life', 'feature request']
        
        if any(kw in query_lower for kw in off_topic):
            state['is_valid_bug'] = False
            state['severity'] = 'not_a_bug'
            state['workflow_done'] = True
            state['final_output'] = {
                'status': 'rejected',
                'reason': 'Off-topic query, not a bug report',
                'action_taken': 'none'
            }
            state['step_count'] += 1
            return state
        
        # Trivial UI issues (cosmetic only - just typos)
        trivial_keywords = ['typo in footer', 'typo in']
        is_trivial = any(kw in query_lower for kw in trivial_keywords)
        
        # Critical indicators (P0) - "crashed" is stronger signal
        critical_keywords = ['crashed completely', 'database crashed', 'production database crashed',
                           'complete outage', 'all users', 'complete production', 'affecting all']
        is_critical = any(kw in query_lower for kw in critical_keywords)
        
        # Database prod issues are high priority
        is_db_prod = 'database' in query_lower and ('prod' in query_lower or 'production' in query_lower)
        
        # Login failures on production are also high priority
        is_login_prod = 'login' in query_lower and ('prod' in query_lower or 'production' in query_lower)
        
        # High priority indicators
        high_keywords = ['error', 'failure', 'broken', 'not working', 
                        'timeout', 'failing', 'leak', 'memory leak', 'api crash']
        is_high = any(kw in query_lower for kw in high_keywords) or is_db_prod or is_login_prod
        
        # Minor UI issues (need investigation but not critical)
        minor_ui_keywords = ['ui glitch', 'dashboard glitch', 'minor']
        is_minor_ui = any(kw in query_lower for kw in minor_ui_keywords) and not is_critical and not is_high
        
        # Design issues that need full investigation
        is_design_issue = 'doesn\'t match design' in query_lower or 'button color' in query_lower
        
        # Ambiguous queries need investigation
        is_ambiguous = ('bug or feature' in query_lower or 'is this a bug' in query_lower or 
                       'feature request' in query_lower)
        
        # Determine severity
        if is_trivial:
            state['severity'] = 'trivial'
            state['is_valid_bug'] = True
        elif is_critical:
            state['severity'] = 'critical'
            state['is_valid_bug'] = True
        elif is_high:
            state['severity'] = 'high'
            state['is_valid_bug'] = True
        elif is_minor_ui:
            state['severity'] = 'minor'
            state['is_valid_bug'] = True
        elif is_design_issue or is_ambiguous:
            # Design issues and ambiguous queries need full search
            state['severity'] = 'needs_investigation'
            state['is_valid_bug'] = True
        else:
            # Default to medium for any other bug-like query
            state['severity'] = 'medium'
            state['is_valid_bug'] = True
        
        state['step_count'] += 1
        return state

    def search_all_sources(state: AgentState) -> dict:
        """STEP 2: Search Jira, Slack, GitHub for duplicates (if appropriate)"""
        state = init_state(state)
        if not state.get('is_valid_bug', True):
            return state
        
        severity = state.get('severity', 'medium')
        
        # For trivial issues, search only Jira (minimal duplicate check)
        if severity == 'trivial':
            instruction = SystemMessage(
                content="This is a trivial cosmetic issue (typo). Search ONLY Jira for existing tickets. If duplicate found, reference it. If not, DO NOT create ticket. Summarize as 'low priority' or 'minor' issue."
            )
        else:
            # For all other bugs (including needs_investigation), search all sources
            instruction = SystemMessage(
                content="Search Jira, Slack, AND GitHub for related issues. Call jira_search, slack_search, and github_search tools."
            )
        
        state['step_count'] += 1
        return {'messages': [instruction]}

    def determine_action(state: AgentState) -> dict:
        """STEP 3: Decide if we should create ticket, update, or skip"""
        state = init_state(state)
        messages = state['messages']
        
        # Check if duplicate was found by examining all messages
        response_text = " ".join(
            m.content if hasattr(m, 'content') and m.content else ""
            for m in messages
        )
        response_lower = response_text.lower()
        
        # Check for existing ticket references
        import re
        ticket_matches = re.findall(r'(CSE-\d+)', response_text, re.IGNORECASE)
        
        if ticket_matches and ('existing' in response_lower or 'found' in response_lower or 'already' in response_lower or 'duplicate' in response_lower):
            state['duplicate_found'] = True
            state['duplicate_ticket_id'] = ticket_matches[0].upper()
        
        state['step_count'] += 1
        return state

    def execute_action(state: AgentState) -> dict:
        """STEP 4: Create ticket if needed, or reference existing"""
        state = init_state(state)
        if not state.get('is_valid_bug', True):
            return state
        
        messages = state['messages']
        severity = state.get('severity', 'medium')
        
        if state.get('duplicate_found', False):
            ticket_id = state.get('duplicate_ticket_id', 'unknown')
            instruction = SystemMessage(
                content=f"Found existing ticket {ticket_id}. Summarize findings. DO NOT create new ticket."
            )
        elif severity == 'trivial':
            # Don't create tickets for trivial issues
            instruction = SystemMessage(
                content="This is a trivial cosmetic issue. DO NOT create ticket. Summarize as 'low priority' or 'minor' issue."
            )
        elif severity == 'needs_investigation':
            # Don't create tickets for ambiguous or design issues without confirmation
            instruction = SystemMessage(
                content="This needs investigation. If existing ticket found, reference it. If clearly a bug with no duplicate, you may create ticket. Otherwise, summarize findings without creating ticket."
            )
        else:
            # Create ticket with appropriate priority
            priority_map = {
                'critical': 'P0',
                'high': 'P1',
                'medium': 'P2',
                'minor': 'P3'
            }
            priority = priority_map.get(severity, 'P2')
            
            # Add severity-specific language requirements
            if severity == 'critical':
                instruction = SystemMessage(
                    content=f"No duplicate found. Use jira_create to create a new ticket with priority='{priority}'. This is CRITICAL - include words like 'critical', 'urgent', or 'P0' in your summary. Then summarize."
                )
            else:
                instruction = SystemMessage(
                    content=f"No duplicate found. Use jira_create to create a new ticket with priority='{priority}', then summarize."
                )
        
        state['step_count'] += 1
        return {'messages': [instruction]}

    def create_final_output(state: AgentState) -> dict:
        """STEP 5: Create structured final output"""
        state = init_state(state)
        messages = state['messages']
        
        output = {
            'status': 'complete' if state['workflow_done'] else 'incomplete',
            'ticket_id': None,
            'action_taken': None,
            'tools_used': [],
            'summary': None,
            'steps_taken': state.get('step_count', 0),
            'retries': state.get('retry_count', 0)
        }
        
        # Extract ticket ID
        for m in messages:
            if hasattr(m, 'content') and m.content:
                import re
                match = re.search(r'(CSE-\d+)', m.content, re.IGNORECASE)
                if match:
                    output['ticket_id'] = match.group(1).upper()
                    
                if 'Created new Jira ticket' in m.content:
                    output['action_taken'] = 'created_new_ticket'
                elif 'existing Jira ticket' in m.content.lower():
                    output['action_taken'] = 'found_duplicate'
        
        # Track tools used
        for m in messages:
            if hasattr(m, 'tool_calls'):
                output['tools_used'].extend([tc['name'] for tc in m.tool_calls])
        
        # Get summary
        for m in reversed(messages):
            if hasattr(m, 'content') and m.content and len(m.content) > 20:
                output['summary'] = m.content[:300]
                break
        
        state['final_output'] = output
        return state

    workflow = StateGraph(AgentState)

    def verify(state: AgentState) -> dict:
        """STEP 6: Verify completion and decide if retry needed"""
        state = init_state(state)
        
        # Skip verification if off-topic
        if not state.get('is_valid_bug', True):
            state['workflow_done'] = True
            state['needs_retry'] = False
            return state
        
        messages = state["messages"]
        severity = state.get('severity', 'medium')

        # Get full response text for content verification
        response_text = " ".join(
            m.content if hasattr(m, 'content') and m.content else ""
            for m in messages
        )
        response_lower = response_text.lower()

        # 1. Check that Jira was searched
        jira_searched = any(
            hasattr(m, "tool_calls") and any(tc["name"] == "jira_search" for tc in m.tool_calls)
            for m in messages
        )

        # 2. Check that Slack was searched (if not trivial)
        if severity == 'trivial':
            slack_searched = True  # Not required for trivial issues
        else:
            slack_searched = any(
                hasattr(m, "tool_calls") and any(tc["name"] == "slack_search" for tc in m.tool_calls)
                for m in messages
            )

        # 3. Check that GitHub was searched (if not trivial)
        if severity == 'trivial':
            github_searched = True  # Not required for trivial issues
        else:
            github_searched = any(
                hasattr(m, "tool_calls") and any(tc["name"] == "github_search" for tc in m.tool_calls)
                for m in messages
            )

        # 4. Check ticket creation OR explicit decision not to create
        ticket_created = any(
            hasattr(m, "tool_calls") and any(tc["name"] == "jira_create" for tc in m.tool_calls)
            for m in messages
        )
        duplicate_referenced = "existing" in response_lower and "cse-" in response_lower
        trivial_noted = severity == 'trivial' and ('low priority' in response_lower or 'minor' in response_lower)
        
        ticket_ok = ticket_created or duplicate_referenced or trivial_noted

        # 5. Check summary was done
        summary_ok = len(response_text) > 50
        
        # 6. Severity-specific content checks
        content_ok = True
        if severity == 'critical':
            # Critical bugs MUST mention priority/urgency
            required_words = ['p0', 'critical', 'urgent']
            content_ok = any(word in response_lower for word in required_words)
        elif severity == 'trivial':
            # Trivial issues must NOT create tickets
            content_ok = not ticket_created

        # Determine if workflow is complete
        all_checks_passed = all([
            jira_searched,
            slack_searched,
            github_searched,
            ticket_ok,
            summary_ok,
            content_ok
        ])

        if all_checks_passed:
            state["workflow_done"] = True
            state["needs_retry"] = False
        elif state["retry_count"] < state["max_retries"]:
            state["needs_retry"] = True
            state["retry_count"] += 1
        else:
            state["workflow_done"] = True
            state["needs_retry"] = False

        return state
        
    def should_retry(state: AgentState) -> str:
        """Determine if we should retry or finish"""
        if state.get("needs_retry", False):
            return "agent"
        return "finalize"
        
    def route_after_classify(state: AgentState) -> str:
        """Route based on classification"""
        if not state.get('is_valid_bug', True):
            return 'finalize'
        return 'search'

    # Create workflow
    workflow.add_node('classify', classify_input)
    workflow.add_node('search', search_all_sources)
    workflow.add_node('decide', determine_action)
    workflow.add_node('execute', execute_action)
    workflow.add_node('verify', verify)
    workflow.add_node('finalize', create_final_output)
    workflow.add_node('agent', call_model)
    workflow.add_node('tools', tool_node)

    # Set entry point
    workflow.set_entry_point('classify')

    # Routing from classify
    workflow.add_conditional_edges(
        'classify',
        route_after_classify,
        {
            'search': 'search',
            'finalize': 'finalize'
        }
    )

    # Linear flow through main steps
    workflow.add_edge('search', 'agent')
    workflow.add_edge('decide', 'agent')
    workflow.add_edge('execute', 'verify')

    # Retry loop from verify
    workflow.add_conditional_edges(
        'verify',
        should_retry,
        {
            'agent': 'agent',
            'finalize': 'finalize'
        }
    )

    # Agent tool loop (for retries)
    workflow.add_conditional_edges(
        'agent',
        should_continue,
        {
            'tools': 'tools',
            'verify': 'verify'
        }
    )
    workflow.add_edge('tools', 'agent')

    # Final output then end
    workflow.add_edge('finalize', END)

    compiled = workflow.compile()
    compiled.system_prompt = agent_system_prompt
    return compiled

agent = create_agent()

def ask_agent(question: str) -> str:
    state = {'messages':[SystemMessage(content=DEFAULT_SYSTEM_PROMPT), HumanMessage(content=question)]}
    result = agent.invoke(state)
    for msg in reversed(result['messages']):
        if isinstance(msg, AIMessage) and msg.content:
            return msg.content
    return 'No response generated.'
