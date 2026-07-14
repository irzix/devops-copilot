import logging
from langchain_core.messages import SystemMessage, HumanMessage
from app.modules.chat.agent import get_llm
from app.modules.memory.stores import LessonStore
from app.core.database import async_session_maker
from app.modules.chat.models import ChatMessage
from sqlmodel import select

class ReflexionPipeline:
    async def reflect_on_negative_feedback(
        self, 
        session_id: int, 
        message_id: int, 
        user_comment: str, 
        owner_id: int
    ):
        """
        Analyzes a conversation session that received negative feedback,
        extracts why the user was dissatisfied, and creates a structured lesson learned
        so the agent avoids this pattern in the future.
        """
        try:
            # 1. Fetch conversation history for this session
            async with async_session_maker() as db_session:
                stmt = select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc())
                res = await db_session.exec(stmt)
                db_messages = res.all()
            
            if not db_messages:
                return

            transcript_parts = []
            target_ai_message = ""
            for msg in db_messages:
                role = "User" if msg.sender == "user" else "AI"
                transcript_parts.append(f"[{role}]: {msg.content}")
                if msg.id == message_id:
                    target_ai_message = msg.content

            transcript = "\n".join(transcript_parts)
            
            prompt = """You are an Expert DevOps Post-Incident Analyst.
A DevOps administrator has given NEGATIVE feedback on one of the AI agent's responses.
Analyze the transcript of the conversation, the specific message they disliked, and their feedback comment.

Your task is to perform a root-cause analysis and output a JSON object representing a lesson learned to prevent this error in the future.

The user's feedback comment: "{feedback_comment}"
The AI response they disliked: "{target_ai_message}"

Output ONLY a JSON object with the following fields (no markdown formatting, no codeblocks):
{{
  "problem": "Brief description of the problem/request",
  "real_cause": "Why did the agent fail? (e.g., ran a dangerous command without explaining, ignored directory context, etc.)",
  "what_didnt_work": "The action or response the agent did that resulted in negative feedback",
  "what_worked": "What the agent SHOULD have done instead to satisfy the user",
  "time_to_resolve": "N/A"
}}
"""
            llm = get_llm()
            formatted_prompt = prompt.format(
                feedback_comment=user_comment or "No comment provided.",
                target_ai_message=target_ai_message
            )
            
            response = await llm.ainvoke([
                SystemMessage(content=formatted_prompt),
                HumanMessage(content=f"CONVERSATION TRANSCRIPT:\n{transcript}")
            ])
            
            import json
            text = response.content
            if isinstance(text, list):
                text = " ".join([str(t) for t in text])
            
            clean_json = text.strip()
            if clean_json.startswith("```json"):
                clean_json = clean_json[7:]
            if clean_json.startswith("```"):
                clean_json = clean_json[3:]
            if clean_json.endswith("```"):
                clean_json = clean_json[:-3]
            clean_json = clean_json.strip()
            
            data = json.loads(clean_json)
            
            # Save the generated lesson into LessonStore (ChromaDB)
            LessonStore.add_lesson(
                server_name="General/Reflexion",
                problem=data.get("problem", "User dissatisfaction with agent behavior"),
                real_cause=data.get("real_cause", ""),
                what_didnt_work=data.get("what_didnt_work", ""),
                what_worked=data.get("what_worked", ""),
                time_to_resolve="N/A",
                owner_id=owner_id
            )
            logging.info(f"Successfully recorded reflection lesson for session {session_id}")
            
        except Exception as e:
            logging.error(f"Error in negative feedback reflexion pipeline: {str(e)}")

# Single global instance
reflexion_pipeline = ReflexionPipeline()
