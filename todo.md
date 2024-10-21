
Auto summarize


# Code stuff
- Linting

# Future versions: 
- Suporte more models other than OpenAI
    - Any LLM do crew ai 
    - permitir mais de um vetorizer
    - Colocar o Gemini como modelo de consulta de documentos
    - Permitir usar modelos como Ollama entre outros
    - Tentar usar o Pydantic Output Parser
    - Tentar remover langchain_openai e anthropic
- DB consistency
    - delete notebook (o que fazer com os filhos)
    - Ta acumulando 2 sumaries
    - deletar filhos quando deletar pais
- Brincar com o tema do Streamlit
- Docstrings
- Arrumar o chat quando houver utilização de ferramentas
- Implementar streaming no chat também
- Citacions: explicar de onde vieram os insights
- Usar propósito do projeto para sumarizar
- Melhorar Citacions: explicar de onde vieram os insights
- Melhorar as estratégias de embedding e limpeza de conteúdo e indexação
- Improve streamlit navigation and refresh
- Mais de uma sessão de chats?
- Melhorias no banco, menos tabelas, mais inteligentes
- Live Query for the front end
- Implementar a ideia do Fabric de prompts e perguntas recomendadas
- Menu bar: sources, notes, projects, search, topics
- Trazer algum sistema de busca
- Multiple study sessions

- Melhorar a visão dos dados
    - Usar as queries corretas no Surreal
    - Dar um talento de nada no models
    - Transformar tudo em lambda?
    - Por information nos edges para contexto?

- Processamento tinha que ser async
    - Ta dando pau em arquivos grandes
    - Precisa de um sistema de fila
    - Automatizar o processo de analise
    - Suportar transcrição de audio e de video
https://www.youtube.com/watch?v=mdLBr9IMmgI
- Langgraph
    - Mudar a memória das threads para o SurrealDB

- Estratégias mais poderosas que combinem fabric com embeddings

- Uma ideia legal seria usar um LLM muito barato para limpar textos e o vision para entender pdfs

----
There is a known issue with the surreal sdk for large content


FEATURES

- Recursive sumarizationa cima de 500k de texto
- Estimativa de custo do vetorizer para os conteudos
- Context Manager - fine grained
- Campo de busca de texto, vetor e híbrida
- Vector search on my own notes
