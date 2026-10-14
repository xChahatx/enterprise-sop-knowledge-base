"""
Conversation Memory

Stores previous user interactions so follow-up
questions can use previous context.

Example

User:
What is the leave policy?

Bot:
...

User:
How many days?

↓

Question becomes

What is the leave policy?
How many days?
"""

from collections import deque
from typing import List, Dict


class ConversationMemory:

    def __init__(self, max_history: int = 5):

        self.max_history = max_history

        self.history = deque(maxlen=max_history)

    ###########################################################

    def add_turn(
        self,
        question: str,
        answer: str
    ):

        self.history.append(
            {
                "question": question,
                "answer": answer
            }
        )

    ###########################################################

    def clear(self):

        self.history.clear()

    ###########################################################

    def get_history(self):

        return list(self.history)

    ###########################################################

    def build_context(self):

        """
        Builds conversation history
        for prompt.

        Returns string.
        """

        if len(self.history) == 0:
            return ""

        text = []

        for turn in self.history:

            text.append(
                f"User: {turn['question']}"
            )

            text.append(
                f"Assistant: {turn['answer']}"
            )

        return "\n".join(text)

    ###########################################################

    def rewrite_question(
        self,
        question: str
    ):

        """
        Very lightweight query rewriting.

        Example

        Previous:
        What is health screening?

        New:
        How often is it?

        →

        What is health screening?
        How often is it?
        """

        if len(self.history) == 0:
            return question

        previous = self.history[-1]["question"]

        followup_words = [

            "it",
            "they",
            "them",
            "that",
            "those",
            "this",
            "these",

            "he",
            "she",

            "its",

            "their",

            "there",

            "here"
        ]

        lower = question.lower()

        if any(word in lower for word in followup_words):

            return previous + "\n" + question

        return question