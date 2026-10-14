from typing import List, Dict


class PromptBuilder:

    def build_prompt(
        self,
        question: str,
        search_results: List[Dict]
    ) -> str:

        context_parts = []

        for result in search_results:

            page = result.get("page", "Unknown")
            text = result.get("text", "")

            context_parts.append(
f"""
Page: {page}

{text}
"""
            )

        context = "\n\n".join(context_parts)

        prompt = f"""
You are an Enterprise SOP AI Assistant.

Answer ONLY using the retrieved SOP context.

Rules:

- Never use outside knowledge.
- Never invent information.
- Merge information from all retrieved context.
- Treat related sections, keywords, and concepts as relevant even if the exact wording of the question is not present.
- Remove duplicate points.
- Use clear bullet points whenever possible.
- Do not mention filenames.
- Do not mention chunk IDs.
- Do not mention Document 1, Document 2 or similar labels.
- Do not explain how you found the answer.
- If the retrieved context contains relevant information but does not fully answer the question, provide the available information and clearly state that it is a partial answer.
- Only use the exact fallback response if there is no relevant information related to the question in the retrieved context.


I could not find this information in the uploaded SOP documents.

Context:

{context}

Question:

{question}

Answer:
"""

        print("\n" + "=" * 100)
        print("PROMPT PREVIEW")
        print("=" * 100)
        print(prompt)
        print("=" * 100)

        return prompt