# RAG com Elasticsearch e Groq

Este projeto implementa uma arquitetura RAG (Retrieval-Augmented Generation) utilizando Elasticsearch para busca semântica e a API do Groq para geração de respostas.

## Arquitetura

O sistema funciona da seguinte forma:
1. O usuário envia uma pergunta através do chatbot
2. A LLM (via API Groq) transforma a pergunta em uma consulta híbrida para o Elasticsearch
3. O Elasticsearch realiza a busca semântica utilizando sua capacidade nativa de vetorização
4. Os documentos mais relevantes são recuperados
5. A LLM gera uma resposta contextualizada com base nos documentos encontrados

## Estrutura do Projeto

```
├── app.py             # Aplicação principal com interface Gradio
├── config.py          # Configurações (ES, LLM, etc.)
├── .env.example       # Exemplo de variáveis de ambiente
├── requirements.txt   # Dependências
└── utils/
    ├── __init__.py
    ├── es_client.py   # Cliente Elasticsearch
    └── llm_client.py  # Cliente LLM (Groq)
```

## Pré-requisitos

- Python 3.8+
- Acesso a um cluster Elasticsearch com índice que contém campo semantic_text vetorizado
- Chave de API do Groq

## Configuração

1. Clone este repositório
2. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```
3. Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:
   ```
   # Elasticsearch
   ES_HOST=seu_host_elasticsearch
   ES_PORT=9200
   ES_USERNAME=seu_usuario # se necessário
   ES_PASSWORD=sua_senha # se necessário
   ES_INDEX=nome_do_indice
   ES_TEXT_FIELD=texto # campo de texto principal
   ES_SEMANTIC_FIELD=semantic_text # campo vetorizado
   ES_TIMEOUT=30
   ES_MAX_RESULTS=5
   
   # Groq API
   GROQ_API_KEY=sua_chave_api_groq
   LLM_MODEL=llama3-70b-8192
   LLM_TEMPERATURE=0.3
   ```

## Uso

Execute a aplicação com:
```
python app.py
```

A interface web será iniciada localmente. Você pode:
1. Clicar em "Inicializar Pipeline" para conectar ao Elasticsearch e preparar o sistema
2. Digitar sua pergunta e clicar em "Buscar"
3. Opcionalmente, ativar/desativar as opções:
   - "Mostrar detalhes da pesquisa" para ver informações sobre os documentos recuperados
   - "Usar LLM para preparar consulta" para alternar entre consulta personalizada pela LLM ou busca semântica direta

## Fluxo de Funcionamento

### Com preparação de consulta pela LLM (recomendado)
1. A pergunta do usuário é enviada para a LLM
2. A LLM prepara uma consulta híbrida optimizada para o Elasticsearch
3. O Elasticsearch executa a consulta e retorna documentos relevantes
4. A LLM gera uma resposta com base nos documentos recuperados

### Sem preparação de consulta (busca semântica direta)
1. A pergunta do usuário é enviada diretamente para o Elasticsearch
2. O Elasticsearch utiliza suas capacidades nativas de busca híbrida
3. Os documentos relevantes são recuperados
4. A LLM gera uma resposta com base nos documentos recuperados

## Boas Práticas Implementadas

- **Busca híbrida**: Combina busca semântica (vetores) e busca textual (BM25) para melhores resultados
- **Timeouts e limites**: Configurados para evitar consultas que retornem muitos documentos
- **Consultas fallback**: Sistema robusto com consultas alternativas em caso de falha
- **Logging**: Sistema completo de logs para rastrear problemas
- **Tratamento de erros**: Captura e reporta erros de forma amigável

## Personalização

Para adaptar o sistema a diferentes índices ou modelos:
- Ajuste as configurações no arquivo `.env`
- Modifique os templates de prompt em `config.py` para se adequar ao seu caso de uso
- Adapte o processamento de documentos em `llm_client.py` de acordo com a estrutura do seu índice
