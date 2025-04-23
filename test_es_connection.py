from elasticsearch import Elasticsearch
import logging
from dotenv import load_dotenv
import os
import sys

# Configurar logging detalhado
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("es_test")

# Carregar variáveis do arquivo .env
load_dotenv()

# Obter configurações
es_cloud_id = os.getenv("ES_CLOUD_ID", "")
es_api_key = os.getenv("ES_API_KEY", "")
es_index = os.getenv("ES_INDEX", "documentos")

logger.info(f"Verificando conexão com Elasticsearch")
logger.info(f"Cloud ID (primeiros 10 caracteres): {es_cloud_id[:10]}...")  # Mostrar apenas parte do Cloud ID por segurança
logger.info(f"Index configurado: {es_index}")

try:
    # Tentar conectar
    logger.info("Inicializando cliente Elasticsearch...")
    es = Elasticsearch(
        cloud_id=es_cloud_id,
        api_key=es_api_key,
        verify_certs=True,
        request_timeout=30
    )
    
    # Tentar fazer ping
    logger.info("Testando conexão com ping()...")
    if es.ping():
        logger.info("Conexão realizada com sucesso!")
    else:
        logger.error("Ping retornou falso - problema de conexão.")
        sys.exit(1)
    
    # Tentar verificar o índice
    logger.info(f"Verificando índice '{es_index}'...")
    if es.indices.exists(index=es_index):
        logger.info(f"Índice '{es_index}' encontrado.")
        
        # Verificar mapeamento
        logger.info(f"Obtendo mapeamento do índice...")
        mapping = es.indices.get_mapping(index=es_index)
        logger.info(f"Mapeamento obtido com sucesso.")
        
        # Contar documentos
        logger.info(f"Contando documentos...")
        count = es.count(index=es_index)
        logger.info(f"O índice contém {count['count']} documentos.")
        
        # Verificar um documento de exemplo
        logger.info(f"Buscando um documento de exemplo...")
        try:
            sample = es.search(index=es_index, size=1)
            if sample["hits"]["hits"]:
                logger.info(f"Documento de exemplo encontrado com ID: {sample['hits']['hits'][0]['_id']}")
            else:
                logger.info(f"Nenhum documento encontrado no índice.")
        except Exception as e:
            logger.error(f"Erro ao buscar documento de exemplo: {str(e)}")
    else:
        logger.error(f"Índice '{es_index}' não existe!")
        logger.info("Listando índices disponíveis...")
        indices = es.indices.get_alias(index="*")
        logger.info(f"Índices disponíveis: {', '.join(indices.keys())}")
    
except Exception as e:
    logger.error(f"Erro na conexão: {str(e)}")
    logger.error(f"Tipo de erro: {type(e).__name__}")
    logger.error("Verifique se o Cloud ID e API Key estão corretos no arquivo .env")
    sys.exit(1)
