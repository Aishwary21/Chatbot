import requests
from bs4 import BeautifulSoup
import openai
import os
from typing import Optional
from urllib.parse import urlparse

class WebsiteChatbot:
    def __init__(self, api_key: str):
        """Initialize the chatbot with OpenAI API key."""
        openai.api_key = api_key
        self.context = ""
        self.conversation_history = []

    def extract_website_content(self, url: str) -> Optional[str]:
        """Extract text content from the given website URL."""
        try:
            # Validate URL
            parsed_url = urlparse(url)
            if not all([parsed_url.scheme, parsed_url.netloc]):
                raise ValueError("Invalid URL format")

            # Fetch website content
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            # Parse content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Extract text content
            text = soup.get_text()
            
            # Clean and process text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Truncate to avoid token limits
            self.context = text[:4000]  # Adjust limit based on your needs
            return self.context

        except Exception as e:
            print(f"Error extracting website content: {str(e)}")
            return None

    def process_query(self, user_input: str) -> str:
        """Process user query and generate response using ChatGPT."""
        try:
            # Prepare the conversation context
            messages = [
                {"role": "system", "content": f"You are a helpful assistant that answers questions about the following website content: {self.context}"},
                *self.conversation_history,
                {"role": "user", "content": user_input}
            ]

            # Generate response using ChatGPT
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=150,
                temperature=0.7
            )

            # Extract and store response
            bot_response = response.choices[0].message['content']
            self.conversation_history.extend([
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": bot_response}
            ])

            # Keep conversation history manageable
            if len(self.conversation_history) > 6:  # Store last 3 exchanges
                self.conversation_history = self.conversation_history[-6:]

            return bot_response

        except Exception as e:
            return f"Error processing query: {str(e)}"

def main():
    """Main function to demonstrate the chatbot."""
    # Get API key from environment variable
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Please set the OPENAI_API_KEY environment variable.")
        return

    # Initialize chatbot
    chatbot = WebsiteChatbot(api_key)

    # Get website URL
    url = input("Enter the website URL to chat about: ")
    content = chatbot.extract_website_content(url)

    if not content:
        print("Failed to extract website content. Please check the URL and try again.")
        return

    print("\nWebsite content loaded! You can now ask questions about it.")
    print("Type 'quit' to exit the chat.")

    # Main chat loop
    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() == 'quit':
            break

        response = chatbot.process_query(user_input)
        print(f"\nBot: {response}")

if __name__ == "__main__":
    main()