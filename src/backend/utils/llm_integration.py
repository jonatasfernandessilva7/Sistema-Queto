from services.service_llama_api import llama_api_call

import httpx

def clean_text(text):

    return text.encode("utf-8", "ignore").decode("utf-8").strip()

def truncate_text(text, max_tokens=2048):

    words = text.split()

    return " ".join(words[:max_tokens])

def generate_initial_prompt(document_text, analysis_data=None):

    document_text = clean_text(truncate_text(document_text))

    metrics_section = ""
    if analysis_data:
        metrics_section = f"""
### Document Metrics:
- Complexity: {analysis_data.get('complexity', 'N/A')}
- Vocabulary Diversity: {analysis_data.get('vocabulary_diversity', 0.0):.2f}
- Writing Style: {'Passive' if analysis_data.get('style', 0) > 0 else 'Active'}
- Sentiment: Negative={analysis_data['details']['sentiment']['neg']:.2f}, Neutral={analysis_data['details']['sentiment']['neu']:.2f}, Positive={analysis_data['details']['sentiment']['pos']:.2f}
- Key Terms: {', '.join(analysis_data.get('key_terms', ['N/A']))}
- Main Topics: {', '.join(analysis_data.get('topics', ['N/A']))}
"""

    prompt = f"""
You are an expert crisis analyst tasked with evaluating documents based on their adherence to crisis best practices, crisis identification, and compliance with standards like NIST and ISO 22361:2022.

### Document Excerpt:
{document_text}

{metrics_section}

### Task:
Perform an initial cybersecurity assessment of the document. Focus on:
1.  Identifying potential organizationals crisis.
2.  Assessing proposed threat mitigation strategies.
3.  Commenting on the document's general writing style regarding crisis (e.g., clarity, conciseness, technical accuracy).
4.  Providing initial recommendations for improvement.

Your response should be concise and direct.
"""
    return prompt

def generate_refined_prompt(initial_response, document_text):

    prompt = f"""
You have provided an initial crisis assessment of the document. Now, refine your analysis to improve its clarity, depth, and alignment with industry best practices.

### Initial Assessment:
{initial_response}

### Additional Considerations:
- Expand on any vague or generic risks.
- Provide specific solutions for unclear recommendations.
- Compare the document more explicitly to NIST, ISO 22361.
- Ensure the response is actionable and precise.

### Expected Final Analysis:
1. Strengths & Weaknesses
2. Clearer Organizationals Crisis
3. Stronger Compliance Evaluation
4. Refined Recommendations
"""
    
    return prompt

async def analise_com_llm(document_text, analysis_data=None):

    initial_prompt = generate_initial_prompt(document_text, analysis_data)
    
    try:

        initial_response = await llama_api_call(initial_prompt)

        refined_prompt = generate_refined_prompt(initial_response, document_text)
        refined_response = await llama_api_call(refined_prompt)
        
        return refined_response
    
    except httpx.HTTPStatusError as e:

        return f"Erro na chamada da API do Groq: {e.response.status_code} - {e.response.text}"
    
    except Exception as e:
        
        return f"Ocorreu um erro ao analisar com o LLM do Groq: {e}"