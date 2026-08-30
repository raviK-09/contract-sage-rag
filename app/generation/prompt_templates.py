"""
System and user prompt templates for legal contract Q&A.
Enforces strict context grounding, mandatory [Source N] citations,
and an optional chain-of-thought reasoning mode.
"""


from dataclasses import dataclass

from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage

from app.retrieval.hybrid_retriever import RetrievedChunk


# ── System Prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are ContractSage, an expert legal document assistant.
Your job is to answer questions about legal contracts clearly and accurately.

## STRICT RULES YOU MUST FOLLOW:

1. **Answer ONLY from the provided context.** Never use outside knowledge.

2. **Cite every factual claim** using [Source N] format, where N matches
   the source label in the context (e.g. [Source 1], [Source 2]).
   - Place citations immediately after the claim they support.
   - You MUST cite at least one source for every answer.

3. **If the context doesn't contain enough information**, respond with EXACTLY:
   "INSUFFICIENT_CONTEXT: [brief explanation of what information is missing]"
   Do NOT guess or infer beyond what the documents state.

4. **Write in plain English** — explain legal terms when they appear.
   Your audience is a non-lawyer trying to understand their rights.

5. **Be concise but complete.** Answer the question fully, but don't pad.

6. **Never say "based on the document" or "the text says"** — just answer
   directly with citations. Bad: "The document says rent is Rs. 28,000."
   Good: "The monthly rent is Rs. 28,000 [Source 1]."

## CITATION FORMAT EXAMPLE:
If Source 1 mentions a 2-month notice period and Source 3 mentions forfeiture:
"Either party must give 2 months' written notice to terminate [Source 1].
If the tenant leaves during the lock-in period, the security deposit is
forfeited [Source 3]."
"""

SYSTEM_PROMPT_REASONING = """You are ContractSage, an expert legal document assistant.
Your job is to answer questions about legal contracts clearly and accurately.

## STRICT RULES YOU MUST FOLLOW:

1. **Answer ONLY from the provided context.** Never use outside knowledge.

2. **Think step by step** before giving your final answer:
   - First, identify which sources are relevant to the question
   - Then, extract the key information from those sources
   - Finally, compose a clear answer with citations

3. **Cite every factual claim** using [Source N] format.

4. **If the context doesn't contain enough information**, respond with EXACTLY:
   "INSUFFICIENT_CONTEXT: [brief explanation of what information is missing]"

5. **Write in plain English** for a non-lawyer audience.

Format your response as:
REASONING: [your step-by-step analysis]
ANSWER: [your final plain-English answer with citations]
"""


# ── Context Builder ───────────────────────────────────────────────────────────

@dataclass
class BuiltContext:
    """The formatted context string and its source mapping."""
    context_text: str                      # The full context to inject into prompt
    source_map: dict[int, RetrievedChunk]  # source_num → RetrievedChunk


def build_context_from_chunks(chunks: list[RetrievedChunk]) -> BuiltContext:
    """
    Format retrieved chunks into a numbered context block for the LLM.

    Each chunk is labelled [Source N] so the LLM can cite it precisely.
    The label number corresponds to what the LLM will write in citations.

    Output format:
        [Source 1] — residential_rental_agreement.pdf (Page 3)
        <chunk text>

        [Source 2] — residential_rental_agreement.pdf (Page 2)
        <chunk text>
        ...

    Args:
        chunks: Retrieved chunks from the hybrid retriever.

    Returns:
        BuiltContext with formatted text and source mapping.
    """
    context_parts: list[str] = []
    source_map: dict[int, RetrievedChunk] = {}

    for i, chunk in enumerate(chunks, start=1):
        source_num = i
        source_map[source_num] = chunk

        # Format source label
        file_name  = chunk.document.metadata.get("file_name", "Unknown Document")
        page_num   = chunk.document.metadata.get("page", "?")
        doc_type   = chunk.document.metadata.get("doc_type", "pdf")
        label_type = "Page" if doc_type == "pdf" else "Section"

        header = f"[Source {source_num}] — {file_name} ({label_type} {page_num})"
        context_parts.append(f"{header}\n{chunk.document.page_content.strip()}")

    context_text = "\n\n---\n\n".join(context_parts)
    return BuiltContext(context_text=context_text, source_map=source_map)


# ── Message Builder ───────────────────────────────────────────────────────────

def build_messages(
    query: str,
    chunks: list[RetrievedChunk],
    reasoning_mode: bool = False,
) -> tuple[list, BuiltContext]:
    """
    Build the complete message list for the LLM and return the context map.

    Args:
        query          : The user's question.
        chunks         : Retrieved chunks from the hybrid retriever.
        reasoning_mode : If True, use chain-of-thought system prompt.

    Returns:
        Tuple of (messages list for LLM, BuiltContext for citation parsing).
    """
    built_context = build_context_from_chunks(chunks)

    system_prompt = SYSTEM_PROMPT_REASONING if reasoning_mode else SYSTEM_PROMPT

    user_content = f"""## Context from your documents:

{built_context.context_text}

---

## Question:
{query}

Remember: Cite every claim with [Source N]. If the context is insufficient,
start your response with "INSUFFICIENT_CONTEXT:"."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content),
    ]

    return messages, built_context


def build_decline_message(reason: str) -> str:
    """
    Build a user-friendly decline message when confidence is too low.

    Trade-off: Hard decline vs partial answer with low-confidence warning.
    We chose hard decline for legal documents because:
    - A wrong answer about legal rights can cause real harm
    - "I don't know" is more trustworthy than "I think maybe..."
    - Users can rephrase and try again — it's not a dead end
    """
    return (
        f"⚠️ **I'm not confident enough to answer this question accurately.**\n\n"
        f"**Reason**: {reason}\n\n"
        f"**What you can do**:\n"
        f"- Try rephrasing your question with specific terms from the contract\n"
        f"- Make sure the relevant document has been uploaded\n"
        f"- Ask about a specific clause number (e.g. 'What does Clause 13 say?')"
    )
