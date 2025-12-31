"""
Test OpenAI API configuration
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.config import settings
from openai import OpenAI
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_openai_connection():
    """Test OpenAI API connection and configuration"""

    print("\n" + "=" * 60)
    print("OpenAI Configuration Test")
    print("=" * 60 + "\n")

    # Check configuration
    print("Configuration:")
    print(f"  LLM Provider: {settings.llm_provider}")
    print(f"  LLM Model: {settings.llm_model}")
    print(f"  Embedding Model: {settings.embedding_model}")
    print(f"  Embedding Dimension: {settings.embedding_dimension}")
    print(f"  API Key: {settings.openai_api_key[:20]}...{settings.openai_api_key[-4:]}")
    print()

    # Test 1: OpenAI client initialization
    print("Test 1: Initializing OpenAI client...")
    try:
        client = OpenAI(api_key=settings.openai_api_key)
        print("✓ Client initialized successfully")
    except Exception as e:
        print(f"✗ Client initialization failed: {str(e)}")
        return False

    # Test 2: Embedding generation
    print("\nTest 2: Testing embedding generation...")
    try:
        response = client.embeddings.create(
            model=settings.embedding_model,
            input="This is a test sentence for embedding generation."
        )
        embedding = response.data[0].embedding
        print(f"✓ Embedding generated successfully")
        print(f"  Embedding dimension: {len(embedding)}")
        print(f"  Expected dimension: {settings.embedding_dimension}")

        if len(embedding) == settings.embedding_dimension:
            print("✓ Dimension matches configuration")
        else:
            print(f"⚠ Warning: Dimension mismatch ({len(embedding)} vs {settings.embedding_dimension})")
    except Exception as e:
        print(f"✗ Embedding generation failed: {str(e)}")
        return False

    # Test 3: LLM chat completion
    print("\nTest 3: Testing LLM chat completion...")
    try:
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Configuration test successful!' if you can read this."}
            ],
            max_tokens=50
        )
        message = response.choices[0].message.content
        print(f"✓ LLM response received")
        print(f"  Response: {message}")
    except Exception as e:
        print(f"✗ LLM completion failed: {str(e)}")
        print(f"\n⚠ Note: If you see an error about 'gpt-5-nano' not existing,")
        print(f"  update your .env file to use a valid model like 'gpt-4' or 'gpt-3.5-turbo'")
        return False

    # Test 4: Test our embedding generator
    print("\nTest 4: Testing custom embedding generator...")
    try:
        from src.rag.embedding import EmbeddingGenerator

        generator = EmbeddingGenerator()
        test_embedding = generator.embed_text("Test sentence for our embedding generator")
        print(f"✓ Custom embedding generator works")
        print(f"  Generated embedding dimension: {len(test_embedding)}")
    except Exception as e:
        print(f"✗ Custom embedding generator failed: {str(e)}")
        return False

    # Test 5: Test our LLM client
    print("\nTest 5: Testing custom LLM client...")
    try:
        from src.utils.llm_client import LLMClient

        llm = LLMClient()
        response = llm.generate(
            prompt="What is 2+2? Answer with just the number.",
            max_tokens=10
        )
        print(f"✓ Custom LLM client works")
        print(f"  Response: {response.strip()}")
    except Exception as e:
        print(f"✗ Custom LLM client failed: {str(e)}")
        return False

    print("\n" + "=" * 60)
    print("✓ All tests passed! OpenAI configuration is working.")
    print("=" * 60 + "\n")

    return True


if __name__ == "__main__":
    success = test_openai_connection()
    sys.exit(0 if success else 1)
