import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# Configurações do Elasticsearch
ES_CLOUD_ID = os.getenv("ES_CLOUD_ID", "")
ES_API_KEY = os.getenv("ES_API_KEY", "")
ES_INDEX = os.getenv("ES_INDEX", "documentos")
ES_TIMEOUT = int(os.getenv("ES_TIMEOUT", "30"))
ES_MAX_RESULTS = int(os.getenv("ES_MAX_RESULTS", "5"))
ES_TEXT_FIELD = os.getenv("ES_TEXT_FIELD", "texto")  # Campo de texto principal para consultas
ES_SEMANTIC_FIELD = os.getenv("ES_SEMANTIC_FIELD", "semantic_text")  # Campo vetorizado

# Configurações da LLM (Groq)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3-70b-8192")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))

# Prompt templates
ELASTICSEARCH_QUERY_TEMPLATE = """
Você é um assistente especializado em transformar perguntas em consultas para Elasticsearch.
Baseado na seguinte pergunta do usuário, crie uma consulta híbrida para o Elasticsearch.

Pergunta do usuário: {query}

A consulta deve incluir:
1. Uma parte semântica (semantic search) usando o campo '{semantic_field}' para busca vetorial
2. Uma parte de texto (query_string) extraindo palavras-chave da pergunta do usuário

IMPORTANTE:
- Para a busca do tipo "query_string", você DEVE extrair apenas as palavras-chave relevantes da pergunta do usuário e formatá-las como uma consulta booleana.
- A consulta original completa do usuário só deve ser usada na parte semântica.

Exemplo de extração de palavras-chave:

Pergunta do usuário: "Quais podcasts de fitness são mais populares?"
Palavras-chave extraídas: "(fitness)"

Pergunta do usuário: "Me resuma 3 notícias de copas do mundo de futebol"
Palavras-chave extraídas: "(copa do mundo) OR (futebol)"

Pergunta do usuário: "Como posso melhorar meu sono com meditação?"
Palavras-chave extraídas: "(sono) OR (meditação) OR (insonia)"

Formate a consulta Elasticsearch como JSON seguindo este modelo:
{{
  "retriever": {{
    "rrf": {{
      "retrievers": [
        {{
          "standard": {{
            "query": {{
              "query_string": {{
                "default_field": "{text_field}",
                "query": "PALAVRAS_CHAVE_AQUI"  # Substitua por palavras-chave extraídas
              }}
            }}
          }}
        }},
        {{
          "standard": {{
            "query": {{
              "semantic": {{ 
                "field": "{semantic_field}",
                "query": "{query}"  # Mantenha a consulta original do usuário aqui
              }}
            }}
          }}
        }}
      ]
    }}
  }},
  "size": {max_results}
}}

Você DEVE substituir "PALAVRAS_CHAVE_AQUI" pelas palavras-chave relevantes que você extraiu da pergunta do usuário, formatadas como expressão booleana com operadores OR.
"""

RESPONSE_GENERATION_TEMPLATE = """
Você é um assistente especializado em fornecer respostas precisas com base no contexto fornecido.

Contexto:
{context}

Pergunta do usuário: {query}

Forneça uma resposta resumida e informativa com base apenas nas informações contidas no contexto acima. 
Se o contexto não contiver informações suficientes para responder à pergunta, indique isso claramente.
Não invente informações ou use conhecimento externo ao contexto fornecido.
Sempre forneça a resposta baseado nos documentos mais relevantes. Priorize-os, sempre. No entanto, não mencione o número do documento.
Sempre forneça a resposta em português, mesmo que o contexto esteja em outro idioma.
Seja breve, preciso e não vá muito além do solicitado.
"""
