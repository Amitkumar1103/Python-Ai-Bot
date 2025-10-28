import os
import json
from google import genai as gen
from dotenv import load_dotenv 


load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = gen.Client(api_key=api_key)
print("API Key Loaded:", api_key is not None)

class memoryy():
    def __init__(self):
        self.memory = self.load("facts.json")
        self.memory2 = self.load("chats.json")

    def load(self, file_path):
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                data = json.load(f)
                print(f"Memory loaded from {file_path}.")
            return data
        else:
            print(f"Memory file {file_path} not found. Returning empty memory.")
            return []

    def save(self, file_path, data):
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

    def storing_msg(self, user_input, ai_response, category="chat"):
        if category == "fact":
            self.memory.append({"user": user_input, "ai": ai_response})
            self.save("facts.json", self.memory)
            self.summ_combine(max_facts=15, size=10)
        else:
            max_memory = 50
            if len(self.memory2) > max_memory:
                self.memory2 = self.memory2[-max_memory:]
            self.memory2.append({"user": user_input, "ai": ai_response})
        self.save("chats.json", self.memory2)

    def summarize_facts(self, facts_list):
        if not facts_list:
            return "No facts available for summary."
        summary = "Facts Summary:\n"
        for i, fact in enumerate(facts_list, 1):
            summary += f"{i}. User: {fact.get('user')}\n   AI: {fact.get('ai')}\n"
        return summary


    def summ_combine(self, max_facts=50, size=10):
        if len(self.memory) > max_facts:
        # Only raw facts (ignore summaries)
            old_facts = [fact for fact in self.memory[:-size] if "summary" not in fact]
            latest_facts = self.memory[-size:]

        if old_facts:  # Only summarize if we actually have raw facts
            summarized = self.summarize_facts(old_facts)
            self.memory = [{"summary": summarized}] + latest_facts
            self.save("facts.json", self.memory)
            
    def add_fact(self, user, ai):
        self.memory.append({"user": user, "ai": ai})
        self.save("facts.json", self.memory)
        self.summ_combine(max_facts=50, size=10)
        
    def get_response(user_input, memory, client):
        if user_input.lower() in ["summary", "show summary", "summarize"]:
            return memory.summarize()
        facts = memory.memory
        facts_text = "\n".join([f"- {fact}" for fact in facts])
        prompt = f"""
            You are an AI that remembers facts about the user.
            Here are the stored facts so far:
        {facts_text}
        Now answer the user's input using these facts if relevant.
        User said: "{user_input}"
        """
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        return response.text




def ask(mem, contents):
    try:
        context = ""
        for fact in mem.memory:
            if "summary" not in fact: 
                context += f"- {fact.get('user')} \n  AI: {fact.get('ai')}\n"
        context += ""
        for chat in mem.memory2:
            context += f"User: {chat.get('user')}\nAI: {chat.get('ai')}\n"
        context += f"\nUser: {contents}\n"
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=context
        )
        reply= response.text.strip()
        
        if contents.lower() in  ["exit","bye","quit"]:
            print("Exiting the program.")
            exit()
        # if contents.lower() in ["summary", "show summary", "summarize"]:
        #     for item in mem.memory:
        #         if "summary" in item:
        #             return item["summary"]
        #     return "No summarized facts available yet."
        if contents.lower() in ["forget last message", "clear memory", "forget"]:
            mem.memory2.pop()
            mem.save("chats.json", mem.memory2)
            return "Last memory is cleared."
        if contents.lower() in ["clear all memory", "forget all"]:
            mem.memory2.clear()
            mem.save("chats.json", mem.memory2)
            return "all memory is cleared."
        if contents.lower().startswith("my") or "i am" in contents.lower() or "remember" in contents.lower() or "im" in contents.lower():
            mem.storing_msg(contents, reply, category="fact")
        else:
            mem.storing_msg(contents, reply, category="chat")
        return response.text
        

    except Exception as e:
        print("Error occurred while generating content:", e)
        return "Sorry, I couldn't generate a response."


m=memoryy()
print(len(m.memory), "memory items loaded.")
while True:
    user_input = input("You: ")
    reply = ask(m,user_input)
    print("AI:", reply)

