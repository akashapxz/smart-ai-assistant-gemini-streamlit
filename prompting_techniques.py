TECHNIQUES = {
    "None": "",

    "Zero-Shot Prompting": """
Complete the user's request accurately and directly.
No examples are provided.
""",

    "One-Shot Prompting": """
Example:
Input: Explain machine learning.
Output: Machine learning is a branch of artificial intelligence that enables systems to learn from data.

Now answer the user's request in the same style.
""",

    "Few-Shot Prompting": """
Examples:
Input: Define AI.
Output: Artificial intelligence is the simulation of human intelligence by machines.

Input: Define Python.
Output: Python is a high-level programming language known for readability and versatility.

Input: Explain Data Science.
Output: Data science is the field of extracting insights and knowledge from data.

Now answer the user's request in the same educational style.
""",

    "Chain-of-Thought Prompting": """
Reason step by step before giving the final answer.
Show intermediate reasoning clearly.
""",

    "Role-Based Prompting": """
Act as a world-class expert in the requested domain.
Provide professional and detailed explanations.
""",

    "Structured Output Prompting": """
Format your response using:

1. Summary
2. Detailed Explanation
3. Key Points
4. Examples
"""
}