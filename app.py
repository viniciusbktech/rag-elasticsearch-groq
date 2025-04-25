import gradio as gr
import logging
import json
import time
from config import ES_MAX_RESULTS
from utils.es_client import ElasticsearchClient
from utils.llm_client import LLMClient

# Corrigir o problema de compatibilidade com Pydantic v2
import pydantic
from pydantic import BaseModel

# Configurar Pydantic para lidar com tipos arbitrários
class Config:
    arbitrary_types_allowed = True

pydantic.config.ConfigDict = lambda **kwargs: {**Config.__dict__, **kwargs}

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RAGPipeline:
    def __init__(self):
        """
        Inicializa a pipeline RAG com todos os componentes necessários
        """
        logger.info("Inicializando pipeline RAG")
        
        # Inicializar clientes
        self.es_client = ElasticsearchClient()
        self.llm_client = LLMClient()
        
        logger.info("Pipeline RAG inicializada com sucesso")
    
    def process_query(self, user_query, use_llm_query=True):
        """
        Processa a consulta do usuário através da pipeline RAG completa
        
        Args:
            user_query: Pergunta ou consulta do usuário
            use_llm_query: Se True, usa a LLM para preparar a consulta Elasticsearch. Se False, usa diretamente a busca semântica do ES.
            
        Returns:
            Resposta final
        """
        try:
            start_time = time.time()
            
            # 1. Usar a LLM para preparar a query do Elasticsearch (ou usar diretamente a busca semântica)
            if use_llm_query:
                logger.info("Preparando consulta Elasticsearch com LLM")
                es_query = self.llm_client.prepare_elasticsearch_query(user_query, ES_MAX_RESULTS)
                logger.info("Executando consulta personalizada no Elasticsearch")
                documents = self.es_client.search(es_query)
            else:
                # Usando diretamente a busca semântica nativa do Elasticsearch
                logger.info("Realizando busca semântica direta no Elasticsearch")
                documents = self.es_client.semantic_search(user_query, ES_MAX_RESULTS)
            
            # Registrar tempo de busca
            search_time = time.time() - start_time
            logger.info(f"Busca concluída em {search_time:.2f} segundos. Encontrados {len(documents)} documentos.")
            
            # 2. Gerar resposta com base nos documentos encontrados
            if not documents:
                answer = "Não encontrei informações relevantes para responder sua pergunta."
            else:
                logger.info(f"Gerando resposta com LLM com base em {len(documents)} documentos")
                answer = self.llm_client.generate_response(user_query, documents)
            
            total_time = time.time() - start_time
            logger.info(f"Processamento completo em {total_time:.2f} segundos")
            
            return answer
        except Exception as e:
            logger.error(f"Erro ao processar consulta: {str(e)}")
            return f"Ocorreu um erro ao processar sua consulta: {str(e)}"

# Inicializar a pipeline ao carregar o módulo
rag_pipeline = None

def initialize_pipeline():
    global rag_pipeline
    try:
        rag_pipeline = RAGPipeline()
        return "Pipeline RAG inicializada com sucesso!"
    except Exception as e:
        return f"Erro ao inicializar pipeline: {str(e)}"

def process_user_query(query, use_llm_for_query):
    """Função para processar a consulta do usuário através da interface"""
    global rag_pipeline
    
    if rag_pipeline is None:
        result = initialize_pipeline()
        if "Erro" in result:
            return result
    
    return rag_pipeline.process_query(query, use_llm_for_query)

# Interface Gradio
def create_interface():
    """Cria a interface do usuário com Gradio"""
    with gr.Blocks(title="RAG Elasticsearch + Groq") as interface:
        gr.Markdown("# RAG com Elasticsearch e Groq")
        gr.Markdown("Este sistema utiliza Elasticsearch para busca semântica e Groq API para geração de respostas.")
        
        with gr.Row():
            with gr.Column():
                init_button = gr.Button("Inicializar Pipeline")
                init_output = gr.Textbox(label="Status de inicialização")
                init_button.click(initialize_pipeline, outputs=init_output)
        
        with gr.Row():
            with gr.Column():
                query_input = gr.Textbox(lines=3, label="Sua pergunta")
                
                with gr.Row():

                    use_llm_for_query = gr.Checkbox(label="Usar LLM para preparar consulta", value=True, 
                                                info="Se ativado, a LLM irá preparar a consulta Elasticsearch. Se desativado, usará a busca semântica direta.")
                
                search_button = gr.Button("Buscar", variant="primary")
            
            with gr.Column():
                answer_output = gr.Markdown(label="Resposta", value="", show_label=True)
        
        with gr.Accordion("Sobre o sistema", open=False):
            gr.Markdown("""
            ## Como funciona este sistema RAG?
            
            1. **Recebimento da pergunta**: O sistema recebe sua pergunta em linguagem natural
            2. **Preparação da consulta**: A LLM (via Groq API) transforma sua pergunta em uma consulta híbrida para o Elasticsearch
            3. **Busca semântica**: O Elasticsearch realiza uma busca híbrida (semântica + textual) no índice
            4. **Contextualização**: Os documentos mais relevantes são extraídos
            5. **Geração de resposta**: A LLM gera uma resposta contextualizada usando os documentos recuperados
            
            O sistema utiliza o modelo de linguagem do Groq e as capacidades de busca semântica nativa do Elasticsearch.
            """)
        
        search_button.click(
            process_user_query, 
            inputs=[query_input, use_llm_for_query], 
            outputs=answer_output
        )
        
    return interface

if __name__ == "__main__":
    # Criar e iniciar a interface
    demo = create_interface()
    demo.launch(share=False)  # share=True para compartilhar link público (opcional)
