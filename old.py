from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_openai.chat_models import ChatOpenAI

import os
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader,Docx2txtLoader,TextLoader



class RAGSystem:
    def __init__(self):

        self.llm = ChatOpenAI(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_api_base=os.getenv("OPENROUTER_BASE_URL"),
            model_name=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
            temperature=0.3
            )

        self.embeddings = OpenAIEmbeddings(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_api_base=os.getenv("OPENROUTER_BASE_URL"),
        )



        self.vectorstore = None
        self.retriever = None
        self.rag_chain = None
        self.file_path = Path('./chroma_db')
        self.prompt = ChatPromptTemplate.from_template("""
                You are a helpful AI assistant. Answer the question based on the provided context.
                If the context doesn't contain the answer, say "I don't know."

                CONTEXT:
                {context}

                QUESTION: {question}

                ANSWER:
            """)

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=150,
            length_function=len,
            separators=["\n\n","\n"," ","","."]
        )


    def load_document(self, file_path):
        """
        Load a document from file path (supports PDF, DOCX, TXT)
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        extension = file_path.suffix.lower()

        if extension == '.pdf':
            loader = PyPDFLoader(str(file_path))
        elif extension == '.docx':
            loader = Docx2txtLoader(str(file_path))
        elif extension == '.txt':
            loader = TextLoader(str(file_path))
        else:
            raise ValueError(f"Unsupported file type: {extension}. Supported: .pdf, .docx, .txt")

        documents = loader.load()
        # Add source metadata
        print(f"Loaded {len(documents)} pages/sections")
        if documents:
            preview = documents[0].page_content[:200]
            print(f"Preview: {preview}...")

        for doc in documents:
            doc.metadata['source'] = file_path.name

        chunks = self.text_splitter.split_documents(documents)

        print(f"Loaded {file_path.name} with {len(chunks)} chunks")
        return chunks

    def add_documents(self, documents):
        """
        Add documents to vector store
        """
        if not documents:
            print("No documents to add.")
            return

        if self.file_path.exists():
            import shutil
            shutil.rmtree(self.file_path)
            print("Cleared existing vector store")

        # Create vectorstore
        self.vectorstore = Chroma.from_documents(
            documents,
            self.embeddings,
            persist_directory=str(self.file_path)
        )

        self.retriever = self.vectorstore.as_retriever(
            search_type='similarity',
            search_kwargs={
                'k': 6,
            }
        )

        self._build_chain()
        print(f"Added {len(documents)} documents to the vector store.")


    def query_debug(self, question: str):
        """
        Query and show debug information about retrieved chunks
        """
        if self.retriever is None:
            raise ValueError("No documents loaded. Load a document or directory first.")

        docs = self.retriever.invoke(question)

        context = "\n\n".join(doc.page_content for doc in docs)
        response = self.rag_chain.invoke(question)


        return response

    def query(self, question: str) -> str:

        if self.rag_chain is None:
            raise ValueError("No documents loaded. Load a document or directory first.")

        response = self.rag_chain.invoke(question)
        return response

    def _build_chain(self):

            def format_docs(docs):
                formatted = []
                for i, doc in enumerate(docs, 1):
                    source = doc.metadata.get('source','Unknown')
                    page = doc.metadata.get('page','N/A')
                    content = ' '.join(doc.page_content.split())
                    formatted.append(f"[Document {i}] - Source:{source}, Page:{page}\n{content}")
                return "\n\n---\n\n".join(formatted)

            self.rag_chain = (
                {
                    "context": self.retriever | format_docs,
                    "question": RunnablePassthrough()
                }
                | self.prompt
                | self.llm
                | StrOutputParser()
            )

    # def clear(self):

    #     if self.file_path.exists():
    #         import shutil
    #         shutil.rmtree(self.file_path)
    #         print("Cleared vector store.")

    #     self.vectorstore = None
    #     self.retriever = None
    #     self.rag_chain = None

if __name__=="__main__":
    rag = RAGSystem()

    file_path = input("Enter file path: ").strip()
    try:
        chunks = rag.load_document(file_path)
        rag.add_documents(chunks)
        print("✅ Document loaded successfully!")
        question = input("Enter your question: ").strip()
        try:
            answer = rag.query_debug(question)
            print("\n" + "="*50)
            print(f"Answer: {answer}")
            print("="*50)
        except Exception as e:
            print(f"❌ Error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

    # documents = [
    #     "Islamabad is the capital of Pakistan. It's known for the Margalla hills.",
    #     "Kabul is the capital of the Afghanistan. It has National Museum.",
    #     "Tokyo is the capital of Japan. It's famous for sushi.",
    # ]
    # rag.add_documents(documents)


    # question = input("Ask a question about capitals: ")
    # answer = rag.query(question)
    # print(f"Answer: {answer}")
