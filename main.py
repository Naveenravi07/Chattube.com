from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound
from langchain.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq
from langchain.schema import Document

def get_video_id(url):
    """Extracts the video ID from a YouTube URL."""
    if "youtu.be" in url:
        return url.split("/")[-1]
    elif "youtube.com" in url:
        return url.split("v=")[-1].split("&")[0]
    else:
        raise ValueError("Invalid YouTube URL")

def fetch_subtitles(video_url, language_code='en'):
    """Fetches subtitles from a YouTube video."""
    try:
        video_id = get_video_id(video_url)
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        try:
            transcript = transcript_list.find_transcript([language_code])
        except NoTranscriptFound:
            transcript = transcript_list.find_transcript(['en'])
        return transcript.fetch()
    except Exception as e:
        print(f"An error occurred while fetching subtitles: {str(e)}")
        return None

def prepare_subtitle_data(subtitle_data):
    """Prepares the subtitle text from the fetched data."""
    doc = []
    for item in subtitle_data:
        doc.append(Document(page_content=item['text']))
    return doc

def create_langchain_pipeline(documents):
    """Creates a LangChain pipeline for question answering."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    texts = text_splitter.split_documents(documents)

    llm = ChatGroq(
        api_key="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",
        model_name="Llama-3.2-90b-Text-Preview"
    )

    vectorstore = FAISS.from_documents(
        texts,
        GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key="AIzaSyCWY9f-l6CT4WgfcGp_TUN8cIZKWwL_-WQ"
        )
    )

    retriever = vectorstore.as_retriever()

    prompt = ChatPromptTemplate.from_template(
        """
        You should give the answer based on the context. It should be a very accurate answer.
        Context: {context}
        Question: {question}
        """
    )

    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain

def main():
    video_url = input("Enter the YouTube video URL: ")
    subtitle_data = fetch_subtitles(video_url)
    if subtitle_data:
        documents = prepare_subtitle_data(subtitle_data)
        qa_chain = create_langchain_pipeline(documents)
        while True:
            query = input("Enter your question (or 'quit' to exit): ")
            if query.lower() == 'quit':
                break
            try:
                result = qa_chain.invoke(query)
                print(f"Answer: {result}")
            except Exception as e:
                print(f"An error occurred while processing the query: {str(e)}")
    else:
        print("No subtitles available for this video.")

if __name__ == "__main__":
    main()