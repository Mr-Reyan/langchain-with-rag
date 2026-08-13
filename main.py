from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
# self.documents = [
#             "Paris is the capital of France. It's known for the Eiffel Tower.",
#             "London is the capital of the United Kingdom. It has Big Ben.",
#             "Tokyo is the capital of Japan. It's famous for sushi.",
#         ]
class RAGSystem:
    def __init__(self):
        
        self.llm = ChatOpenAI(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_api_base=os.getenv("OPENROUTER_BASE_URL"),
            model_name=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
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
                Answer the question based ONLY on the following context.
                If you can't answer, say "I don't know."

                Context: {context}
                Question: {question}
            """)

        self.text_spliiter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
            separators=["\n\n","\n"," ",""]
        )


    def load_document(self, file_path):
        """
        Load a document from file path (supports PDF, DOCX, TXT)
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Determine loader based on file extension
        extension = file_path.suffix.lower()
        
        if extension == '.pdf':
            loader = PyPDFLoader(str(file_path))
        elif extension == '.docx':
            loader = Docx2txtLoader(str(file_path))
        elif extension == '.txt':
            loader = TextLoader(str(file_path))
        else:
            raise ValueError(f"Unsupported file type: {extension}. Supported: .pdf, .docx, .txt")
        
        # Load and split documents
        documents = loader.load()
        print(documents)
        # Add source metadata
        for doc in documents:
            doc.metadata['source'] = file_path.name
        
        # Split into chunks
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
        
        # Clear existing vectorstore if it exists (optional - you might want to keep old data)
        # Comment this out if you want to add to existing data
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
                'k': 3,
            }
        )
        
        self._build_chain()
        print(f"Added {len(documents)} documents to the vector store.")

    
    
    def query(self, question: str) -> str:
        
        if self.rag_chain is None:
            raise ValueError("No documents loaded. Load a document or directory first.")
        
        response = self.rag_chain.invoke(question)
        return response

    def _build_chain(self):
            
            def format_docs(docs):
                return "\n\n".join(doc.page_content for doc in docs)
            
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