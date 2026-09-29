import os

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0
)


prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are an AI Engineering Design Review assistant.

Your job is to explain CAD inspection findings to an engineer.

STRICT RULES:

1. Use ONLY the CAD data and inspection findings provided.
2. Do NOT invent measurements.
3. Do NOT invent material properties.
4. Do NOT invent manufacturing capabilities.
5. Do NOT claim that a design is safe or unsafe without sufficient evidence.
6. Clearly distinguish measured facts from engineering considerations.
7. Explain why each finding may matter from an engineering or manufacturing perspective.
8. Recommend what an engineer should review next.
"""
    ),
    (
        "human",
        """
CAD PART:

{cad_data}

RULE-BASED INSPECTION FINDINGS:

{findings}

Provide an engineering review with:

1. Summary
2. Findings
3. Engineering considerations
4. Recommended review actions
"""
    )
])


def generate_engineering_review(
    cad_data: dict,
    findings: list
) -> str:

    chain = prompt | llm

    response = chain.invoke({
        "cad_data": cad_data,
        "findings": findings
    })

    return response.content # type: ignore

def generate_reuse_review(
    source_part: dict,
    reuse_candidates: list
) -> str:

    reuse_prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """
You are an AI engineering design-review assistant.

Analyze CAD part reuse candidates.

STRICT RULES:

1. Use only the supplied CAD data.
2. Do not invent engineering measurements.
3. Do not claim that a part is safe to reuse.
4. Do not make the final engineering approval decision.
5. Explain similarities and differences using the supplied data.
6. Clearly identify warnings and review requirements.
7. Treat reuse_candidate as a candidate for engineering review,
   not as an approval.
"""
        ),
        (
            "human",
            """
SOURCE CAD PART:

{source_part}

REUSE CANDIDATES:

{reuse_candidates}

Provide:

## Source Part

Summarize the source part.

## Similar Parts

Explain the strongest similarities.

## Reuse Considerations

For each significant candidate, explain:

- why it is similar
- important differences
- reuse advantages
- engineering concerns

## Recommended Engineering Review

List the checks an engineer should perform before reuse.
"""
        )
    ])

    chain = reuse_prompt | llm

    response = chain.invoke({
        "source_part": source_part,
        "reuse_candidates": reuse_candidates
    })

    return response.content # type: ignore

def generate_part_intelligence_review(
    question: str,
    intelligence: dict
) -> str:

    intelligence_prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """
You are an AI Engineering Part Intelligence assistant.

Your job is to help engineers evaluate whether an existing CAD part
should be considered for a future development.

STRICT RULES:

1. Use ONLY the supplied part intelligence data.
2. Do not invent measurements, products, materials, loads, or requirements.
3. Do not claim that a part is safe or unsafe.
4. Do not give final engineering approval.
5. Do not replace engineering validation.
6. Clearly distinguish existing facts from engineering considerations.
7. Explain similarities and differences using the supplied data.
8. Consider where the part is currently used.
9. Consider reuse history and lifecycle information.
10. Identify engineering checks required before reuse.
11. If the supplied data is insufficient to answer something, explicitly say so.

Your response must contain:

## Answer

Directly address the engineer's question.

## Part

Summarize the requested part.

## Current Usage

Explain where the part is currently used based only on the supplied
where-used information.

## Similar Parts

Identify relevant similar parts and explain the supplied similarities
and differences.

## Future Development Consideration

Explain why the part may be considered as an existing design candidate,
and identify limitations in the available data.

## Engineering Checks

List the engineering checks that should be performed before reuse.

## Conclusion

Give a concise conclusion using language such as:
- "Can be considered for engineering review"
- "Requires engineering review"
- "Insufficient data to determine"

Do not provide final approval.
"""
        ),
        (
            "human",
            """
ENGINEER QUESTION:

{question}

PART INTELLIGENCE:

{intelligence}
"""
        )
    ])

    chain = intelligence_prompt | llm

    response = chain.invoke({
        "question": question,
        "intelligence": intelligence
    })

    return response.content # type: ignore