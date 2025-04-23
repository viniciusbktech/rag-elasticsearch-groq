from elasticsearch import Elasticsearch
import json
import logging
from config import ES_CLOUD_ID, ES_API_KEY, ES_INDEX, ES_TIMEOUT, ES_MAX_RESULTS, ES_TEXT_FIELD, ES_SEMANTIC_FIELD

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ElasticsearchClient:
    def __init__(self):
        try:
            # Verificar se temos as credenciais necessárias
            if not ES_CLOUD_ID:
                raise ValueError("ES_CLOUD_ID não configurado no arquivo .env")
                
            if not ES_API_KEY:
                raise ValueError("ES_API_KEY não configurado no arquivo .env")
                
            logger.info(f"Tentando conectar ao Elasticsearch usando cloud_id: {ES_CLOUD_ID[:10]}...")
            
            # Inicializar cliente usando cloud_id e api_key
            self.es = Elasticsearch(
                cloud_id=ES_CLOUD_ID,
                api_key=ES_API_KEY,
                verify_certs=True,  # Geralmente True para conexões cloud
                request_timeout=ES_TIMEOUT
            )
            
            # Verificar conexão
            logger.info("Verificando conexão com o Elasticsearch...")
            ping_result = self.es.ping()
            if not ping_result:
                raise ConnectionError("Falha no ping: Não foi possível conectar ao Elasticsearch")
            
            logger.info("Conectado ao Elasticsearch com sucesso!")
                
        except Exception as e:
            logger.error(f"Erro ao conectar ao Elasticsearch: {str(e)}")
            raise
        
    def search(self, query_json, size=ES_MAX_RESULTS):
        """
        Executa uma consulta JSON no Elasticsearch
        
        Args:
            query_json: JSON da consulta Elasticsearch (já formatado)
            size: número máximo de resultados a retornar (substitui o valor no query_json se presente)
            
        Returns:
            Lista de documentos correspondentes
        """
        try:
            # Garantir que o query_json é um dicionário
            if isinstance(query_json, str):
                query = json.loads(query_json)
            else:
                query = query_json
            
            # Definir o tamanho máximo de resultados se não estiver definido no query
            if "size" not in query:
                query["size"] = size
            
            # Executar a consulta
            logger.info(f"Executando consulta no índice {ES_INDEX}")
            logger.debug(f"Query: {json.dumps(query, indent=2, ensure_ascii=False)}")
            logger.info(f"Consulta JSON enviada ao Elasticsearch:\n{json.dumps(query, ensure_ascii=False, indent=2)}")
            response = self.es.search(index=ES_INDEX, body=query)
            logger.info(f"Encontrados {len(response['hits']['hits'])} resultados")
            
            # Processar resultados
            hits = response["hits"]["hits"]
            logger.info(f"Encontrados {len(hits)} resultados")
            
            # Extrair documentos
            documents = []
            for hit in hits:
                doc = {
                    "id": hit["_id"],
                    "score": hit["_score"],
                    "source": hit["_source"]
                }
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"Erro na consulta ao Elasticsearch: {str(e)}")
            raise
    
    def semantic_search(self, query_text, size=ES_MAX_RESULTS):
        """
        Realiza uma busca híbrida (vetorial + textual) utilizando a funcionalidade nativa de semantic search do Elasticsearch
        com o formato RRF (Reciprocal Rank Fusion)
        
        Args:
            query_text: Texto da consulta
            size: número máximo de resultados a retornar
            
        Returns:
            Lista de documentos correspondentes
        """
        try:
            # Extrair palavras-chave simples para query_string
            import re
            # Remove pontuação e caracteres especiais
            palavras = re.sub(r'[^\w\s]', ' ', query_text.lower())
            # Lista de stop words em português
            stop_words = {'o', 'a', 'os', 'as', 'de', 'da', 'do', 'das', 'dos', 'em', 'na', 'no',
                          'nas', 'nos', 'por', 'para', 'como', 'que', 'se', 'e', 'ou', 'é', 'são', 
                          'um', 'uma', 'uns', 'umas', 'ao', 'aos', 'pelo', 'pela'}
            # Criar expressão com palavras-chave relevantes
            palavras_filtradas = [palavra for palavra in palavras.split() if palavra not in stop_words and len(palavra) > 2]
            
            if palavras_filtradas:
                palavras_chave = ' OR '.join(['(' + palavra + ')' for palavra in palavras_filtradas])
            else:
                # Se não conseguiu extrair palavras-chave, usa algumas palavras da query original
                palavras_chave = ' OR '.join(['(' + palavra + ')' for palavra in query_text.split()[:3] if len(palavra) > 2])
                if not palavras_chave:
                    palavras_chave = query_text  # Último recurso: usa a query original
            
            # Construir a consulta RRF (Reciprocal Rank Fusion)
            query = {
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
                                            "query": query_text
                                        }
                                    }
                                }
                            }
                        ]
                    }
                },
                "size": size
            }
            
            logger.info(f"Executando busca RRF com consulta: '{query_text}'")
            logger.info(f"Palavras-chave extraídas: '{palavras_chave}'")
            
            # Executar a consulta
            return self.search(query)
            
        except Exception as e:
            logger.error(f"Erro na consulta semântica: {str(e)}")
            raise
    
    def get_index_info(self):
        """Retorna informações sobre o índice configurado"""
        try:
            return self.es.indices.get(index=ES_INDEX)
        except Exception as e:
            logger.error(f"Erro ao obter informações do índice: {str(e)}")
            raise
