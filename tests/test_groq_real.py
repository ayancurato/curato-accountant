import os
import pytest
from app.services.ai_service import extract_invoice_data

# NOTE: This test will only run if GROQ_API_KEY is set in the environment
# and it is NOT "mock-api-key". Do not commit real API keys.

@pytest.mark.skipif(
    os.getenv("GROQ_API_KEY") is None or os.getenv("GROQ_API_KEY") == "mock-api-key" or os.getenv("GROQ_API_KEY") == "your-groq-api-key",
    reason="Real GROQ_API_KEY is not set"
)
def test_real_groq_integration():
    # Create a dummy image for testing
    test_image = "tests/test_real_invoice.jpg"
    with open(test_image, "wb") as f:
        # Just write some dummy bytes, though for a real test you'd want a real invoice image
        f.write(b"dummy image data")
        
    try:
        # Note: Since it's a dummy image, Groq Vision will likely fail to extract valid info,
        # but we are testing that the connection and Pydantic validation handles it.
        # It should return None/null for everything and very low confidence.
        result = extract_invoice_data(test_image, "image/jpeg")
        assert result is not None
        assert hasattr(result, "vendor_customer")
        assert hasattr(result, "total_amount")
    finally:
        if os.path.exists(test_image):
            os.remove(test_image)
