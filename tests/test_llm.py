from src.llm import LLM


llm = LLM()

answer = llm.generate(
    """
    Explain machine learning in one sentence.
    """
)

print("\nANSWER\n")
print(answer)