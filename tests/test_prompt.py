from src.prompt_builder import PromptBuilder

builder = PromptBuilder()

fake_results = [
    {
        "text": "Employee examinations are scheduled through the Personnel Chief.",
        "metadata": {
            "filename": "Medical_SOP.pdf"
        }
    }
]

prompt = builder.build_prompt(
    "Who schedules employee examinations?",
    fake_results
)

print(prompt)