import groq
import json
import logging
from config import GROQ_API_KEY, LLM_MODEL, LLM_TEMPERATURE, ELASTICSEARCH_QUERY_TEMPLATE, RESPONSE_GENERATION_TEMPLATE, ES_TEXT_FIELD, ES_SEMANTIC_FIELD, ES_MAX_RESULTS

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        """
        Inicializa o cliente LLM com Groq API
        """
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY não encontrada. Configure a variável de ambiente ou o arquivo .env")
        
        logger.info(f"Inicializando cliente Groq com modelo: {LLM_MODEL}")
        self.client = groq.Client(api_key=GROQ_API_KEY)
        self.model = LLM_MODEL
        self.temperature = LLM_TEMPERATURE
    
    def prepare_elasticsearch_query(self, user_query, max_results=ES_MAX_RESULTS):
        """
        Prepara uma consulta Elasticsearch híbrida a partir da pergunta do usuário
        
        Args:
            user_query: Pergunta do usuário
            max_results: Número máximo de resultados a retornar
            
        Returns:
            Consulta JSON para o Elasticsearch
        """
        try:
            # Formatar o prompt com a pergunta do usuário e campos do Elasticsearch
            prompt = ELASTICSEARCH_QUERY_TEMPLATE.format(
                query=user_query,
                max_results=max_results,
                semantic_field=ES_SEMANTIC_FIELD,
                text_field=ES_TEXT_FIELD
            )
            
            # Chamar a API do Groq
            logger.info("Preparando consulta Elasticsearch com LLM")
            logger.debug(f"Prompt para gerar consulta: {prompt}")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Você é um assistente especializado em gerar consultas Elasticsearch e extrair palavras-chave relevantes."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature
            )
            
            # Extrair a consulta gerada do texto da resposta
            generated_text = response.choices[0].message.content
            logger.debug(f"Resposta da LLM: {generated_text}")
            
            # Extrair o JSON da resposta (pode estar entre ```json e ``` ou ser o texto completo)
            try:
                # Tentar extrair o JSON se estiver formatado com blocos de código markdown
                import re
                json_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
                json_match = re.search(json_pattern, generated_text)
                
                if json_match:
                    json_str = json_match.group(1)
                    query_json = json.loads(json_str)
                else:
                    # Tentar carregar o texto completo como JSON
                    query_json = json.loads(generated_text)
                
                # Verificar se a consulta foi gerada corretamente
                if 'retriever' in query_json and 'rrf' in query_json['retriever']:
                    # Estrutura correta baseada no novo template
                    logger.info("Consulta Elasticsearch RRF preparada com sucesso")
                    return query_json
                else:
                    logger.warning("A consulta gerada não segue o formato RRF esperado. Usando fallback.")
                    raise ValueError("Formato de consulta inválido")
                    
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Erro ao extrair ou validar JSON da resposta da LLM: {str(e)}")
                logger.error(f"Resposta recebida: {generated_text}")
                
                # Usar uma consulta RRF padrão como fallback
                # Extrair algumas palavras-chave simples da consulta original
                import re
                # Remove palavras comuns, pontuação e mantém palavras relevantes
                palavras = re.sub(r'[^\w\s]', ' ', user_query.lower())
                stop_words = {'o', 'a', 'os', 'as', 'de', 'da', 'do', 'das', 'dos', 'em', 'na', 'no', 'nas', 'nos', 'por', 'para', 'como', 'que', 'se', 'e', 'ou', 'é', 'são'}
                palavras_chave = ' OR '.join(['(' + palavra + ')' for palavra in palavras.split() if palavra not in stop_words and len(palavra) > 2])
                
                if not palavras_chave:
                    palavras_chave = user_query  # Uso a consulta original se não conseguir extrair palavras-chave
                
                fallback_query = {
                    "retriever": {
                        "rrf": {
                            "retrievers": [
                                {
                                    "standard": {
                                        "query": {
                                            "query_string": {
                                                "default_field": ES_TEXT_FIELD,
                                                "query": palavras_chave
                                            }
                                        }
                                    }
                                },
                                {
                                    "standard": {
                                        "query": {
                                            "semantic": { 
                                                "field": ES_SEMANTIC_FIELD,
                                                "query": user_query
                                            }
                                        }
                                    }
                                }
                            ]
                        }
                    },
                    "size": max_results
                }
                
                logger.info("Usando consulta fallback devido a erro na extração de JSON")
                return fallback_query
            
        except Exception as e:
            logger.error(f"Erro ao preparar consulta Elasticsearch: {str(e)}")
            raise
    
    def generate_response(self, user_query, documents):
        """
        Gera uma resposta para o usuário com base nos documentos recuperados
        
        Args:
            user_query: Pergunta do usuário
            documents: Documentos recuperados do Elasticsearch
            
        Returns:
            Resposta gerada pela LLM
        """
        try:
            if not documents:
                return "Não encontrei informações relevantes para responder sua pergunta. Por favor, reformule ou tente outra questão."
                
            # Formatar o contexto para o prompt
            formatted_context = ""
            for i, doc in enumerate(documents):
                formatted_context += f"Documento {i+1}:\n"
                
                # Se tivermos um campo de texto ou conteúdo específico, exiba-o
                # Adapte os campos conforme a estrutura real dos seus documentos
                source = doc["source"]
                
                # Tentar extrair o conteúdo do documento com base nos campos mais comuns
                # Adicione ou modifique os campos de acordo com a estrutura real do seu índice
                if ES_TEXT_FIELD in source:
                    formatted_context += f"{source[ES_TEXT_FIELD]}\n\n"
                elif "text" in source:
                    formatted_context += f"{source['text']}\n\n"
                elif "content" in source:
                    formatted_context += f"{source['content']}\n\n"
                elif "title" in source and "body" in source:
                    formatted_context += f"Título: {source['title']}\n\nConteúdo: {source['body']}\n\n"
                else:
                    # Mostrar todo o documento se não houver campo específico
                    # Excluir o campo vetorial para não sobrecarregar o contexto
                    source_copy = source.copy()
                    if ES_SEMANTIC_FIELD in source_copy:
                        del source_copy[ES_SEMANTIC_FIELD]
                    formatted_context += f"{json.dumps(source_copy, ensure_ascii=False, indent=2)}\n\n"
            
            # Formatar o prompt com a pergunta do usuário e o contexto
            prompt = RESPONSE_GENERATION_TEMPLATE.format(
                query=user_query,
                context=formatted_context
            )
            
            # Chamar a API do Groq
            logger.info("Gerando resposta para o usuário com LLM")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Você é um assistente especializado em fornecer respostas precisas baseadas no contexto."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature
            )
            
            # Extrair e retornar a resposta gerada
            answer = response.choices[0].message.content
            logger.info("Resposta gerada com sucesso")
            return answer
            
        except Exception as e:
            logger.error(f"Erro ao gerar resposta: {str(e)}")
            raise
