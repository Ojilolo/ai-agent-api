from flask import Flask, request, jsonify
import os
import subprocess
from groq import Groq

app = Flask(__name__)
# We will set the API key in Render's environment variables later
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

@app.route('/api/run_agent', methods=['POST'])
def run_agent():
    data = request.get_json()
    goal = data.get('goal', '')
    
    if not goal:
        return jsonify({"error": "No goal provided"}), 400

    history = []
    final_output = ""
    
    for i in range(2): # 2 iterations
        prompt = f"""
        You are an autonomous AI agent running inside a Linux cloud server.
        Goal: {goal}
        Write ONLY Python code to achieve the next step. No markdown. Code must print results.
        Previous history: {history}
        """
        
        try:
            response = client.chat.completions.create(
                model="qwen/qwen3.8-27b",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            generated_code = response.choices[0].message.content.strip()
            
            if generated_code.startswith("```python"): generated_code = generated_code[9:]
            if generated_code.endswith("```"): generated_code = generated_code[:-3]
            
            with open("agent_action.py", "w") as f:
                f.write(generated_code)
                
            result = subprocess.run(["python", "agent_action.py"], capture_output=True, text=True, timeout=15)
            output = result.stdout + result.stderr
            
            final_output += f"--- Iteration {i+1} ---\nCode:\n{generated_code}\n\nOutput:\n{output}\n\n"
            history.append(f"Code: {generated_code} Output: {output}")
            
        except Exception as e:
            final_output += f"Error: {str(e)}"
            break

    return jsonify({"result": final_output})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
